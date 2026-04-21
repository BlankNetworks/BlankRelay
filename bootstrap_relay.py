import secrets
from pathlib import Path


ENV_PATH = Path(".env")
REGISTRY_PATH = Path("relay_registry.json")


def ask(prompt: str, default: str = "") -> str:
    suffix = f" [{default}]" if default else ""
    value = input(f"{prompt}{suffix}: ").strip()
    return value or default


def generate_admin_token() -> str:
    return secrets.token_hex(32)


def write_env(relay_domain: str, admin_token: str) -> None:
    content = f"""APP_HOST=0.0.0.0
APP_PORT=8080
EMAIL_DOMAIN=blank.mail
CORS_ORIGINS=*
ALLOW_ID_REUSE_AFTER_DELETE=false
ADMIN_DELETE_TOKEN={admin_token}
DATABASE_URL=sqlite:///./blankcoms.db

MULTI_RELAY_MODE=false
LEDGER_QUORUM_SIZE=1

RELAY_DOMAIN={relay_domain}
RELAY_SYNC_SOURCE_WEIGHT=100
RELAY_MAX_SYNC_CLIENTS=3
RELAY_JOIN_BLOCK_CLIENT_WRITES=true
RELAY_JOIN_MODE=false
RELAY_AUTO_EXIT_JOIN_MODE_ON_SYNC=true

RELAY_REGISTRY_URL=
RELAY_DISCOVERY_REFRESH_SECONDS=60
RELAY_ALLOW_SELF_ADVERTISE=true
LOCAL_RELAY_REGISTRY_FILE=./relay_registry.json
USE_LOCAL_RELAY_REGISTRY=true
PEER_RELAYS=
"""
    ENV_PATH.write_text(content, encoding="utf-8")


def write_registry() -> None:
    if not REGISTRY_PATH.exists():
        REGISTRY_PATH.write_text('{\n  "relays": []\n}\n', encoding="utf-8")


def main():
    print("Blank Relay Bootstrap")
    relay_domain = ask("Enter your DDNS / relay domain", "blankcoms.duckdns.org")
    generated_token = generate_admin_token()
    admin_token = ask("Enter admin token", generated_token)

    write_env(relay_domain, admin_token)
    write_registry()

    print("")
    print("Bootstrap complete.")
    print("Created:")
    print(" - .env")
    print(" - relay_registry.json")
    print("")
    print("Important:")
    print(" - Save your admin token securely")
    print(" - Do not share it publicly")
    print("")
    print("Next:")
    print("  1. Review .env")
    print("  2. Restart the relay")
    print("  3. Check /health and /ledger/config-status")


if __name__ == "__main__":
    main()
