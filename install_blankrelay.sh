#!/usr/bin/env bash
set -e

REPO_URL="https://github.com/BlankNetworks/BlankRelay.git"
INSTALL_DIR="$HOME/BlankRelay"

echo "BlankRelay installer"
echo "==================="

read -p "Enter your DDNS / relay domain (example: yourrelay.duckdns.org): " RELAY_DOMAIN
if [ -z "$RELAY_DOMAIN" ]; then
  echo "Relay domain is required."
  exit 1
fi

read -p "Enter your admin token (leave blank to auto-generate): " ADMIN_TOKEN
if [ -z "$ADMIN_TOKEN" ]; then
  ADMIN_TOKEN=$(openssl rand -hex 32)
  echo ""
  echo "Generated admin token:"
  echo "$ADMIN_TOKEN"
  echo ""
  echo "Save this token somewhere safe."
  echo ""
fi

echo "Installing system packages..."
sudo apt update
sudo apt install -y git python3 python3-venv python3-pip curl openssl

if [ -d "$INSTALL_DIR" ]; then
  echo "Existing BlankRelay directory found at $INSTALL_DIR"
  read -p "Remove it and reinstall? (y/N): " REINSTALL
  if [ "$REINSTALL" = "y" ] || [ "$REINSTALL" = "Y" ]; then
    rm -rf "$INSTALL_DIR"
  else
    echo "Installation cancelled."
    exit 1
  fi
fi

echo "Cloning BlankRelay..."
git clone "$REPO_URL" "$INSTALL_DIR"
cd "$INSTALL_DIR"

echo "Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo "Writing .env..."
cat > .env <<EOF
APP_HOST=0.0.0.0
APP_PORT=8080
EMAIL_DOMAIN=blank.mail
CORS_ORIGINS=*
ALLOW_ID_REUSE_AFTER_DELETE=false
ADMIN_DELETE_TOKEN=$ADMIN_TOKEN
DATABASE_URL=sqlite:///./blankcoms.db

MULTI_RELAY_MODE=false
LEDGER_QUORUM_SIZE=1

RELAY_DOMAIN=$RELAY_DOMAIN
RELAY_SYNC_SOURCE_WEIGHT=100
RELAY_MAX_SYNC_CLIENTS=3
RELAY_JOIN_BLOCK_CLIENT_WRITES=true
RELAY_JOIN_MODE=false
RELAY_AUTO_EXIT_JOIN_MODE_ON_SYNC=true

RELAY_REGISTRY_URL=
RELAY_DISCOVERY_REFRESH_SECONDS=60
RELAY_ALLOW_SELF_ADVERTISE=true
LOCAL_RELAY_REGISTRY_FILE=./relay_registry.json
USE_LOCAL_RELAY_REGISTRY=true
PEER_RELAYS=
EOF

echo "Writing relay_registry.json..."
cat > relay_registry.json <<EOF
{
  "relays": [
    "https://$RELAY_DOMAIN"
  ]
}
EOF

echo "Creating systemd service..."
sudo tee /etc/systemd/system/blank-coms-backend.service > /dev/null <<EOF
[Unit]
Description=Blank Coms Backend
After=network.target

[Service]
User=$USER
WorkingDirectory=$INSTALL_DIR
Environment=PYTHONUNBUFFERED=1
ExecStart=$INSTALL_DIR/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8080
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

echo "Reloading systemd..."
sudo systemctl daemon-reload
sudo systemctl enable blank-coms-backend
sudo systemctl restart blank-coms-backend

sleep 3

echo ""
echo "Checking health..."
curl http://127.0.0.1:8080/health || true
echo ""
echo ""
echo "Installation complete."
echo ""
echo "Your relay domain: $RELAY_DOMAIN"
echo "Your admin token:  $ADMIN_TOKEN"
echo ""
echo "Important:"
echo "- Save your admin token securely"
echo "- Forward TCP port 8080 on your router to this machine"
echo "- Test externally: http://$RELAY_DOMAIN:8080/health"
echo ""
echo "Useful commands:"
echo "sudo systemctl status blank-coms-backend --no-pager"
echo "sudo journalctl -u blank-coms-backend -n 50 --no-pager"
echo "curl http://127.0.0.1:8080/ledger/network-mode"
