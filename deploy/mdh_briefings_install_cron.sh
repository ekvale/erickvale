#!/usr/bin/env bash
# Install (or show) the daily MDH leadership digest cron for user erickvale.
#
#   bash deploy/mdh_briefings_install_cron.sh          # print line only
#   bash deploy/mdh_briefings_install_cron.sh --install
#
# Default: 6:30 AM server local time (often UTC on DO — adjust for Central).

set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
LOG_DIR="${LOG_DIR:-/home/erickvale/logs}"
# Monday–Friday only (field 5 = 1-5)
CRON_LINE="30 6 * * 1-5 cd ${ROOT} && ${ROOT}/deploy/mdh_briefings_daily_digest.sh >> ${LOG_DIR}/mdh_briefings_digest.log 2>&1"

mkdir -p "${LOG_DIR}"
chmod +x "${ROOT}/deploy/mdh_briefings_daily_digest.sh"

echo "MDH digest cron line:"
echo "  ${CRON_LINE}"
echo ""

if [[ "${1:-}" != "--install" ]]; then
  echo "To install for the current user:"
  echo "  bash deploy/mdh_briefings_install_cron.sh --install"
  echo ""
  echo "For 6:30 AM America/Chicago on a UTC server, use 30 11 * * 1-5 (CST) or 30 12 * * 1-5 (CDT)."
  exit 0
fi

if crontab -l 2>/dev/null | grep -q 'mdh_briefings_daily_digest'; then
  echo "Cron already contains mdh_briefings_daily_digest — no change."
  crontab -l | grep mdh_briefings_daily_digest || true
  exit 0
fi

( crontab -l 2>/dev/null || true; echo "${CRON_LINE}" ) | crontab -
echo "Installed. Verify with: crontab -l | grep mdh"
echo "Status anytime: python manage.py mdh_briefings_cron_status"
