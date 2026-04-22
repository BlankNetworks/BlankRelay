#!/bin/bash
set -u

echo "=== Blank Relay Verification ==="
echo

PASS_COUNT=0
FAIL_COUNT=0

pass() {
  echo "[PASS] $1"
  PASS_COUNT=$((PASS_COUNT + 1))
}

fail() {
  echo "[FAIL] $1"
  FAIL_COUNT=$((FAIL_COUNT + 1))
}

check_contains() {
  local file="$1"
  local pattern="$2"
  local label="$3"

  if grep -q "$pattern" "$file" 2>/dev/null; then
    pass "$label"
  else
    fail "$label"
  fi
}

echo "--- Paths ---"
[ -d ~/blank-coms-backend ] && pass "Relay A repo exists" || fail "Relay A repo missing"
[ -f ~/blank-coms-backend/.env ] && pass ".env exists" || fail ".env missing"
[ -f ~/blank-coms-backend/sync_registry.py ] && pass "sync_registry.py exists" || fail "sync_registry.py missing"
[ -f ~/blank-coms-backend/app/main.py ] && pass "app/main.py exists" || fail "app/main.py missing"
[ -f ~/blank-coms-backend/app/ledger/local_registry_index.py ] && pass "local_registry_index.py exists" || fail "local_registry_index.py missing"
[ -f ~/blank-coms-backend/app/ledger/peer_scoring.py ] && pass "peer_scoring.py exists" || fail "peer_scoring.py missing"
[ -f ~/blank-coms-backend/app/ledger/relay_health_state.py ] && pass "relay_health_state.py exists" || fail "relay_health_state.py missing"

echo
echo "--- .env checks ---"
check_contains ~/blank-coms-backend/.env '^USE_LOCAL_RELAY_REGISTRY=true' "USE_LOCAL_RELAY_REGISTRY=true"
check_contains ~/blank-coms-backend/.env '^LOCAL_RELAY_REGISTRY_FILE=./registry/relays' "LOCAL_RELAY_REGISTRY_FILE set"
check_contains ~/blank-coms-backend/.env '^RELAY_REGISTRY_URL=https://blankregistry.duckdns.org/relays' "RELAY_REGISTRY_URL set"
check_contains ~/blank-coms-backend/.env '^BLANKID_REGISTRY_URL=https://blankidregistry.duckdns.org' "BLANKID_REGISTRY_URL set"
check_contains ~/blank-coms-backend/.env '^RELAY_DOMAIN=' "RELAY_DOMAIN exists"

echo
echo "--- Local cache files ---"
[ -d ~/blank-coms-backend/registry/relays ] && pass "registry/relays dir exists" || fail "registry/relays dir missing"
[ -d ~/blank-coms-backend/registry/ids ] && pass "registry/ids dir exists" || fail "registry/ids dir missing"
ls ~/blank-coms-backend/registry/relays/*.json >/dev/null 2>&1 && pass "relay chunk files exist" || fail "relay chunk files missing"
ls ~/blank-coms-backend/registry/ids/*.json >/dev/null 2>&1 && pass "id chunk files exist" || fail "id chunk files missing"

echo
echo "--- Code checks ---"
check_contains ~/blank-coms-backend/app/main.py 'publish_blankid(' "register publishes BlankID"
check_contains ~/blank-coms-backend/app/main.py '@app.get("/relay/health")' "relay health endpoint exists"
check_contains ~/blank-coms-backend/app/main.py '@app.get("/relay/peers")' "relay peers endpoint exists"
check_contains ~/blank-coms-backend/app/main.py 'start_peer_scoring()' "peer scoring starts at boot"
check_contains ~/blank-coms-backend/app/main.py 'start_registry_heartbeat()' "registry heartbeat starts at boot"
check_contains ~/blank-coms-backend/app/main.py 'start_discovery_loop()' "discovery loop starts at boot"
check_contains ~/blank-coms-backend/app/ledger/blankid_registry_client.py 'def lookup_blankid_local' "local BlankID lookup exists"
check_contains ~/blank-coms-backend/app/ledger/blankid_registry_client.py 'def lookup_blankid(' "BlankID lookup exists"
check_contains ~/blank-coms-backend/app/ledger/relay_registry.py 'def fetch_local_registry_relays' "local relay registry loader exists"

echo
echo "--- Service checks ---"
systemctl is-enabled blank-coms-backend >/dev/null 2>&1 && pass "blank-coms-backend enabled" || fail "blank-coms-backend not enabled"
systemctl is-active blank-coms-backend >/dev/null 2>&1 && pass "blank-coms-backend active" || fail "blank-coms-backend not active"

echo
echo "--- HTTP checks ---"
curl -fsS http://127.0.0.1:8080/health >/dev/null 2>&1 && pass "/health responds" || fail "/health failed"
curl -fsS http://127.0.0.1:8080/relay/health >/dev/null 2>&1 && pass "/relay/health responds" || fail "/relay/health failed"
curl -fsS http://127.0.0.1:8080/relay/peers >/dev/null 2>&1 && pass "/relay/peers responds" || fail "/relay/peers failed"
curl -fsS http://127.0.0.1:8080/ledger/discovery-status >/dev/null 2>&1 && pass "/ledger/discovery-status responds" || fail "/ledger/discovery-status failed"

echo
echo "--- Cron checks ---"
crontab -l 2>/dev/null | grep -q 'sync_registry.py' && pass "registry sync cron exists" || fail "registry sync cron missing"
crontab -l 2>/dev/null | grep -q 'update_blankrelay.sh' && pass "nightly update cron exists" || fail "nightly update cron missing"

echo
echo "=== Summary ==="
echo "Pass: $PASS_COUNT"
echo "Fail: $FAIL_COUNT"

if [ "$FAIL_COUNT" -eq 0 ]; then
  echo "Overall: OK"
  exit 0
else
  echo "Overall: NEEDS ATTENTION"
  exit 1
fi
