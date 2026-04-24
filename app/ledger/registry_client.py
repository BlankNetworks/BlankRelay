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


def get_self_relay_domain() -> str:
    return RELAY_DOMAIN or THIS_RELAY_DOMAIN


def register_with_registry() -> bool:
    registry_url = get_registry_base_url()
    if not registry_url:
        return False

    try:
        response = requests.post(
            f"{registry_url}/register",
            json={
                "relayDomain": get_self_relay_domain(),
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
                "relayDomain": get_self_relay_domain(),
                "syncSourceWeight": SYNC_SOURCE_WEIGHT,
                "maxSyncClients": MAX_SYNC_CLIENTS,
            },
            timeout=5,
        )
        return response.status_code == 200
    except Exception:
        return False


def fetch_registry_relays_raw() -> list[dict]:
    registry_url = get_registry_base_url()
    if not registry_url:
        return []

    try:
        response = requests.get(f"{registry_url}/relays", timeout=5)
        if response.status_code != 200:
            return []
        return response.json().get("relays", [])
    except Exception:
        return []


def self_is_registered() -> bool:
    self_domain = get_self_relay_domain()
    for relay in fetch_registry_relays_raw():
        if relay.get("relayDomain") == self_domain:
            return True
    return False


def registry_status() -> dict:
    relays = fetch_registry_relays_raw()
    return {
        "registryBaseURL": get_registry_base_url(),
        "selfRelayDomain": get_self_relay_domain(),
        "registered": self_is_registered(),
        "relayCount": len(relays),
        "relays": relays,
    }
