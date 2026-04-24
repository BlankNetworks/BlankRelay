import json
import threading
import time
from datetime import datetime, timezone

import requests

from app.database import SessionLocal
from app.models import ForwardRetryQueue


def enqueue_forward_retry(target_url: str, payload: dict):
    db = SessionLocal()
    try:
        row = ForwardRetryQueue(
            target_url=target_url,
            payload_json=json.dumps(payload),
            attempt_count=0,
            max_attempts=10,
            status="pending",
            updated_at=datetime.now(timezone.utc).isoformat(),
        )
        db.add(row)
        db.commit()
    finally:
        db.close()


def process_retry_once():
    db = SessionLocal()
    try:
        rows = (
            db.query(ForwardRetryQueue)
            .filter(ForwardRetryQueue.status == "pending")
            .order_by(ForwardRetryQueue.created_at.asc())
            .limit(25)
            .all()
        )

        for row in rows:
            try:
                payload = json.loads(row.payload_json)
                r = requests.post(row.target_url, json=payload, timeout=8)

                if 200 <= r.status_code < 300:
                    row.status = "sent"
                    row.updated_at = datetime.now(timezone.utc).isoformat()
                    continue

                row.attempt_count += 1
                row.last_error = f"{r.status_code}: {r.text[:300]}"
            except Exception as e:
                row.attempt_count += 1
                row.last_error = str(e)

            row.updated_at = datetime.now(timezone.utc).isoformat()

            if row.attempt_count >= row.max_attempts:
                row.status = "dead"

        db.commit()
    finally:
        db.close()


def retry_loop():
    while True:
        try:
            process_retry_once()
        except Exception:
            pass
        time.sleep(15)


def start_forward_retry_worker():
    thread = threading.Thread(target=retry_loop, daemon=True)
    thread.start()
