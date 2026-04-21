from app.ledger.validator_config import IS_MULTI_RELAY_MODE, QUORUM_SIZE


def quorum_required() -> int:
    return QUORUM_SIZE


def is_multi_relay_enforced() -> bool:
    return IS_MULTI_RELAY_MODE
