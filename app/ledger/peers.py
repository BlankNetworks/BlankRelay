from app.ledger.dynamic_peers import get_all_peers


def get_peer_relays() -> list[str]:
    return get_all_peers()
