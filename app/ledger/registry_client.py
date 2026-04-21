import requests

from app.config import RELAY_DOMAIN, RELAY_REGISTRY_URL
from app.ledger.validator_config import (
    MAX_SYNC_CLIENTS,
    SYNC_SOURCE_WEIGHT,
    THIS_RELAY_DOMAIN,
)


def get_registry_base_url() -> str:
    url = (RELAY_REGISTRY_URL or "").rstrip("/")
    if url.endswith("/relays"):
        url = url[:-7]
    return url


def register_with_registry() -> bool:
    registry_url = get_registry_base_url()
    if not registry_url:
        return False

    try:
        response = requests.post(
            f"{registry_url}/register",
            json={
                "relayDomain": RELAY_DOMAIN or THIS_RELAY_DOMAIN,
                "syncSourceWeight": SYNC_SOURCE_WEIGHT,
                "maxSyncClients": MAX_SYNC_CLIENTS,
            },
            timeout=5,
        )
        return response.status_code == 200
    except Exception:
        return False


def heartbeat_registry() -> bool:
    registry_url = get_registry_base_url()
    if not registry_url:
        return False

    try:
        response = requests.post(
            f"{registry_url}/heartbeat",
            json={
                "relayDomain": RELAY_DOMAIN or THIS_RELAY_DOMAIN,
                "syncSourceWeight": SYNC_SOURCE_WEIGHT,
                "maxSyncClients": MAX_SYNC_CLIENTS,
            },
            timeout=5,
        )
        return response.status_code == 200
    except Exception:
        return False
