"""
Check whether the MDH daily digest cron is installed and whether recent runs logged output.

  python manage.py mdh_briefings_cron_status
"""

from __future__ import annotations

import subprocess
from datetime import datetime
from pathlib import Path

from django.core.management.base import BaseCommand
from django.utils import timezone

from mdh_briefings.digest import get_digest_recipients
from mdh_briefings.email_probe import run_email_probe

DEFAULT_LOG = Path('/home/erickvale/logs/mdh_briefings_digest.log')
CRON_MARKER = 'mdh_briefings_daily_digest'


class Command(BaseCommand):
    help = 'Show MDH digest cron installation hints and recent log output.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--log',
            default=str(DEFAULT_LOG),
            help=f'Path to cron log file (default: {DEFAULT_LOG})',
        )

    def handle(self, *args, **options):
        log_path = Path(options['log'])
        recipients = get_digest_recipients()

        self.stdout.write('MDH daily digest — cron & delivery status')
        self.stdout.write(f'  Server local time: {timezone.localtime().strftime("%Y-%m-%d %H:%M:%S %Z")}')
        self.stdout.write(f'  Recipients: {recipients or "(none — set MDH_BRIEFINGS_DIGEST_RECIPIENTS)"}')

        probe = run_email_probe(send=False)
        cfg = probe.get('delivery_config') or {}
        self.stdout.write(
            f'  Email backend: '
            f'{"resend" if cfg.get("resend_configured") else "smtp" if cfg.get("smtp_configured") else "NOT CONFIGURED"}'
        )

        self.stdout.write('')
        self.stdout.write('Cron (crontab -l):')
        cron_lines = self._read_crontab()
        mdh_lines = [ln for ln in cron_lines if CRON_MARKER in ln or 'send_mdh_briefings_digest' in ln]
        if mdh_lines:
            for ln in mdh_lines:
                self.stdout.write(self.style.SUCCESS(f'  {ln}'))
        else:
            self.stdout.write(
                self.style.WARNING(
                    '  No MDH digest cron line found. Install with:\n'
                    '    bash deploy/mdh_briefings_install_cron.sh'
                )
            )

        self.stdout.write('')
        self.stdout.write(f'Log file: {log_path}')
        if log_path.is_file():
            stat = log_path.stat()
            mtime = datetime.fromtimestamp(stat.st_mtime)
            self.stdout.write(f'  Last modified: {mtime.isoformat(sep=" ", timespec="seconds")}')
            tail = log_path.read_text(encoding='utf-8', errors='replace').splitlines()[-25:]
            if tail:
                self.stdout.write('  Last lines:')
                for line in tail:
                    self.stdout.write(f'    {line}')
            else:
                self.stdout.write('  (empty file)')
        else:
            self.stdout.write(
                self.style.WARNING(
                    '  Log not found — cron may never have run. '
                    'mkdir -p /home/erickvale/logs then install cron.'
                )
            )

        self.stdout.write('')
        self.stdout.write('Manual send now:')
        self.stdout.write('  python manage.py send_mdh_briefings_digest')
        self.stdout.write('Quick test email:')
        self.stdout.write('  python manage.py send_mdh_email_probe')

    def _read_crontab(self) -> list[str]:
        try:
            proc = subprocess.run(
                ['crontab', '-l'],
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
        except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
            return []
        if proc.returncode != 0:
            return []
        return [ln.strip() for ln in proc.stdout.splitlines() if ln.strip() and not ln.startswith('#')]
