from pathlib import Path

from app.config import ADMIN_DELETE_TOKEN, RELAY_DOMAIN


def is_weak_token(value: str) -> bool:
    v = value.strip().lower()
    if len(v) < 24:
        return True
    weak_values = {
        "",
        "change-me-now",
        "admin",
        "password",
        "123456",
    }
    return v in weak_values


def run_startup_checks() -> None:
    if not RELAY_DOMAIN.strip():
        raise RuntimeError("RELAY_DOMAIN is missing")

    if not ADMIN_DELETE_TOKEN.strip():
        raise RuntimeError("ADMIN_DELETE_TOKEN is missing")

    registry_file = Path("./relay_registry.json")
    if not registry_file.exists():
        registry_file.write_text('{\n  "relays": []\n}\n', encoding="utf-8")
