import json
import threading
import time
from datetime import datetime, timezone
from hashlib import sha256
from app.ledger.blankid_registry_client import publish_blankid
from app.ledger.quorum import is_multi_relay_enforced, quorum_required

from app.db.ledger_database import LedgerSessionLocal
from app.ledger.models import (
    ConsensusState,
    LedgerBlock,
    LedgerClaim,
    LedgerCommitSignature,
    LedgerProposal,
    OwnershipIndex,
    PendingClaim,
)
from app.ledger.ownership_index import rebuild_ownership_index
from app.ledger.schemas import build_block_hash
from app.ledger.validator_config import NETWORK_ID, QUORUM_SIZE, THIS_RELAY_DOMAIN

COMMIT_INTERVAL_SECONDS = 10


def get_state(db, key: str, default: str) -> str:
    row = db.query(ConsensusState).filter(ConsensusState.state_key == key).first()
    return row.state_value if row else default


def set_state(db, key: str, value: str) -> None:
    row = db.query(ConsensusState).filter(ConsensusState.state_key == key).first()
    if row is None:
        row = ConsensusState(state_key=key, state_value=value)
        db.add(row)
    else:
        row.state_value = value


def claims_hash_for_block(claims: list[dict]) -> str:
    raw = json.dumps(claims, sort_keys=True, separators=(",", ":"))
    return sha256(raw.encode("utf-8")).hexdigest()


def ensure_local_vote(db, block_index: int):
    existing_vote = (
        db.query(LedgerCommitSignature)
        .filter(
            LedgerCommitSignature.block_index == block_index,
            LedgerCommitSignature.relay_domain == THIS_RELAY_DOMAIN,
        )
        .first()
    )
    if existing_vote is None:
        db.add(
            LedgerCommitSignature(
                block_index=block_index,
                relay_domain=THIS_RELAY_DOMAIN,
                signature_base64="LOCAL_SINGLE_NODE_V1",
            )
        )
        db.commit()


def vote_count(db, block_index: int) -> int:
    return (
        db.query(LedgerCommitSignature)
        .filter(LedgerCommitSignature.block_index == block_index)
        .count()
    )


