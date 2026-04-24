from pathlib import Path
from datetime import datetime, timezone
import json

REGISTRY_BASE = Path("./registry")
RELAYS_DIR = REGISTRY_BASE / "relays"
IDS_DIR = REGISTRY_BASE / "ids"


def _count_records(folder: Path, key: str) -> int:
    total = 0
    if not folder.exists():
        return 0

    for file_path in folder.glob("*.json"):
        try:
            data = json.loads(file_path.read_text(encoding="utf-8"))
            total += len(data.get(key, []))
        except Exception:
            continue

    return total


def _latest_mtime(folder: Path):
    if not folder.exists():
        return None

    files = list(folder.glob("*.json"))
    if not files:
        return None

    latest = max(f.stat().st_mtime for f in files)
    return datetime.fromtimestamp(latest, timezone.utc).isoformat()


def cache_health():
    return {
        "success": True,
        "relayCacheCount": _count_records(RELAYS_DIR, "relays"),
        "blankIDCacheCount": _count_records(IDS_DIR, "blankIDs"),
        "relayCacheLastUpdatedAt": _latest_mtime(RELAYS_DIR),
        "blankIDCacheLastUpdatedAt": _latest_mtime(IDS_DIR),
        "checkedAt": datetime.now(timezone.utc).isoformat(),
    }
