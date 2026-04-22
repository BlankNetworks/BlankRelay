import threading
import time
from datetime import datetime, timezone

from app.ledger.registry_client import heartbeat_registry, register_with_registry
from app.ledger.relay_health_state import set_health_value

REGISTRY_HEARTBEAT_SECONDS = 60


def _now():
    return datetime.now(timezone.utc).isoformat()


def registry_heartbeat_loop():
    while True:
        try:
            if register_with_registry():
                set_health_value("lastRegistryRegisterAt", _now())
            if heartbeat_registry():
                set_health_value("lastRegistryHeartbeatAt", _now())
                set_health_value("status", "healthy")
        except Exception:
            set_health_value("status", "degraded")
        time.sleep(REGISTRY_HEARTBEAT_SECONDS)


def start_registry_heartbeat():
    thread = threading.Thread(target=registry_heartbeat_loop, daemon=True)
    thread.start()
