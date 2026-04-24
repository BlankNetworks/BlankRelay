import sqlite3
from pathlib import Path

db_path = Path("blankcoms.db")

conn = sqlite3.connect(db_path)
cur = conn.cursor()

cur.execute("PRAGMA journal_mode=WAL;")
cur.execute("PRAGMA synchronous=NORMAL;")
cur.execute("PRAGMA temp_store=MEMORY;")
cur.execute("PRAGMA busy_timeout=5000;")

indexes = [
    "CREATE INDEX IF NOT EXISTS idx_users_blank_id ON users(blank_id);",
    "CREATE INDEX IF NOT EXISTS idx_user_devices_blank_id ON user_devices(blank_id);",
    "CREATE INDEX IF NOT EXISTS idx_user_devices_device_id ON user_devices(device_id);",
    "CREATE INDEX IF NOT EXISTS idx_user_devices_last_seen_at ON user_devices(last_seen_at);",
    "CREATE INDEX IF NOT EXISTS idx_message_envelopes_recipient ON message_envelopes(recipient_blank_id, recipient_device_id);",
    "CREATE INDEX IF NOT EXISTS idx_message_envelopes_sender ON message_envelopes(sender_blank_id, sender_device_id);",
    "CREATE INDEX IF NOT EXISTS idx_message_envelopes_conversation ON message_envelopes(conversation_id);",
    "CREATE INDEX IF NOT EXISTS idx_message_envelopes_delivered ON message_envelopes(is_delivered_or_processed);",
    "CREATE INDEX IF NOT EXISTS idx_prekey_bundles_blank_device ON prekey_bundles(blank_id, device_id);",
    "CREATE INDEX IF NOT EXISTS idx_one_time_prekeys_bundle_used ON one_time_prekeys(bundle_id, is_used);",
]

for sql in indexes:
    cur.execute(sql)

conn.commit()

cur.execute("PRAGMA journal_mode;")
journal = cur.fetchone()[0]

conn.close()

print({"status": "ok", "journal_mode": journal, "indexes": len(indexes)})
