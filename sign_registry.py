from pathlib import Path
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
import base64

BASE = Path(__file__).resolve().parent
PRIVATE_KEY_PATH = BASE / "registry_keys" / "registry_private_key.pem"

TARGET_DIRS = [
    BASE / "registry" / "relays",
    BASE / "registry" / "ids",
]

private_key = serialization.load_pem_private_key(
    PRIVATE_KEY_PATH.read_bytes(),
    password=None,
)

for folder in TARGET_DIRS:
    folder.mkdir(parents=True, exist_ok=True)

    for file_path in folder.glob("*.json"):
        if file_path.name.endswith(".sig"):
            continue

        data = file_path.read_bytes()
        signature = private_key.sign(data)
        sig_path = file_path.with_suffix(file_path.suffix + ".sig")
        sig_path.write_text(base64.b64encode(signature).decode("utf-8"), encoding="utf-8")
        print(f"signed {file_path}")
