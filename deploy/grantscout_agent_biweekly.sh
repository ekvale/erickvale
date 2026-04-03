#!/usr/bin/env bash
# Run GrantScout LLM agent at most once every GRANTSCOUT_INTERVAL_DAYS (default 14).
# Install: chmod +x deploy/grantscout_agent_biweekly.sh
#
# Cron (check daily; script skips until interval elapsed):
#   15 7 * * * /home/erickvale/erickvale/deploy/grantscout_agent_biweekly.sh >> /home/erickvale/logs/grantscout.log 2>&1
#
# Optional env (e.g. in cron line or a small wrapper):
#   GRANTSCOUT_STATE=$HOME/.cache/dream_blue_grantscout_last_run
#   GRANTSCOUT_INTERVAL_DAYS=14
#   GRANTSCOUT_PYTHON=/home/erickvale/erickvale/venv/bin/python
#   GRANTSCOUT_SEND_DIGEST=1   # set to 0 to skip dream_blue_send_digest after a successful agent run

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

STATE="${GRANTSCOUT_STATE:-$HOME/.cache/dream_blue_grantscout_last_run}"
DAYS="${GRANTSCOUT_INTERVAL_DAYS:-14}"
PYTHON="${GRANTSCOUT_PYTHON:-$ROOT/venv/bin/python}"
SEND_DIGEST="${GRANTSCOUT_SEND_DIGEST:-1}"

export PATH="/usr/bin:/bin:$PATH"

mkdir -p "$(dirname "$STATE")"

now=$(date +%s)
if [[ -f "$STATE" ]]; then
  last=$(stat -c %Y "$STATE")
else
  last=0
fi

elapsed=$(( (now - last) / 86400 ))
if (( elapsed < DAYS )); then
  echo "$(date -Iseconds) grantscout: skip (${elapsed}d since last run; interval ${DAYS}d)"
  exit 0
fi

"$PYTHON" manage.py grantscout_run_agent
touch "$STATE"
echo "$(date -Iseconds) grantscout: completed grantscout_run_agent"

if [[ "$SEND_DIGEST" == "1" || "$SEND_DIGEST" == "true" || "$SEND_DIGEST" == "yes" ]]; then
  "$PYTHON" manage.py dream_blue_send_digest
  echo "$(date -Iseconds) grantscout: completed dream_blue_send_digest"
else
  echo "$(date -Iseconds) grantscout: skipped dream_blue_send_digest (GRANTSCOUT_SEND_DIGEST=$SEND_DIGEST)"
fi
