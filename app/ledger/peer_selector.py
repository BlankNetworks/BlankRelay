import requests

from app.ledger.peers import get_peer_relays
from app.ledger.url_normalizer import normalize_relay_url
from app.ledger.validator_config import THIS_RELAY_DOMAIN


def fetch_admission_status(peer: str) -> dict | None:
    try:
        r = requests.get(f"{peer}/ledger/admission-status", timeout=4)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return None


def pick_best_sync_peer() -> str | None:
    candidates = []
    self_normalized = normalize_relay_url(THIS_RELAY_DOMAIN)

    for peer in get_peer_relays():
        if normalize_relay_url(peer) == self_normalized:
            continue

        status = fetch_admission_status(peer)
        if not status:
            continue

        if not status.get("readyForJoin", False):
            continue

        active_sync_clients = int(status.get("activeSyncClients", 0))
        max_sync_clients = int(status.get("maxSyncClients", 0))
        current_block_index = int(status.get("currentBlockIndex", 0))
        sync_source_weight = int(status.get("syncSourceWeight", 100))

        candidates.append(
            (
                sync_source_weight,
                active_sync_clients,
                -current_block_index,
                peer,
            )
        )

    if not candidates:
        return None

    candidates.sort()
    return candidates[0][3]
