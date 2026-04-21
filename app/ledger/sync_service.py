import threading
import time
from typing import Optional

import requests
from sqlalchemy.orm import Session

from app.ledger.block_sync import sync_missing_blocks_once

from app.db.ledger_database import LedgerSessionLocal
from app.ledger.models import ConsensusState
from app.ledger.validator_config import (
    NETWORK_ID,
    THIS_RELAY_DOMAIN,
    VALIDATOR_SET_VERSION,
    get_peer_domains,
)

SYNC_INTERVAL_SECONDS = 15


def get_state(db: Session, key: str, default: str) -> str:
    row = db.query(ConsensusState).filter(ConsensusState.state_key == key).first()
    return row.state_value if row else default


def set_state(db: Session, key: str, value: str) -> None:
    row = db.query(ConsensusState).filter(ConsensusState.state_key == key).first()
    if row is None:
        row = ConsensusState(state_key=key, state_value=value)
        db.add(row)
    else:
        row.state_value = value


def fetch_peer_status(peer_domain: str) -> Optional[dict]:
    url = f"https://{peer_domain}/ledger/status"
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        return response.json()
    except Exception:
        return None


def run_sync_check_once():
    db = LedgerSessionLocal()
    try:
        sync_missing_blocks_once()
        local_index = int(get_state(db, "current_block_index", "0"))
        local_hash = get_state(db, "current_block_hash", "GENESIS")

        peer_statuses = []
        for peer in get_peer_domains():
            status = fetch_peer_status(peer)
            if status:
                peer_statuses.append(status)

        # If no peers respond yet, remain synced for local/dev use.
        if not peer_statuses:
            set_state(db, "network_id", NETWORK_ID)
            set_state(db, "validator_set_version", str(VALIDATOR_SET_VERSION))
            set_state(db, "is_synced", "true")
            set_state(db, "last_sync_check", str(int(time.time())))
            db.commit()
            return

        highest_index = max(int(p.get("currentBlockIndex", 0)) for p in peer_statuses)
        matching_peer = any(
            int(p.get("currentBlockIndex", 0)) == local_index
            and p.get("currentBlockHash", "") == local_hash
            for p in peer_statuses
        )

        is_synced = local_index >= highest_index and matching_peer

        set_state(db, "network_id", NETWORK_ID)
        set_state(db, "validator_set_version", str(VALIDATOR_SET_VERSION))
        set_state(db, "is_synced", "true" if is_synced else "false")
        set_state(db, "highest_peer_block_index", str(highest_index))
        set_state(db, "last_sync_check", str(int(time.time())))
        db.commit()
    finally:
        db.close()


def sync_checker_loop():
    while True:
        try:
            run_sync_check_once()
        except Exception as e:
            db = LedgerSessionLocal()
            try:
                set_state(db, "is_synced", "false")
                set_state(db, "last_sync_error", str(e))
                set_state(db, "last_sync_check", str(int(time.time())))
                db.commit()
            finally:
                db.close()
        time.sleep(SYNC_INTERVAL_SECONDS)


def start_sync_checker():
    thread = threading.Thread(target=sync_checker_loop, daemon=True)
    thread.start()
