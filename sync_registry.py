import os
import json
import requests

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.join(BASE_DIR, "registry")


def chunk_write(data, path, key_name, chunk_size=100):
    os.makedirs(path, exist_ok=True)

    for filename in os.listdir(path):
        if filename.endswith(".json"):
            os.remove(os.path.join(path, filename))

    for i in range(0, len(data), chunk_size):
        chunk = data[i:i + chunk_size]
        with open(f"{path}/chunk_{i // chunk_size}.json", "w", encoding="utf-8") as f:
            json.dump({key_name: chunk}, f, ensure_ascii=False, indent=2)


r = requests.get("https://blankregistry.duckdns.org/relays", timeout=10)
if r.status_code == 200:
    relays = r.json().get("relays", [])
    chunk_write(relays, f"{BASE}/relays", "relays")

r = requests.get("https://blankidregistry.duckdns.org/all", timeout=10)
if r.status_code == 200:
    ids = r.json().get("blankIDs", [])
    chunk_write(ids, f"{BASE}/ids", "blankIDs")

print("sync complete")

import subprocess
from pathlib import Path

BASE = Path(__file__).resolve().parent
PRIVATE_KEY = BASE / "registry_keys" / "registry_private_key.pem"
SELF_HEAL_MARKER = BASE / ".registry_self_heal_running"


def run_signature_check():
    if PRIVATE_KEY.exists():
        subprocess.run(["python3", str(BASE / "sign_registry.py")], check=True)
        print("registry signed")
    else:
        subprocess.run(["python3", str(BASE / "verify_registry.py")], check=True)
        print("registry verified")


try:
    run_signature_check()
except Exception as e:
    print(f"registry signature check failed: {e}")

    if PRIVATE_KEY.exists():
        print("source relay re-signing registry")
        run_signature_check()
    else:
        if SELF_HEAL_MARKER.exists():
            raise RuntimeError("registry self-heal failed after retry")

        try:
            SELF_HEAL_MARKER.write_text("1", encoding="utf-8")
            print("tamper detected; re-syncing from source of truth")
            subprocess.run(["python3", str(BASE / "sync_registry.py")], check=True)
            run_signature_check()
        finally:
            SELF_HEAL_MARKER.unlink(missing_ok=True)
