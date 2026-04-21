import json
from pathlib import Path

import requests

from app.config import (
    LOCAL_RELAY_REGISTRY_FILE,
    RELAY_ALLOW_SELF_ADVERTISE,
    RELAY_DISCOVERY_REFRESH_SECONDS,
    RELAY_REGISTRY_URL,
    USE_LOCAL_RELAY_REGISTRY,
)
from app.ledger.validator_config import THIS_RELAY_DOMAIN


def fetch_remote_registry_relays() -> list[str]:
    if not RELAY_REGISTRY_URL:
        return []

    try:
        r = requests.get(RELAY_REGISTRY_URL, timeout=5)
        if r.status_code != 200:
            return []

        data = r.json()
        relays = data.get("relays", [])
        clean = []
        for relay in relays:
            if isinstance(relay, str) and relay.strip():
                clean.append(relay.strip())
        return clean
    except Exception:
        return []


def fetch_local_registry_relays() -> list[str]:
    if not USE_LOCAL_RELAY_REGISTRY:
        return []

    try:
        path = Path(LOCAL_RELAY_REGISTRY_FILE)
        if not path.exists():
            return []

        data = json.loads(path.read_text(encoding="utf-8"))
        relays = data.get("relays", [])
        clean = []
        for relay in relays:
            if isinstance(relay, str) and relay.strip():
                clean.append(relay.strip())
        return clean
    except Exception:
        return []


def fetch_registry_relays() -> list[str]:
    combined = []
    seen = set()

    for relay in fetch_local_registry_relays() + fetch_remote_registry_relays():
        value = relay.strip()
        if not value:
            continue
        if value in seen:
            continue
        seen.add(value)
        combined.append(value)

    return combined


def build_self_registry_record() -> dict:
    return {
        "relayDomain": THIS_RELAY_DOMAIN,
        "advertise": RELAY_ALLOW_SELF_ADVERTISE,
        "discoveryRefreshSeconds": RELAY_DISCOVERY_REFRESH_SECONDS,
    }


def read_local_registry_payload() -> dict:
    try:
        path = Path(LOCAL_RELAY_REGISTRY_FILE)
        if not path.exists():
            return {"relays": []}
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {"relays": []}
