from django.core.management.base import BaseCommand, CommandError
from django.template.loader import render_to_string
from django.utils import timezone

from dream_blue.digest_context import build_monthly_digest_context
from dream_blue.emailing import (
    DreamBlueEmailConfigError,
    get_digest_recipients,
    send_html_digest,
)
from dream_blue.models import GrantScoutRun, GrantScoutRunStatus


class Command(BaseCommand):
    help = (
        'Send the Dream Blue combined report (calendar, KPIs, leases, loans, utilities, '
        'lease economics, suggested rents, optional lease comp + GrantScout) to '
        'DREAM_BLUE_REPORT_RECIPIENTS (Resend or SMTP).'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Print recipient count and exit without sending.',
        )
        parser.add_argument(
            '--no-grantscout',
            action='store_true',
            help='Omit GrantScout section from the email body.',
        )
        parser.add_argument(
            '--subject',
            type=str,
            default='',
            help=(
                'Override email subject (default: month/year + send timestamp so Gmail '
                'does not hide repeats in one thread).'
            ),
        )

    def handle(self, *args, **options):
        recipients = get_digest_recipients()
        if not recipients:
            raise CommandError(
                'DREAM_BLUE_REPORT_RECIPIENTS is empty or unset; no recipients to send to.'
            )

        if options['dry_run']:
            self.stdout.write(
                self.style.SUCCESS(
                    f'Dry run: would send to {len(recipients)} recipient(s): '
                    + ', '.join(recipients)
                )
            )
            return

        include_gs = not options['no_grantscout']
        context = build_monthly_digest_context(include_grantscout=include_gs)

        n_cal = len(context.get('business_calendar_events') or [])
        n_kpi = len(context.get('business_kpis') or [])
        n_sec = len(context.get('business_report_sections') or [])
        lc = context.get('lease_comp_research')
        n_lc = 1 if lc is not None else 0
        n_lease = len(context.get('business_lease_schedule') or [])
        n_loan = len(context.get('business_loan_schedule') or [])
        n_util = len(context.get('business_utility_schedule') or [])
        le = context.get('lease_economics') or {}
        eco = ''
        if le.get('show_section'):
            eco = (
                f" | Lease economics: out ${le.get('monthly_out', 0):,.0f}/mo, "
                f"required GPR ${le.get('required_gross_monthly', 0):,.0f}/mo "
                f"(@ {le.get('vacancy_assumption_pct', 0)}% vacancy)"
            )
        self.stdout.write(
            self.style.SUCCESS(
                f'Operations: {n_cal} upcoming calendar row(s), {n_lease} lease(s), '
                f'{n_loan} loan(s), {n_util} utility account(s), {n_kpi} KPI(s), '
                f'{n_sec} narrative section(s), lease comp memo={n_lc}{eco}'
            )
        )

        if include_gs:
            run = context.get('grantscout_run')
            if run is None:
                n_done = GrantScoutRun.objects.filter(
                    status=GrantScoutRunStatus.COMPLETED
                ).count()
                n_any = GrantScoutRun.objects.count()
                self.stdout.write(
                    self.style.WARNING(
                        'GrantScout section will be empty: no completed run found '
                        f'(completed={n_done}, total_runs={n_any}). '
                        'Run from the same host/db as grantscout_run_agent, '
                        'or run: python manage.py grantscout_run_agent'
                    )
                )
            else:
                n_op = len(context.get('grantscout_opportunities') or [])
                self.stdout.write(
                    self.style.SUCCESS(
                        f'GrantScout: using run id={run.id} period={run.period_label} '
                        f'({n_op} opportunity rows in email)'
                    )
                )

        now = timezone.now()
        if options['subject']:
            subject = options['subject']
        else:
            # Unique subject per send — same subject every time hides new mail inside one Gmail thread.
            subject = (
                f"Dream Blue report — {now.strftime('%B %Y')} "
                f"· sent {now.strftime('%Y-%m-%d %H:%M')}"
            )

        html = render_to_string('dream_blue/emails/monthly_digest.html', context)

        self.stdout.write('Recipients: ' + ', '.join(recipients))
        try:
            send_html_digest(subject, html, recipients=recipients)
        except DreamBlueEmailConfigError as e:
            raise CommandError(str(e)) from e

        self.stdout.write(
            self.style.SUCCESS(f'Sent digest "{subject}" to {len(recipients)} recipient(s).')
        )
