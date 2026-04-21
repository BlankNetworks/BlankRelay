from sqlalchemy.orm import Session

from app.ledger.models import ConsensusState


def get_join_mode(db: Session) -> bool:
    row = db.query(ConsensusState).filter(ConsensusState.state_key == "join_mode").first()
    if row is None:
        return False
    return row.state_value.lower() == "true"


def set_join_mode(db: Session, value: bool) -> None:
    row = db.query(ConsensusState).filter(ConsensusState.state_key == "join_mode").first()
    if row is None:
        row = ConsensusState(state_key="join_mode", state_value="true" if value else "false")
        db.add(row)
    else:
        row.state_value = "true" if value else "false"
