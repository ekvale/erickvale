"""Preview stored GrantScout report shape + operations appendix (no LLM call)."""

from pathlib import Path

from django.core.management.base import BaseCommand

from dream_blue.digest_context import build_operations_calendar_markdown
from dream_blue.grantscout_reports import build_compiled_report

_SAMPLE_PAYLOAD = {
    'coverage_summary': (
        'Sample coverage (no LLM). Set OPENAI_API_KEY and run grantscout_run_agent for live output.'
    ),
    'search_queries': [
        'MN small business energy incentives',
        'Beltrami County economic development',
    ],
    'opportunities': [
        {
            'category': 'grant',
            'opportunity_type': 'Sample DEED program',
            'eligibility': 'MN businesses',
            'deadline': '2099-12-31',
            'summary': 'Placeholder opportunity for report preview.',
            'action_recommended': 'Run grantscout_run_agent with API credentials for real rows.',
            'source_url': 'https://mn.gov/deed/',
            'priority_score': 50,
            'source_url_check_passed': True,
        }
    ],
}


class Command(BaseCommand):
    help = (
        'Print or save a sample compiled GrantScout report plus loans/utilities/calendar markdown. '
        'Does not call the LLM.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '-o',
            '--output',
            default='',
            help='Write markdown to this path (default: print to stdout)',
        )

    def handle(self, *args, **options):
        body = build_compiled_report(_SAMPLE_PAYLOAD).strip()
        ops = build_operations_calendar_markdown()
        full = f'{body}\n\n{ops}'
        path = (options.get('output') or '').strip()
        if path:
            Path(path).write_text(full, encoding='utf-8')
            self.stdout.write(self.style.SUCCESS(f'Wrote {path} ({len(full)} characters)'))
        else:
            self.stdout.write(full)
