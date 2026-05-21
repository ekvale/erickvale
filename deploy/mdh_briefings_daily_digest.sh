#!/usr/bin/env bash
# Daily MDH leadership priorities + news email (Perplexity + cached briefings).
#
# Requires env: PERPLEXITY_API_KEY, MDH_BRIEFINGS_DIGEST_RECIPIENTS,
# plus Resend (RESEND_*) or SMTP (EMAIL_HOST, DEFAULT_FROM_EMAIL, ...).
#
# Cron example (6:30 AM server time):
#   30 6 * * * cd /home/erickvale/erickvale && ./deploy/mdh_briefings_daily_digest.sh >> /home/erickvale/logs/mdh_briefings_digest.log 2>&1
#
# Test delivery (no Perplexity):
#   ./deploy/mdh_briefings_daily_digest.sh --email-probe
#   python manage.py send_mdh_email_probe
#
# Optional:
#   DIGEST_PYTHON=/home/erickvale/erickvale/venv/bin/python

set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
PYTHON="${DIGEST_PYTHON:-$ROOT/venv/bin/python}"
echo "==> mdh_briefings_daily_digest $(date -Is 2>/dev/null || date) pid=$$"
exec "$PYTHON" manage.py send_mdh_briefings_digest "$@"
