from app.ledger.validator_config import VALIDATOR_PEERS

_dynamic_peers: list[str] = []


def get_dynamic_peers() -> list[str]:
    return list(_dynamic_peers)


def set_dynamic_peers(peers: list[str]) -> None:
    global _dynamic_peers
    seen = set()
    cleaned = []

    for peer in peers:
        value = peer.strip()
        if not value:
            continue
        if value in seen:
            continue
        seen.add(value)
        cleaned.append(value)

    _dynamic_peers = cleaned


def get_all_peers() -> list[str]:
    combined = []
    seen = set()

    for peer in VALIDATOR_PEERS + _dynamic_peers:
        value = peer.strip()
        if not value:
            continue
        if value in seen:
            continue
        seen.add(value)
        combined.append(value)

    return combined
