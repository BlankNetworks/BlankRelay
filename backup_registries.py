import json
import os
from datetime import datetime, timezone
from pathlib import Path

import requests

BASE = Path.home() / "blank-coms-backend"
BACKUP_RELAYS = BASE / "registry_backups" / "relays"
BACKUP_IDS = BASE / "registry_backups" / "ids"
BACKUP_RELAYS.mkdir(parents=True, exist_ok=True)
BACKUP_IDS.mkdir(parents=True, exist_ok=True)

def now_stamp():
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

def write_backup(folder: Path, name: str, payload: dict):
    stamp = now_stamp()
    file_path = folder / f"{name}_{stamp}.json"
    file_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    latest = folder / f"{name}_latest.json"
    latest.write_text(json.dumps(payload, indent=2), encoding="utf-8")

def fetch_json(url: str):
    r = requests.get(url, timeout=15)
    r.raise_for_status()
    return r.json()

def prune(folder: Path, keep: int = 50):
    files = sorted(folder.glob("*.json"))
    backup_files = [f for f in files if not f.name.endswith("_latest.json")]
    for old in backup_files[:-keep]:
        old.unlink(missing_ok=True)

relay_payload = fetch_json("https://blankregistry.duckdns.org/relays")
id_payload = fetch_json("https://blankidregistry.duckdns.org/all")

write_backup(BACKUP_RELAYS, "relays", relay_payload)
write_backup(BACKUP_IDS, "blankids", id_payload)

prune(BACKUP_RELAYS)
prune(BACKUP_IDS)

print("backup complete")
