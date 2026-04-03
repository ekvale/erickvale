#!/usr/bin/env bash
# Email the Dream Blue combined HTML report (calendar, KPIs, loans, utilities, GrantScout).
# Does NOT run the LLM — use grantscout_run_agent first if you need a fresh Scout section.
#
# Requires env (e.g. systemd EnvironmentFile or cron): DREAM_BLUE_REPORT_RECIPIENTS,
# plus Resend (RESEND_*) or SMTP (EMAIL_HOST, DEFAULT_FROM_EMAIL, ...).
#
# Cron example (weekly report without waiting for biweekly GrantScout):
#   30 8 * * 1 cd /home/erickvale/erickvale && ./deploy/dream_blue_send_digest.sh >> /home/erickvale/logs/dream_blue_digest.log 2>&1
#
# Optional:
#   DIGEST_PYTHON=/home/erickvale/erickvale/venv/bin/python

set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
PYTHON="${DIGEST_PYTHON:-$ROOT/venv/bin/python}"
exec "$PYTHON" manage.py dream_blue_send_digest "$@"
