#!/usr/bin/env bash
set -e

echo "=== Blank Relay Installer ==="

if [ "$EUID" -eq 0 ]; then
  echo "Run as normal user, not root."
  exit 1
fi

read -p "Relay domain, example relay.example.com: " RELAY_DOMAIN

sudo apt update
sudo apt install -y python3 python3-venv python3-pip git sqlite3 curl

cd ~
if [ ! -d "BlankRelay" ]; then
  git clone https://github.com/BlankNetworks/BlankRelay.git
fi

cd ~/BlankRelay
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

cat > .env <<EOF
APP_HOST=0.0.0.0
APP_PORT=8080
RELAY_DOMAIN=$RELAY_DOMAIN
DATABASE_URL=sqlite:///./blankcoms.db
ADMIN_DELETE_TOKEN=change-this-to-random-string
MULTI_RELAY_MODE=false
LEDGER_QUORUM_SIZE=1
RELAY_SYNC_SOURCE_WEIGHT=100
RELAY_MAX_SYNC_CLIENTS=3
RELAY_JOIN_BLOCK_CLIENT_WRITES=true
RELAY_JOIN_MODE=false
RELAY_AUTO_EXIT_JOIN_MODE_ON_SYNC=true
RELAY_REGISTRY_URL=https://blankregistry.duckdns.org/relays
RELAY_DISCOVERY_REFRESH_SECONDS=60
USE_LOCAL_RELAY_REGISTRY=true
LOCAL_RELAY_REGISTRY_FILE=./registry/relays
BLANKID_REGISTRY_URL=https://blankidregistry.duckdns.org
EOF

mkdir -p registry/relays registry/ids uploads/profile_photos

python3 sync_registry.py || true
python3 optimize_db.py || true

sudo tee /etc/systemd/system/blankrelay.service > /dev/null <<EOF
[Unit]
Description=Blank Relay
After=network-online.target
Wants=network-online.target

[Service]
User=$USER
WorkingDirectory=$HOME/BlankRelay
EnvironmentFile=$HOME/BlankRelay/.env
ExecStart=$HOME/BlankRelay/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8080
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable blankrelay
sudo systemctl restart blankrelay

sleep 3
curl http://127.0.0.1:8080/health
echo
echo "Relay installed."

