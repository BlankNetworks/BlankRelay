import threading
import time
from datetime import datetime, timezone

import requests

from app.ledger.dynamic_peers import get_all_peers
from app.ledger.relay_health_state import set_health_value

_scores = {}
_lock = threading.Lock()


def _now():
    return datetime.now(timezone.utc).isoformat()


def get_peer_scores():
    with _lock:
        return dict(_scores)


def check_peer(peer: str):
    score = {
        "peer": peer,
        "reachable": False,
        "admissionOk": False,
        "headOk": False,
        "latencyMs": None,
        "lastCheckedAt": _now(),
    }

    started = time.time()
    try:
        r1 = requests.get(f"{peer}/ledger/admission-status", timeout=4)
        if r1.status_code == 200:
            score["admissionOk"] = True

        r2 = requests.get(f"{peer}/ledger/blocks/head", timeout=4)
        if r2.status_code == 200:
            score["headOk"] = True

        score["reachable"] = score["admissionOk"] and score["headOk"]
        score["latencyMs"] = int((time.time() - started) * 1000)
    except Exception:
        pass

    with _lock:
        _scores[peer] = score


def peer_score_loop():
    while True:
        peers = get_all_peers()
        for peer in peers:
            check_peer(peer)
        set_health_value("lastSyncCheckAt", _now())
        time.sleep(60)


def start_peer_scoring():
    thread = threading.Thread(target=peer_score_loop, daemon=True)
    thread.start()
