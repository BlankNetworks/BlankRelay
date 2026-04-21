from sqlalchemy.orm import Session

from app.ledger.models import ConsensusState


def get_consensus_value(db: Session, key: str, default: str) -> str:
    row = db.query(ConsensusState).filter(ConsensusState.state_key == key).first()
    return row.state_value if row else default


def set_consensus_value(db: Session, key: str, value: str) -> None:
    row = db.query(ConsensusState).filter(ConsensusState.state_key == key).first()
    if row is None:
        row = ConsensusState(state_key=key, state_value=value)
        db.add(row)
    else:
        row.state_value = value


def is_relay_synced(db: Session) -> bool:
    return get_consensus_value(db, "is_synced", "true").lower() == "true"


def is_relay_syncing(db: Session) -> bool:
    return get_consensus_value(db, "is_syncing", "false").lower() == "true"
