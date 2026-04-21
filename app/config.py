import os
from os import getenv
from dotenv import load_dotenv

load_dotenv()

APP_HOST = getenv("APP_HOST", "127.0.0.1")
APP_PORT = int(getenv("APP_PORT", "8080"))
EMAIL_DOMAIN = getenv("EMAIL_DOMAIN", "blank.mail")
CORS_ORIGINS = getenv("CORS_ORIGINS", "*")
ALLOW_ID_REUSE_AFTER_DELETE = getenv("ALLOW_ID_REUSE_AFTER_DELETE", "false").lower() == "true"
ADMIN_DELETE_TOKEN = getenv("ADMIN_DELETE_TOKEN", "")
API_KEY = getenv("API_KEY", "")
DATABASE_URL = getenv("DATABASE_URL", "sqlite:///./blankrelay.db")
RELAY_DOMAIN = os.getenv("RELAY_DOMAIN", "blankcoms.duckdns.org")
MULTI_RELAY_MODE = getenv("MULTI_RELAY_MODE", "false").lower() == "true"
LEDGER_QUORUM_SIZE = int(getenv("LEDGER_QUORUM_SIZE", "1"))
PEER_RELAYS = [p.strip() for p in getenv("PEER_RELAYS", "").split(",") if p.strip()]
RELAY_SYNC_SOURCE_WEIGHT = int(getenv("RELAY_SYNC_SOURCE_WEIGHT", "100"))
RELAY_MAX_SYNC_CLIENTS = int(getenv("RELAY_MAX_SYNC_CLIENTS", "3"))
RELAY_JOIN_BLOCK_CLIENT_WRITES = getenv("RELAY_JOIN_BLOCK_CLIENT_WRITES", "true").lower() == "true"
RELAY_REGISTRY_URL = getenv("RELAY_REGISTRY_URL", "")
RELAY_DISCOVERY_REFRESH_SECONDS = int(getenv("RELAY_DISCOVERY_REFRESH_SECONDS", "60"))
RELAY_ALLOW_SELF_ADVERTISE = getenv("RELAY_ALLOW_SELF_ADVERTISE", "true").lower() == "true"
LOCAL_RELAY_REGISTRY_FILE = getenv("LOCAL_RELAY_REGISTRY_FILE", "./relay_registry.json")
USE_LOCAL_RELAY_REGISTRY = getenv("USE_LOCAL_RELAY_REGISTRY", "true").lower() == "true"
RELAY_JOIN_MODE = getenv("RELAY_JOIN_MODE", "false").lower() == "true"
RELAY_AUTO_EXIT_JOIN_MODE_ON_SYNC = getenv("RELAY_AUTO_EXIT_JOIN_MODE_ON_SYNC", "true").lower() == "true"
