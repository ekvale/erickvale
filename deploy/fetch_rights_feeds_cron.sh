#!/bin/bash
# Run from cron every 6 hours to fetch and save only tagged articles for the Rights Archive.
# Install: chmod +x deploy/fetch_rights_feeds_cron.sh
# Cron: 0 */6 * * * /home/erickvale/erickvale/deploy/fetch_rights_feeds_cron.sh

set -e
cd "$(dirname "$0")/.."
export PATH="/usr/bin:/bin:$PATH"
./venv/bin/python manage.py fetch_rights_feeds --force --tagged-only
