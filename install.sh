#!/bin/bash
set -e

echo "=== Blank Relay Install ==="

# --- basics ---
sudo apt update -y
sudo apt install -y python3 python3-venv python3-pip git curl

# --- venv ---
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# --- dirs ---
mkdir -p registry/relays
mkdir -p registry/ids

# --- detect domain/IP ---
LOCAL_IP=$(hostname -I | awk '{print $1}')
PUBLIC_IP=$(curl -s ifconfig.me || echo "")

if [ -z "$PUBLIC_IP" ]; then
  PUBLIC_IP=$LOCAL_IP
fi

# --- auto .env ---
cat > .env <<EOF
APP_HOST=0.0.0.0
APP_PORT=8080

RELAY_DOMAIN=$PUBLIC_IP

DATABASE_URL=sqlite:///./blankcoms.db

ADMIN_DELETE_TOKEN=$(openssl rand -hex 16)

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

# --- initial sync ---
python3 sync_registry.py || true

# --- install caddy ---
sudo apt install -y debian-keyring debian-archive-keyring apt-transport-https
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | sudo gpg --dearmor -o /usr/share/keyrings/caddy.gpg
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | sudo tee /etc/apt/sources.list.d/caddy-stable.list
sudo apt update -y
sudo apt install -y caddy

# --- caddy config ---
sudo bash -c "cat > /etc/caddy/Caddyfile" <<EOC
:443 {
    reverse_proxy localhost:8080
}
EOC

sudo systemctl restart caddy

# --- systemd service ---
sudo bash -c "cat > /etc/systemd/system/blankrelay.service" <<EOC
[Unit]
Description=Blank Relay
After=network.target

[Service]
User=$USER
WorkingDirectory=$(pwd)
ExecStart=$(pwd)/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8080
Restart=always

[Install]
WantedBy=multi-user.target
EOC

sudo systemctl daemon-reexec
sudo systemctl daemon-reload
sudo systemctl enable blankrelay
sudo systemctl restart blankrelay

# --- cron sync ---
(crontab -l 2>/dev/null; echo "*/2 * * * * $(pwd)/venv/bin/python $(pwd)/sync_registry.py >> /tmp/registry_sync.log 2>&1") | crontab -

echo ""
echo "=== DONE ==="
echo "Relay running on:"
echo "https://$PUBLIC_IP"
echo ""
echo "NOTE:"
echo "- For real HTTPS domain, point DNS to this IP"
echo "- Caddy will auto-provision TLS"
