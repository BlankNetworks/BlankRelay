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


def normalize_relay_value(relay) -> str:
    if isinstance(relay, str):
        value = relay.strip()
        if not value:
            return ""
        return value

    if isinstance(relay, dict):
        value = str(relay.get("relayDomain", "")).strip()
        if not value:
            return ""
        if value.startswith("http://") or value.startswith("https://"):
            return value
        return f"https://{value}"

    return ""


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
            value = normalize_relay_value(relay)
            if value:
                clean.append(value)
        return clean
    except Exception:
        return []


def fetch_local_registry_relays() -> list[str]:
    if not USE_LOCAL_RELAY_REGISTRY:
        return []

    try:
        path = Path(LOCAL_RELAY_REGISTRY_FILE)

        files = []
        if path.is_dir():
            files = sorted(path.glob("*.json"))
        elif path.exists():
            files = [path]
        else:
            parent = path.parent
            if parent.exists() and parent.is_dir():
                files = sorted(parent.glob("*.json"))
            else:
                return []

        clean = []
        for file_path in files:
            try:
                data = json.loads(file_path.read_text(encoding="utf-8"))
                relays = data.get("relays", [])
                for relay in relays:
                    value = normalize_relay_value(relay)
                    if value:
                        clean.append(value)
            except Exception:
                continue

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

