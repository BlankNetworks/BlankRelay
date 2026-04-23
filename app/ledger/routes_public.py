from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.ledger_database import LedgerSessionLocal, get_ledger_db
from app.ledger.join_state import get_join_mode
from app.ledger.models import BlankIDReservation, ConsensusState, OwnershipIndex, PendingClaim
from app.ledger.peer_forwarding import forward_claim_to_peers
from app.ledger.schemas import (
    BlankIDReserveRequest,
    BlankIDReserveResponse,
    LedgerClaimStatusResponse,
    LedgerClaimSubmitRequest,
    LedgerClaimSubmitResponse,
    LedgerIDCheckResponse,
    LedgerStatusResponse,
    build_claim_hash,
)
from app.ledger.sync_state import is_relay_syncing
from app.ledger.validator_config import (
    BLOCK_CLIENT_WRITES_WHILE_SYNCING,
    THIS_RELAY_DOMAIN,
)



router = APIRouter(prefix="/ledger", tags=["ledger"])


def get_consensus_value(db: Session, key: str, default: str) -> str:
    row = db.query(ConsensusState).filter(ConsensusState.state_key == key).first()
    return row.state_value if row else default


@router.get("/status", response_model=LedgerStatusResponse)
def ledger_status(db: Session = Depends(get_ledger_db)):
    return {
        "networkID": get_consensus_value(db, "network_id", "blankchat-mainnet-v1"),
        "isSynced": get_consensus_value(db, "is_synced", "true").lower() == "true",
        "currentBlockIndex": int(get_consensus_value(db, "current_block_index", "0")),
        "currentBlockHash": get_consensus_value(db, "current_block_hash", "GENESIS"),
        "validatorSetVersion": int(get_consensus_value(db, "validator_set_version", "1")),
        "thisRelayDomain": THIS_RELAY_DOMAIN,
        "highestPeerBlockIndex": int(get_consensus_value(db, "highest_peer_block_index", "0")),
        "lastSyncCheck": get_consensus_value(db, "last_sync_check", "0"),
    }


@router.get("/ids/check", response_model=LedgerIDCheckResponse)
def ledger_check_id(blankID: str = Query(..., min_length=3, max_length=32), db: Session = Depends(get_ledger_db)):
    normalized = blankID.strip().lower()
    owned = db.query(OwnershipIndex).filter(OwnershipIndex.blank_id == normalized).first()
    return {
        "blankID": normalized,
        "available": owned is None,
        "source": "ledger",
        "isSynced": get_consensus_value(db, "is_synced", "true").lower() == "true",
        "currentBlockIndex": int(get_consensus_value(db, "current_block_index", "0")),
    }


@router.post("/claims/submit", response_model=LedgerClaimSubmitResponse)
def submit_claim(payload: LedgerClaimSubmitRequest, db: Session = Depends(get_ledger_db)):
    is_synced = get_consensus_value(db, "is_synced", "true").lower() == "true"
    if not is_synced:
        raise HTTPException(status_code=503, detail="relay not synced")

    already_taken = db.query(OwnershipIndex).filter(OwnershipIndex.blank_id == payload.blankID).first()
    if already_taken is not None:
        return {
            "success": False,
            "status": "taken",
            "blankID": payload.blankID,
            "clientClaimHash": "",
            "message": "Blank ID already committed in ledger",
        }

    client_claim_hash = build_claim_hash(
        network_id=get_consensus_value(db, "network_id", "blankchat-mainnet-v1"),
        blank_id=payload.blankID,
        relay_domain=payload.relayDomain,
        identity_key_base64=payload.identityKeyBase64,
        identity_signing_public_key_base64=payload.identitySigningPublicKeyBase64,
        ownership_signature_base64=payload.ownershipSignatureBase64,
        claimed_at=payload.claimedAt,
        nonce=payload.nonce,
    )

    existing_pending = db.query(PendingClaim).filter(PendingClaim.client_claim_hash == client_claim_hash).first()
    if existing_pending is not None:
        return {
            "success": True,
            "status": existing_pending.status,
            "blankID": payload.blankID,
            "clientClaimHash": client_claim_hash,
            "message": "Claim already submitted",
        }

    if BLOCK_CLIENT_WRITES_WHILE_SYNCING and is_relay_syncing(db):
        raise HTTPException(status_code=503, detail="Relay is syncing and not accepting claim writes yet")

    if get_join_mode(db):
        raise HTTPException(status_code=503, detail="Relay is in join mode and not accepting claim writes yet")

    pending = PendingClaim(
        blank_id=payload.blankID,
        relay_domain=payload.relayDomain,
        identity_key_base64=payload.identityKeyBase64,
        identity_signing_public_key_base64=payload.identitySigningPublicKeyBase64,
        ownership_signature_base64=payload.ownershipSignatureBase64,
        claimed_at=payload.claimedAt,
        nonce=payload.nonce,
        client_claim_hash=client_claim_hash,
        relay_signature_base64=payload.relaySignatureBase64,
        received_at=datetime.now(timezone.utc).isoformat(),
        status="pending_consensus",
    )
    db.add(pending)
    db.commit()

    forward_claim_to_peers(
        {
            "blankID": payload.blankID,
            "relayDomain": payload.relayDomain,
            "identityKeyBase64": payload.identityKeyBase64,
            "identitySigningPublicKeyBase64": payload.identitySigningPublicKeyBase64,
            "ownershipSignatureBase64": payload.ownershipSignatureBase64,
            "claimedAt": payload.claimedAt,
            "nonce": payload.nonce,
            "relaySignatureBase64": payload.relaySignatureBase64,
        }
    )

    return {
        "success": True,
        "status": "pending_consensus",
        "blankID": payload.blankID,
        "clientClaimHash": client_claim_hash,
        "message": "Claim submitted",
    }

@router.get("/claims/{clientClaimHash}", response_model=LedgerClaimStatusResponse)
def get_claim_status(clientClaimHash: str, db: Session = Depends(get_ledger_db)):
    pending = db.query(PendingClaim).filter(PendingClaim.client_claim_hash == clientClaimHash).first()
    if pending is not None:
        return {
            "blankID": pending.blank_id,
            "status": pending.status,
            "clientClaimHash": pending.client_claim_hash,
        }

    committed = db.query(OwnershipIndex).filter(OwnershipIndex.client_claim_hash == clientClaimHash).first()
    if committed is not None:
        return {
            "blankID": committed.blank_id,
            "status": "committed",
            "clientClaimHash": committed.client_claim_hash,
        }

    raise HTTPException(status_code=404, detail="claim not found")

@router.post("/ids/reserve", response_model=BlankIDReserveResponse)
def reserve_blank_id(payload: BlankIDReserveRequest):
    db = LedgerSessionLocal()
    try:
        normalized_blank_id = payload.blankID.strip().lower()

        existing = (
            db.query(BlankIDReservation)
            .filter(BlankIDReservation.blank_id == normalized_blank_id)
            .first()
        )
        if existing is not None:
            raise HTTPException(status_code=409, detail="BlankID already reserved")

        row = BlankIDReservation(
            blank_id=normalized_blank_id,
            relay_domain=payload.relayDomain,
            status="reserved",
            reserved_at=datetime.now(timezone.utc).isoformat(),
        )
        db.add(row)
        db.commit()

        return {
            "success": True,
            "blankID": normalized_blank_id,
            "relayDomain": payload.relayDomain,
            "message": "BlankID reserved successfully",
        }
    finally:
        db.close()

