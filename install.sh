#!/bin/bash

set -e

echo "Updating system..."
sudo apt update -y

echo "Installing dependencies..."
sudo apt install -y python3 python3-venv python3-pip git

echo "Setting up virtual environment..."
python3 -m venv venv
source venv/bin/activate

echo "Installing Python packages..."
pip install --upgrade pip
pip install -r requirements.txt

echo "Creating registry folders..."
mkdir -p registry/relays
mkdir -p registry/ids

echo "Running initial registry sync..."
python3 sync_registry.py || true

echo "Creating systemd service..."

sudo bash -c 'cat > /etc/systemd/system/blankrelay.service <<EOF
[Unit]
Description=Blank Relay
After=network.target

[Service]
User='"$USER"'
WorkingDirectory='"$(pwd)"'
ExecStart='"$(pwd)"'/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8080
Restart=always

[Install]
WantedBy=multi-user.target
EOF'

echo "Enabling service..."
sudo systemctl daemon-reexec
sudo systemctl daemon-reload
sudo systemctl enable blankrelay
sudo systemctl restart blankrelay

echo "Setting up auto registry sync..."
(crontab -l 2>/dev/null; echo "*/2 * * * * $(pwd)/venv/bin/python $(pwd)/sync_registry.py >> /tmp/registry_sync.log 2>&1") | crontab -

echo "Done."
echo "Relay is running at:"
echo "http://$(hostname -I | awk '{print $1}'):8080"
