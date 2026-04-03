#!/usr/bin/env bash
# Dream Blue: scheduled lease comparable research + optional digest email.
# LEASE_COMP_INTERVAL_DAYS=30 (monthly) or 90 (quarterly).
#
# Install: chmod +x deploy/lease_comp_scheduled.sh
#
# Cron (check daily; script skips until interval elapsed):
#   20 7 * * * /home/erickvale/erickvale/deploy/lease_comp_scheduled.sh >> /home/erickvale/logs/lease_comp.log 2>&1
#
# Optional env:
#   LEASE_COMP_STATE=$HOME/.cache/dream_blue_lease_comp_last_run
#   LEASE_COMP_INTERVAL_DAYS=30
#   LEASE_COMP_PYTHON=/home/erickvale/erickvale/venv/bin/python
#   LEASE_COMP_SEND_DIGEST=1   # set to 0 to skip dream_blue_send_digest after success

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

STATE="${LEASE_COMP_STATE:-$HOME/.cache/dream_blue_lease_comp_last_run}"
DAYS="${LEASE_COMP_INTERVAL_DAYS:-30}"
PYTHON="${LEASE_COMP_PYTHON:-$ROOT/venv/bin/python}"
SEND_DIGEST="${LEASE_COMP_SEND_DIGEST:-1}"

export PATH="/usr/bin:/bin:$PATH"

mkdir -p "$(dirname "$STATE")"

now=$(date +%s)
if [[ -f "$STATE" ]]; then
  last=$(stat -c %Y "$STATE")
else
  last=0
fi

elapsed=$(( (now - last) / 86400 ))
if [[ "$elapsed" -lt "$DAYS" ]]; then
  echo "$(date -Iseconds) lease_comp: skip (${elapsed}d < ${DAYS}d interval)"
  exit 0
fi

echo "$(date -Iseconds) lease_comp: running dream_blue_run_lease_comp_agent"
if "$PYTHON" manage.py dream_blue_run_lease_comp_agent; then
  date +%s >"$STATE"
  echo "$(date -Iseconds) lease_comp: agent OK"
  if [[ "$SEND_DIGEST" == "1" ]]; then
    "$PYTHON" manage.py dream_blue_send_digest
    echo "$(date -Iseconds) lease_comp: dream_blue_send_digest done"
  else
    echo "$(date -Iseconds) lease_comp: skipped digest (LEASE_COMP_SEND_DIGEST=$SEND_DIGEST)"
  fi
else
  echo "$(date -Iseconds) lease_comp: agent failed (state not updated)"
  exit 1
fi
