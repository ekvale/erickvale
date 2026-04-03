from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from dream_blue.lease_comp_agent import GrantScoutAgentError, run_lease_comp_agent
from dream_blue.lease_comp_report_diff import build_lease_comp_diff_summary
from dream_blue.models import GrantScoutRunStatus, LeaseCompResearchRun


class Command(BaseCommand):
    help = (
        'Run the lease / flex comparables LLM agent (same provider as GrantScout; use '
        'GRANTSCOUT_LLM_PROVIDER=perplexity + PERPLEXITY_API_KEY for fresher listings) and '
        'save a LeaseCompResearchRun. Latest completed run appears in dream_blue_send_digest.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Call the LLM and print a preview; do not write to the database.',
        )
        parser.add_argument(
            '--reference',
            type=str,
            default='',
            help='Override DREAM_BLUE_LEASE_COMP_REFERENCE for this run only.',
        )
        parser.add_argument(
            '--subject',
            type=str,
            default='',
            help='Override DREAM_BLUE_LEASE_COMP_SUBJECT for this run only.',
        )

    def handle(self, *args, **options):
        ref = (options['reference'] or '').strip() or None
        subj = (options['subject'] or '').strip() or None
        try:
            payload = run_lease_comp_agent(reference=ref, subject=subj)
        except GrantScoutAgentError as e:
            raise CommandError(str(e)) from e

        cov = payload['coverage_summary']
        preview = f'{cov[:220]}…' if len(cov) > 220 else cov
        self.stdout.write(self.style.SUCCESS(f'Coverage: {preview}'))
        body_preview = payload['report_markdown'][:400]
        self.stdout.write(
            self.style.NOTICE('Report preview:\n' + body_preview + ('…' if len(payload['report_markdown']) > 400 else ''))
        )

        if options['dry_run']:
            self.stdout.write(self.style.WARNING('Dry run: no database changes.'))
            return

        snap = {
            'coverage_summary': payload['coverage_summary'],
            'search_queries': payload['search_queries'],
            'report_markdown': payload['report_markdown'],
            'saved_at': timezone.now().isoformat(),
        }
        prev = (
            LeaseCompResearchRun.objects.filter(status=GrantScoutRunStatus.COMPLETED)
            .order_by('-created_at')
            .first()
        )
        with transaction.atomic():
            run = LeaseCompResearchRun.objects.create(
                status=GrantScoutRunStatus.DRAFT,
                coverage_summary=payload['coverage_summary'],
                search_query_log=payload['search_queries'],
                compiled_report=payload['report_markdown'],
                agent_snapshot=snap,
                previous_run=prev,
            )
            diff_summary = ''
            if prev and (prev.compiled_report or '').strip():
                diff_summary = build_lease_comp_diff_summary(
                    prev.compiled_report,
                    run.compiled_report,
                )
            run.report_diff_summary = diff_summary
            run.status = GrantScoutRunStatus.COMPLETED
            run.save(update_fields=['status', 'report_diff_summary', 'updated_at'])

        self.stdout.write(
            self.style.SUCCESS(
                f'Saved LeaseCompResearchRun id={run.id} ({run.get_status_display()}).'
            ),
        )
