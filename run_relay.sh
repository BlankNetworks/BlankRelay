#!/usr/bin/env bash
set -e

cd "$(dirname "$0")"

if [ ! -d "venv" ]; then
  python3 -m venv venv
fi

source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

if [ ! -f ".env" ]; then
  python3 bootstrap_relay.py
fi

uvicorn app.main:app --host 0.0.0.0 --port 8080
