import json
from pathlib import Path

BASE_IDS = Path("./registry/ids")
BASE_RELAYS = Path("./registry/relays")

ID_INDEX = {}
RELAY_INDEX = []


def load_id_index():
    global ID_INDEX
    ID_INDEX = {}

    if not BASE_IDS.exists():
        return

    for file_path in sorted(BASE_IDS.glob("*.json")):
        try:
            data = json.loads(file_path.read_text(encoding="utf-8"))
            for record in data.get("blankIDs", []):
                ID_INDEX[record["blankID"]] = record
        except Exception:
            continue


def load_relay_index():
    global RELAY_INDEX
    RELAY_INDEX = []

    if not BASE_RELAYS.exists():
        return

    for file_path in sorted(BASE_RELAYS.glob("*.json")):
        try:
            data = json.loads(file_path.read_text(encoding="utf-8"))
            for r in data.get("relays", []):
                RELAY_INDEX.append(r)
        except Exception:
            continue


def get_blankid(blank_id: str):
    return ID_INDEX.get(blank_id)


def get_relays():
    return RELAY_INDEX
