import requests

def forward_post(url: str, payload: dict):
    try:
        r = requests.post(url, json=payload, timeout=5)
        return r.status_code, r.json()
    except Exception:
        return None, {"detail": "forward failed"}


def forward_get(url: str):
    try:
        r = requests.get(url, timeout=5)
        return r.status_code, r.json()
    except Exception:
        return None, {"detail": "forward failed"}


def normalize_relay_url(relay_domain: str) -> str:
    relay_domain = relay_domain.strip()
    if relay_domain.startswith("http://") or relay_domain.startswith("https://"):
        return relay_domain.rstrip("/")
    return f"https://{relay_domain}"


def forward_envelope_to_relay(relay_domain: str, envelope: dict) -> bool:
    base_url = normalize_relay_url(relay_domain)

    try:
        response = requests.post(
            f"{base_url}/api/envelopes/relay-forward",
            json={"envelope": envelope},
            timeout=10,
        )
        return response.status_code == 200
    except Exception:
        return False
