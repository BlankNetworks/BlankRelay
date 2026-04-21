import threading
import time

from app.ledger.registry_client import heartbeat_registry, register_with_registry

REGISTRY_HEARTBEAT_SECONDS = 60


def registry_heartbeat_loop():
    while True:
        try:
            register_with_registry()
            heartbeat_registry()
        except Exception:
            pass
        time.sleep(REGISTRY_HEARTBEAT_SECONDS)


def start_registry_heartbeat():
    thread = threading.Thread(target=registry_heartbeat_loop, daemon=True)
    thread.start()