def commit_one_round():
    db = LedgerSessionLocal()
    try:
        is_synced = get_state(db, "is_synced", "true").lower() == "true"
        if not is_synced:
            return

        pending = (
            db.query(PendingClaim)
            .filter(PendingClaim.status == "pending_consensus")
            .order_by(PendingClaim.received_at.asc(), PendingClaim.id.asc())
            .all()
        )
        if not pending:
            return

        first = pending[0]

        existing_owner = db.query(OwnershipIndex).filter(OwnershipIndex.blank_id == first.blank_id).first()
        if existing_owner is not None:
            first.status = "taken"
            db.commit()
            return

        current_block_index = int(get_state(db, "current_block_index", "0"))
        current_block_hash = get_state(db, "current_block_hash", "GENESIS")

        next_index = current_block_index + 1
        round_number = next_index
        timestamp = datetime.now(timezone.utc).isoformat()

        same_blank = [p for p in pending if p.blank_id == first.blank_id]

        if len(same_blank) > 1:
            claims = []
            for row in same_blank:
                claims.append(
                    {
                        "blank_id": row.blank_id,
                        "relay_domain": row.relay_domain,
                        "identity_key_base64": row.identity_key_base64,
                        "identity_signing_public_key_base64": row.identity_signing_public_key_base64,
                        "ownership_signature_base64": row.ownership_signature_base64,
                        "claimed_at": row.claimed_at,
                        "nonce": row.nonce,
                        "client_claim_hash": row.client_claim_hash,
                        "relay_signature_base64": row.relay_signature_base64,
                        "claim_status": "collision_rejected",
                    }
                )

            publish_blankid(
                blank_id=first.blank_id,
                relay_domain=first.relay_domain,
                client_claim_hash=first.client_claim_hash,
                block_index=next_index,
                claimed_at=first.claimed_at,
            )

            claims_hash = claims_hash_for_block(claims)
            block_hash = build_block_hash(
                network_id=NETWORK_ID,
                block_index=next_index,
                round_number=round_number,
                previous_block_hash=current_block_hash,
                timestamp=timestamp,
                claims_hash=claims_hash,
                round_result="collision_rejected",
                validator_relay_domain=THIS_RELAY_DOMAIN,
            )

            block_obj = {
                "network_id": NETWORK_ID,
                "index": next_index,
                "round_number": round_number,
                "previous_block_hash": current_block_hash,
                "timestamp": timestamp,
                "claims": claims,
                "round_result": "collision_rejected",
                "validator_relay_domain": THIS_RELAY_DOMAIN,
                "block_hash": block_hash,
                "validator_signature_base64": "LOCAL_SINGLE_NODE_V1",
            }

            proposal = (
                db.query(LedgerProposal)
                .filter(LedgerProposal.proposal_hash == block_hash)
                .first()
            )
            if proposal is None:
                db.add(
                    LedgerProposal(
                        round_number=round_number,
                        proposer_relay_domain=THIS_RELAY_DOMAIN,
                        proposal_hash=block_hash,
                        block_index=next_index,
                        raw_block_json=json.dumps(block_obj, sort_keys=True),
                        status="proposed",
                    )
                )
                db.commit()

            ensure_local_vote(db, next_index)

            if vote_count(db, next_index) < quorum_required():
                return

            proposal = (
                db.query(LedgerProposal)
                .filter(LedgerProposal.proposal_hash == block_hash)
                .first()
            )
            if proposal is not None:
                proposal.status = "committed_locally"

            db.add(
                LedgerBlock(
                    network_id=NETWORK_ID,
                    block_index=next_index,
                    round_number=round_number,
                    previous_block_hash=current_block_hash,
                    timestamp=timestamp,
                    round_result="collision_rejected",
                    validator_relay_domain=THIS_RELAY_DOMAIN,
                    block_hash=block_hash,
                    validator_signature_base64="LOCAL_SINGLE_NODE_V1",
                    raw_block_json=json.dumps(block_obj, sort_keys=True),
                )
            )

            for row in same_blank:
                row.status = "collision_rejected"

            for claim in claims:
                db.add(
                    LedgerClaim(
                        block_index=next_index,
                        blank_id=claim["blank_id"],
                        relay_domain=claim["relay_domain"],
                        identity_key_base64=claim["identity_key_base64"],
                        identity_signing_public_key_base64=claim["identity_signing_public_key_base64"],
                        ownership_signature_base64=claim["ownership_signature_base64"],
                        claimed_at=claim["claimed_at"],
                        nonce=claim["nonce"],
                        client_claim_hash=claim["client_claim_hash"],
                        relay_signature_base64=claim["relay_signature_base64"],
                        claim_status="collision_rejected",
                    )
                )

            set_state(db, "current_block_index", str(next_index))
            set_state(db, "current_block_hash", block_hash)
            db.commit()
            rebuild_ownership_index(db)
            return

        claim_obj = {
            "blank_id": first.blank_id,
            "relay_domain": first.relay_domain,
            "identity_key_base64": first.identity_key_base64,
            "identity_signing_public_key_base64": first.identity_signing_public_key_base64,
            "ownership_signature_base64": first.ownership_signature_base64,
            "claimed_at": first.claimed_at,
            "nonce": first.nonce,
            "client_claim_hash": first.client_claim_hash,
            "relay_signature_base64": first.relay_signature_base64,
            "claim_status": "committed",
        }

        claims = [claim_obj]
        claims_hash = claims_hash_for_block(claims)

        block_hash = build_block_hash(
            network_id=NETWORK_ID,
            block_index=next_index,
            round_number=round_number,
            previous_block_hash=current_block_hash,
            timestamp=timestamp,
            claims_hash=claims_hash,
            round_result="committed",
            validator_relay_domain=THIS_RELAY_DOMAIN,
        )

        block_obj = {
            "network_id": NETWORK_ID,
            "index": next_index,
            "round_number": round_number,
            "previous_block_hash": current_block_hash,
            "timestamp": timestamp,
            "claims": claims,
            "round_result": "committed",
            "validator_relay_domain": THIS_RELAY_DOMAIN,
            "block_hash": block_hash,
            "validator_signature_base64": "LOCAL_SINGLE_NODE_V1",
        }

        proposal = (
            db.query(LedgerProposal)
            .filter(LedgerProposal.proposal_hash == block_hash)
            .first()
        )
        if proposal is None:
            db.add(
                LedgerProposal(
                    round_number=round_number,
                    proposer_relay_domain=THIS_RELAY_DOMAIN,
                    proposal_hash=block_hash,
                    block_index=next_index,
                    raw_block_json=json.dumps(block_obj, sort_keys=True),
                    status="proposed",
                )
            )
            db.commit()

        ensure_local_vote(db, next_index)

        if vote_count(db, next_index) < quorum_required():
            return

        proposal = (
            db.query(LedgerProposal)
            .filter(LedgerProposal.proposal_hash == block_hash)
            .first()
        )
        if proposal is not None:
            proposal.status = "committed_locally"

        db.add(
            LedgerBlock(
                network_id=NETWORK_ID,
                block_index=next_index,
                round_number=round_number,
                previous_block_hash=current_block_hash,
                timestamp=timestamp,
                round_result="committed",
                validator_relay_domain=THIS_RELAY_DOMAIN,
                block_hash=block_hash,
                validator_signature_base64="LOCAL_SINGLE_NODE_V1",
                raw_block_json=json.dumps(block_obj, sort_keys=True),
            )
        )

        db.add(
            LedgerClaim(
                block_index=next_index,
                blank_id=first.blank_id,
                relay_domain=first.relay_domain,
                identity_key_base64=first.identity_key_base64,
                identity_signing_public_key_base64=first.identity_signing_public_key_base64,
                ownership_signature_base64=first.ownership_signature_base64,
                claimed_at=first.claimed_at,
                nonce=first.nonce,
                client_claim_hash=first.client_claim_hash,
                relay_signature_base64=first.relay_signature_base64,
                claim_status="committed",
            )
        )

        first.status = "committed"

        set_state(db, "current_block_index", str(next_index))
        set_state(db, "current_block_hash", block_hash)
        db.commit()
        rebuild_ownership_index(db)

    finally:
        db.close()


def commit_loop():
    while True:
        try:
            commit_one_round()
        except Exception:
            pass
        time.sleep(COMMIT_INTERVAL_SECONDS)


def start_commit_loop():
    thread = threading.Thread(target=commit_loop, daemon=True)
    thread.start()
