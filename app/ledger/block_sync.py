import json

import requests
from sqlalchemy.orm import Session

from app.ledger.join_state import set_join_mode
from app.ledger.validator_config import AUTO_EXIT_JOIN_MODE_ON_SYNC

from app.ledger.peer_selector import pick_best_sync_peer
from app.ledger.sync_state import set_consensus_value

from app.db.ledger_database import LedgerSessionLocal
from app.ledger.models import LedgerBlock, LedgerClaim
from app.ledger.ownership_index import rebuild_ownership_index


def fetch_peer_head(peer: str) -> int:
    try:
        r = requests.get(f"{peer}/ledger/blocks/head", timeout=3)
        if r.status_code == 200:
            return int(r.json()["currentBlockIndex"])
    except Exception:
        pass
    return 0


def fetch_block_from_peer(peer: str, index: int) -> str | None:
    try:
        r = requests.get(f"{peer}/ledger/blocks/{index}", timeout=3)
        if r.status_code == 200:
            return r.json()["rawBlock"]
    except Exception:
        pass
    return None


def import_raw_block(db: Session, raw_block_json: str) -> None:
    block_obj = json.loads(raw_block_json)

    block_index = block_obj["index"]
    existing = db.query(LedgerBlock).filter(LedgerBlock.block_index == block_index).first()
    if existing is not None:
        return

    db.add(
        LedgerBlock(
            network_id=block_obj["network_id"],
            block_index=block_obj["index"],
            round_number=block_obj["round_number"],
            previous_block_hash=block_obj["previous_block_hash"],
            timestamp=block_obj["timestamp"],
            round_result=block_obj["round_result"],
            validator_relay_domain=block_obj["validator_relay_domain"],
            block_hash=block_obj["block_hash"],
            validator_signature_base64=block_obj["validator_signature_base64"],
            raw_block_json=raw_block_json,
        )
    )

    for claim in block_obj.get("claims", []):
        db.add(
            LedgerClaim(
                block_index=block_obj["index"],
                blank_id=claim["blank_id"],
                relay_domain=claim["relay_domain"],
                identity_key_base64=claim["identity_key_base64"],
                identity_signing_public_key_base64=claim["identity_signing_public_key_base64"],
                ownership_signature_base64=claim["ownership_signature_base64"],
                claimed_at=claim["claimed_at"],
                nonce=claim["nonce"],
                client_claim_hash=claim["client_claim_hash"],
                relay_signature_base64=claim["relay_signature_base64"],
                claim_status=claim["claim_status"],
            )
        )

    db.commit()
    rebuild_ownership_index(db)


def sync_missing_blocks_once() -> None:
    db = LedgerSessionLocal()
    try:
        set_consensus_value(db, "is_syncing", "true")
        db.commit()

        local_head = db.query(LedgerBlock).order_by(LedgerBlock.block_index.desc()).first()
        local_index = local_head.block_index if local_head else 0

        best_peer = pick_best_sync_peer()
        if not best_peer:
            set_consensus_value(db, "is_syncing", "false")
            db.commit()
            return

        peer_index = fetch_peer_head(best_peer)

        if peer_index <= local_index:
            set_consensus_value(db, "is_syncing", "false")
            db.commit()
            return

        for i in range(local_index + 1, peer_index + 1):
            raw = fetch_block_from_peer(best_peer, i)
            if raw:
                import_raw_block(db, raw)

        if AUTO_EXIT_JOIN_MODE_ON_SYNC:
            set_join_mode(db, False)

        set_consensus_value(db, "is_syncing", "false")
        db.commit()

    finally:
        db.close()
