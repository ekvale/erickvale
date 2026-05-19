#!/usr/bin/env bash
# Pull latest code and reload the production site (erickvale.com).
# Run on the server after SSH:  cd /home/erickvale/erickvale && bash deploy/sync_site.sh
#
# Override defaults if your layout differs:
#   DEPLOY_ROOT=/path/to/erickvale VENV_ACTIVATE=/path/to/venv/bin/activate bash deploy/sync_site.sh

set -euo pipefail

DEPLOY_ROOT="${DEPLOY_ROOT:-/home/erickvale/erickvale}"
VENV_ACTIVATE="${VENV_ACTIVATE:-/home/erickvale/erickvale/venv/bin/activate}"

cd "${DEPLOY_ROOT}"
echo "==> Working directory: $(pwd)"

if [[ ! -f "${VENV_ACTIVATE}" ]]; then
  echo "ERROR: venv not found at ${VENV_ACTIVATE}. Set VENV_ACTIVATE to your activate script." >&2
  exit 1
fi

# shellcheck source=/dev/null
source "${VENV_ACTIVATE}"

echo "==> git pull origin main"
git pull origin main

echo "==> pip install -r requirements.txt"
pip install -r requirements.txt -q

echo "==> migrate"
python manage.py migrate

if [[ -f package.json ]] && command -v npm >/dev/null 2>&1; then
  echo "==> npm run build:css (Tailwind)"
  if npm run build:css; then
    :
  else
    echo "WARN: Tailwind build failed (often Node too old). Skipping — existing tw.css unchanged." >&2
  fi
fi

echo "==> collectstatic"
python manage.py collectstatic --noinput

echo "==> restart erickvale service"
sudo systemctl restart erickvale

echo "==> Done. Check: sudo systemctl status erickvale"
