from sqlalchemy.orm import Session

from app.ledger.sync_state import get_consensus_value, set_consensus_value
from app.ledger.validator_config import MAX_SYNC_CLIENTS


def get_active_sync_clients(db: Session) -> int:
    return int(get_consensus_value(db, "active_sync_clients", "0"))


def try_acquire_sync_slot(db: Session) -> tuple[bool, int, int]:
    active = get_active_sync_clients(db)
    if active >= MAX_SYNC_CLIENTS:
        return False, active, MAX_SYNC_CLIENTS

    active += 1
    set_consensus_value(db, "active_sync_clients", str(active))
    db.commit()
    return True, active, MAX_SYNC_CLIENTS


def release_sync_slot(db: Session) -> tuple[int, int]:
    active = get_active_sync_clients(db)
    if active > 0:
        active -= 1
    set_consensus_value(db, "active_sync_clients", str(active))
    db.commit()
    return active, MAX_SYNC_CLIENTS
