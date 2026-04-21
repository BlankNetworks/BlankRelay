#!/usr/bin/env bash
set -euo pipefail
uvicorn app.main:app --host "${APP_HOST:-127.0.0.1}" --port "${APP_PORT:-8080}"
