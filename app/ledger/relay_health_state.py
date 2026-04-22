from threading import Lock
from datetime import datetime, timezone

_state = {
    "startedAt": datetime.now(timezone.utc).isoformat(),
    "lastRegistryRegisterAt": None,
    "lastRegistryHeartbeatAt": None,
    "lastDiscoveryRefreshAt": None,
    "lastSyncCheckAt": None,
    "lastRepoSyncAt": None,
    "status": "starting",
}
_lock = Lock()


def set_health_value(key: str, value):
    with _lock:
        _state[key] = value


def get_health_state():
    with _lock:
        return dict(_state)
