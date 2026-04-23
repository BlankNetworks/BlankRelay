import json
from pathlib import Path

import requests

from app.config import BLANKID_REGISTRY_URL
from app.ledger.local_registry_index import get_blankid


def reserve_blankid(blank_id: str, relay_domain: str) -> dict:
    try:
        response = requests.post(
            "https://blankcoms.duckdns.org/ledger/ids/reserve",
            json={
                "blankID": blank_id,
                "relayDomain": relay_domain,
            },
            timeout=5,
        )
        if response.status_code == 200:
            return response.json()
        return {"success": False, "detail": response.text}
    except Exception:
        return {"success": False, "detail": "reservation failed"}

def get_blankid_registry_base_url() -> str:
    return (BLANKID_REGISTRY_URL or "").rstrip("/")


def publish_blankid(
    blank_id: str,
    relay_domain: str,
    client_claim_hash: str,
    block_index: int,
    claimed_at: str,
) -> bool:
    registry_url = get_blankid_registry_base_url()
    if not registry_url:
        return False

    try:
        response = requests.post(
            f"{registry_url}/publish",
            json={
                "blankID": blank_id,
                "relayDomain": relay_domain,
                "clientClaimHash": client_claim_hash,
                "blockIndex": block_index,
                "claimedAt": claimed_at,
            },
            timeout=5,
        )
        return response.status_code == 200
    except Exception:
        return False


def lookup_blankid_local(blank_id: str) -> dict:
    record = get_blankid(blank_id)
    if record:
        return {"found": True, "record": record}
    return {"found": False}


def lookup_blankid(blank_id: str) -> dict:
    local = lookup_blankid_local(blank_id)
    if local.get("found"):
        return local

    registry_url = get_blankid_registry_base_url()
    if not registry_url:
        return {"found": False}

    try:
        response = requests.get(
            f"{registry_url}/lookup/{blank_id}",
            timeout=5,
        )
        if response.status_code == 200:
            return response.json()
    except Exception:
        pass

    return {"found": False}

