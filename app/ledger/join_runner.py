import requests

from app.db.ledger_database import LedgerSessionLocal
from app.ledger.block_sync import sync_missing_blocks_once
from app.ledger.join_state import get_join_mode, set_join_mode
from app.ledger.peer_selector import pick_best_sync_peer
from app.ledger.sync_state import get_consensus_value, set_consensus_value
from app.ledger.validator_config import AUTO_EXIT_JOIN_MODE_ON_SYNC, THIS_RELAY_DOMAIN


def acquire_remote_sync_slot(peer: str) -> bool:
    try:
        r = requests.post(
            f"{peer}/ledger/sync-slot/acquire",
            json={"relayDomain": THIS_RELAY_DOMAIN},
            timeout=5,
        )
        if r.status_code == 200:
            data = r.json()
            return bool(data.get("success", False))
    except Exception:
        pass
    return False


def release_remote_sync_slot(peer: str) -> None:
    try:
        requests.post(
            f"{peer}/ledger/sync-slot/release",
            json={"relayDomain": THIS_RELAY_DOMAIN},
            timeout=5,
        )
    except Exception:
        pass


def run_join_once() -> dict:
    db = LedgerSessionLocal()
    try:
        set_join_mode(db, True)
        set_consensus_value(db, "is_syncing", "true")
        db.commit()

        selected_peer = pick_best_sync_peer()

        if not selected_peer:
            set_consensus_value(db, "is_syncing", "false")
            db.commit()
            return {
                "success": False,
                "joinModeCurrent": get_join_mode(db),
                "isSyncing": False,
                "selectedPeer": None,
                "message": "no eligible sync peer available",
            }
    finally:
        db.close()

    if not acquire_remote_sync_slot(selected_peer):
        db = LedgerSessionLocal()
        try:
            set_consensus_value(db, "is_syncing", "false")
            db.commit()
            return {
                "success": False,
                "joinModeCurrent": get_join_mode(db),
                "isSyncing": False,
                "selectedPeer": selected_peer,
                "message": "selected peer has no sync slot available",
            }
        finally:
            db.close()

    try:
        sync_missing_blocks_once()
    except Exception:
        db = LedgerSessionLocal()
        try:
            set_consensus_value(db, "is_syncing", "false")
            db.commit()
            return {
                "success": False,
                "joinModeCurrent": get_join_mode(db),
                "isSyncing": False,
                "selectedPeer": selected_peer,
                "message": "sync failed during join run",
            }
        finally:
            db.close()
    finally:
        release_remote_sync_slot(selected_peer)

    db = LedgerSessionLocal()
    try:
        set_consensus_value(db, "is_syncing", "false")

        if AUTO_EXIT_JOIN_MODE_ON_SYNC:
            set_join_mode(db, False)

        db.commit()

        return {
            "success": True,
            "joinModeCurrent": get_join_mode(db),
            "isSyncing": get_consensus_value(db, "is_syncing", "false").lower() == "true",
            "selectedPeer": selected_peer,
            "message": "join run completed",
        }
    finally:
        db.close()
