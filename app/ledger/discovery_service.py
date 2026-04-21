import threading
import time

from app.config import RELAY_DISCOVERY_REFRESH_SECONDS
from app.ledger.dynamic_peers import set_dynamic_peers
from app.ledger.relay_registry import fetch_registry_relays
from app.ledger.url_normalizer import normalize_relay_url
from app.ledger.validator_config import THIS_RELAY_DOMAIN


def refresh_peers_once():
    relays = fetch_registry_relays()

    self_normalized = normalize_relay_url(THIS_RELAY_DOMAIN)

    filtered = []
    for relay in relays:
        if normalize_relay_url(relay) == self_normalized:
            continue
        filtered.append(relay)

    set_dynamic_peers(filtered)


def discovery_loop():
    while True:
        try:
            refresh_peers_once()
        except Exception:
            pass
        time.sleep(RELAY_DISCOVERY_REFRESH_SECONDS)


def start_discovery_loop():
    thread = threading.Thread(target=discovery_loop, daemon=True)
    thread.start()
