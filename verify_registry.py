from pathlib import Path
from cryptography.hazmat.primitives import serialization
from cryptography.exceptions import InvalidSignature
import base64
import sys

BASE = Path(__file__).resolve().parent
PUBLIC_KEY_PATH = BASE / "registry_keys" / "registry_public_key.pem"

TARGET_DIRS = [
    BASE / "registry" / "relays",
    BASE / "registry" / "ids",
]

public_key = serialization.load_pem_public_key(PUBLIC_KEY_PATH.read_bytes())

failed = False

for folder in TARGET_DIRS:
    for file_path in folder.glob("*.json"):
        sig_path = file_path.with_suffix(file_path.suffix + ".sig")

        if not sig_path.exists():
            print(f"missing signature: {file_path}")
            failed = True
            continue

        try:
            signature = base64.b64decode(sig_path.read_text(encoding="utf-8"))
            public_key.verify(signature, file_path.read_bytes())
            print(f"verified {file_path}")
        except InvalidSignature:
            print(f"invalid signature: {file_path}")
            failed = True

if failed:
    sys.exit(1)

print("registry verification ok")
