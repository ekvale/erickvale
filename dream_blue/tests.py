from datetime import date
from unittest.mock import MagicMock, patch

from django.contrib.auth.models import User
from io import StringIO

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from dream_blue.emailing import (
    DreamBlueEmailConfigError,
    get_digest_recipients,
    parse_recipient_list,
    send_html_digest,
)
from dream_blue.models import (
    BusinessCalendarEvent,
    BusinessCalendarEventType,
    BusinessKPIEntry,
    GrantScoutCategory,
    GrantScoutOpportunity,
    GrantScoutRun,
    GrantScoutRunStatus,
)


class RecipientParsingTests(TestCase):
    def test_parse_empty(self):
        self.assertEqual(parse_recipient_list(''), [])
        self.assertEqual(parse_recipient_list('   '), [])

    def test_parse_commas(self):
        self.assertEqual(
            parse_recipient_list(' a@b.com , c@d.org '),
            ['a@b.com', 'c@d.org'],
        )


@override_settings(DREAM_BLUE_REPORT_RECIPIENTS='x@example.com,y@example.com')
class GetDigestRecipientsTests(TestCase):
    def test_get_digest_recipients(self):
        self.assertEqual(
            get_digest_recipients(),
            ['x@example.com', 'y@example.com'],
        )


@override_settings(
    DREAM_BLUE_REPORT_RECIPIENTS='ops@example.com',
    RESEND_API_KEY='re_key',
    RESEND_FROM_EMAIL='from@example.com',
)
class ResendSendTests(TestCase):
    @patch('dream_blue.emailing.requests.post')
    def test_send_uses_resend(self, mock_post):
        mock_post.return_value = MagicMock(status_code=200, text='ok')
        send_html_digest('Subj', '<p>hi</p>')
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        self.assertIn('resend.com', args[0])
        self.assertEqual(kwargs['json']['subject'], 'Subj')


@override_settings(
    DREAM_BLUE_REPORT_RECIPIENTS='ops@example.com',
    RESEND_API_KEY='',
    RESEND_FROM_EMAIL='',
    EMAIL_HOST='smtp.example.com',
    DEFAULT_FROM_EMAIL='from@example.com',
)
class SmtpSendTests(TestCase):
    @patch('dream_blue.emailing.EmailMultiAlternatives.send')
    def test_send_uses_django_mail(self, mock_send):
        send_html_digest('Subj', '<p>hi</p>')
        mock_send.assert_called_once()


class SendDigestCommandTests(TestCase):
    @override_settings(DREAM_BLUE_REPORT_RECIPIENTS='')
    def test_command_errors_without_recipients(self):
        with self.assertRaises(CommandError):
            call_command('dream_blue_send_digest')

    @override_settings(DREAM_BLUE_REPORT_RECIPIENTS='a@example.com')
    def test_dry_run(self):
        call_command('dream_blue_send_digest', '--dry-run')


class DreamBlueOpsDbCheckCommandTests(TestCase):
    def test_check_ops_db_reports_ok(self):
        out = StringIO()
        call_command('dream_blue_check_ops_db', stdout=out)
        text = out.getvalue()
        self.assertIn('0004_business_calendar_kpi_report_sections', text)
        self.assertIn('Operations tables are present.', text)


class DigestContextTests(TestCase):
    def test_latest_completed_run_in_context(self):
        draft = GrantScoutRun.objects.create(
            period_label='2099-01',
            status=GrantScoutRunStatus.DRAFT,
        )
        done = GrantScoutRun.objects.create(
            period_label='2099-02',
            status=GrantScoutRunStatus.COMPLETED,
            coverage_summary='MN focus',
        )
        GrantScoutOpportunity.objects.create(
            run=done,
            category=GrantScoutCategory.GRANT,
            summary='Test opportunity',
            source_url='https://example.org/grant',
            priority_score=10,
        )
        from dream_blue.digest_context import build_monthly_digest_context

        ctx = build_monthly_digest_context()
        self.assertEqual(ctx['grantscout_run'].id, done.id)
        self.assertNotEqual(ctx['grantscout_run'].id, draft.id)
        self.assertEqual(len(ctx['grantscout_opportunities']), 1)
        self.assertEqual(ctx['grantscout_opportunities_unverified'], [])

    def test_operations_calendar_and_kpis_in_context(self):
        from django.utils import timezone

        from dream_blue.digest_context import build_monthly_digest_context

        d0 = timezone.localdate()
        BusinessCalendarEvent.objects.create(
            title='Property tax installment',
            event_type=BusinessCalendarEventType.PROPERTY_TAX,
            due_date=d0,
            property_label='Main st',
        )
        BusinessKPIEntry.objects.create(
            label='Occupancy',
            value_display='94%',
            period_hint='as of today',
        )
        BusinessCalendarEvent.objects.create(
            title='Year-end note',
            event_type=BusinessCalendarEventType.LOAN,
            due_date=date(d0.year, 1, 5),
            end_date=date(d0.year, 12, 15),
            property_label='HQ',
        )
        ctx = build_monthly_digest_context(include_grantscout=False)
        tax_events = [
            e for e in ctx['business_calendar_events'] if e.title == 'Property tax installment'
        ]
        self.assertEqual(len(tax_events), 1)
        self.assertGreaterEqual(len(ctx['business_calendar_events']), 1)
        ycal = ctx['email_calendar_year']
        self.assertEqual(ycal['year'], d0.year)
        self.assertEqual(len(ycal['months']), 12)
        mo = ycal['months'][d0.month - 1]
        self.assertEqual(mo['month'], d0.month)
        found_tax_chip = False
        for week in mo['weeks']:
            for cell in week:
                if cell.get('day') == d0.day and not cell.get('out_of_month'):
                    for chip in cell.get('chips', []):
                        if 'Property tax' in chip.get('text', ''):
                            found_tax_chip = True
        self.assertTrue(found_tax_chip, 'year grid should include property tax on due date')
        dec = ycal['months'][11]
        found_loan_end = False
        for week in dec['weeks']:
            for cell in week:
                if cell.get('day') == 15 and not cell.get('out_of_month'):
                    for chip in cell.get('chips', []):
                        if 'Ends' in chip.get('text', '') and 'Year-end note' in chip.get(
                            'text', ''
                        ):
                            found_loan_end = True
        self.assertTrue(found_loan_end, 'December should show loan maturity chip')
        occ = [k for k in ctx['business_kpis'] if k.label == 'Occupancy']
        self.assertEqual(len(occ), 1)
        self.assertTrue(
            BusinessCalendarEvent.objects.filter(
                event_type=BusinessCalendarEventType.LEASE,
                property_label='211 4th St.',
            ).exists()
        )
        self.assertIn('calendar_window_end', ctx)


class OperationsCalendarApiTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.staff = User.objects.create_user(
            username='staff_cal',
            password='pw',
            is_staff=True,
        )
        self.user = User.objects.create_user(
            username='user_cal',
            password='pw',
            is_staff=False,
        )

    def test_calendar_page_staff(self):
        self.client.login(username='staff_cal', password='pw')
        r = self.client.get(reverse('dream_blue:operations_calendar'))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'Operations calendar')

    def test_calendar_events_api_requires_staff(self):
        self.client.login(username='user_cal', password='pw')
        r = self.client.get(
            reverse('dream_blue:operations_calendar_events_api'),
            {'start': '2026-01-01', 'end': '2026-02-01'},
        )
        self.assertEqual(r.status_code, 403)

    def test_calendar_events_api_returns_json(self):
        self.client.login(username='staff_cal', password='pw')
        r = self.client.get(
            reverse('dream_blue:operations_calendar_events_api'),
            {'start': '2026-01-01', 'end': '2026-02-01'},
        )
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertIn('events', data)
        self.assertIsInstance(data['events'], list)

    def test_expense_summary_api(self):
        self.client.login(username='staff_cal', password='pw')
        r = self.client.get(reverse('dream_blue:operations_expense_summary_api'))
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertIn('amountByType', data)
        self.assertIn('countByType', data)


class GrantScoutHttpTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.staff = User.objects.create_user(
            username='staff_gs',
            password='pw',
            is_staff=True,
        )
        self.user = User.objects.create_user(
            username='regular_gs',
            password='pw',
            is_staff=False,
        )

    def test_dashboard_redirects_anonymous(self):
        url = reverse('dream_blue:grantscout_dashboard')
        r = self.client.get(url)
        self.assertEqual(r.status_code, 302)
        self.assertIn('/login/', r.url)

    def test_dashboard_forbidden_non_staff(self):
        self.client.login(username='regular_gs', password='pw')
        r = self.client.get(reverse('dream_blue:grantscout_dashboard'))
        self.assertEqual(r.status_code, 403)

    def test_dashboard_ok_staff(self):
        GrantScoutRun.objects.create(
            period_label='2099-03',
            status=GrantScoutRunStatus.COMPLETED,
        )
        self.client.login(username='staff_gs', password='pw')
        r = self.client.get(reverse('dream_blue:grantscout_dashboard'))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'GrantScout')
        self.assertContains(r, '2099-03')

    def test_latest_api_json_staff(self):
        run = GrantScoutRun.objects.create(
            period_label='2099-04',
            status=GrantScoutRunStatus.COMPLETED,
            coverage_summary='API test',
        )
        GrantScoutOpportunity.objects.create(
            run=run,
            category=GrantScoutCategory.REBATE,
            summary='Heat pump rebate',
            source_url='https://example.org/rebate',
            priority_score=99,
        )
        self.client.login(username='staff_gs', password='pw')
        r = self.client.get(reverse('dream_blue:grantscout_latest_api'))
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertEqual(data['run']['period_label'], '2099-04')
        self.assertEqual(len(data['opportunities']), 1)
        self.assertEqual(data['opportunities'][0]['priority_score'], 99)
        self.assertIn('opportunities_unverified', data)
        self.assertEqual(data['opportunities_unverified'], [])


class DigestCommandSendTests(TestCase):
    """Full command path: template render + Django mail backend (no network)."""

    @override_settings(
        DREAM_BLUE_REPORT_RECIPIENTS='digest@example.com',
        RESEND_API_KEY='',
        RESEND_FROM_EMAIL='',
        EMAIL_HOST='localhost',
        DEFAULT_FROM_EMAIL='from@example.com',
        EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
    )
    def test_send_digest_creates_locmem_message(self):
        from django.core import mail

        mail.outbox.clear()
        call_command('dream_blue_send_digest', '--no-grantscout')
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('Dream Blue report', mail.outbox[0].subject)
        self.assertIn('text/html', mail.outbox[0].alternatives[0][1])


class GrantScoutReportBuilderTests(TestCase):
    def test_compiled_report_contains_sections(self):
        from dream_blue.grantscout_reports import build_compiled_report

        text = build_compiled_report(
            {
                'coverage_summary': 'MN focus.',
                'search_queries': ['deed grants'],
                'opportunities': [
                    {
                        'category': 'grant',
                        'opportunity_type': 'Demo',
                        'eligibility': 'SMB',
                        'deadline': '2099-01-01',
                        'summary': 'Do a thing',
                        'action_recommended': 'Apply',
                        'source_url': 'https://example.org/x',
                        'priority_score': 50,
                        'dedupe_key': 'x',
                    }
                ],
            }
        )
        self.assertIn('GrantScout run report', text)
        self.assertIn('MN focus.', text)
        self.assertIn('deed grants', text)
        self.assertIn('https://example.org/x', text)

    def test_compiled_report_lists_unverified_links_at_bottom(self):
        from dream_blue.grantscout_reports import build_compiled_report

        text = build_compiled_report(
            {
                'coverage_summary': 'MN.',
                'search_queries': [],
                'opportunities': [
                    {
                        'category': 'grant',
                        'summary': 'Good link',
                        'source_url': 'https://example.org/ok',
                        'priority_score': 10,
                        'dedupe_key': 'a',
                        'source_url_check_passed': True,
                    },
                    {
                        'category': 'grant',
                        'summary': 'Maybe moved',
                        'source_url': 'https://example.org/maybe404',
                        'priority_score': 5,
                        'dedupe_key': 'b',
                        'source_url_check_passed': False,
                    },
                ],
            }
        )
        self.assertIn('Links that failed automated verification', text)
        self.assertIn('https://example.org/maybe404', text)
        self.assertIn('Good link', text)


class GrantScoutAgentNormalizationTests(TestCase):
    @override_settings(GRANTSCOUT_VALIDATE_SOURCE_URLS=False)
    def test_normalize_payload(self):
        from dream_blue.grantscout_agent import normalize_agent_payload

        data = normalize_agent_payload(
            {
                'coverage_summary': 'Test coverage',
                'search_queries': ['mn grants'],
                'opportunities': [
                    {
                        'category': 'grant',
                        'opportunity_type': 'Demo',
                        'eligibility': 'Small biz',
                        'deadline': '2099-12-31',
                        'summary': 'Summary text',
                        'action_recommended': 'Apply',
                        'source_url': 'https://example.org/program',
                        'priority_score': 50,
                    }
                ],
            }
        )
        self.assertEqual(len(data['opportunities']), 1)
        self.assertEqual(len(data['opportunities'][0]['dedupe_key']), 64)

    def test_normalize_rejects_when_no_valid_urls(self):
        from dream_blue.grantscout_agent import GrantScoutAgentError, normalize_agent_payload

        with self.assertRaises(GrantScoutAgentError):
            normalize_agent_payload(
                {
                    'coverage_summary': 'x',
                    'search_queries': [],
                    'opportunities': [
                        {'summary': 'bad', 'source_url': 'http://insecure.example/'},
                    ],
                }
            )


class GrantScoutUrlBodyHeuristicTests(TestCase):
    def test_commerce_style_moved_page(self):
        from dream_blue.url_check import url_body_suggests_page_moved

        html = """
        Minnesota Department of Commerce logo
        Menu help: you can navigate through the menu using your arrow keys
        The page you are looking for has moved!
        We have a new website. Please update your bookmarks.
        You can either search for the page or go to the homepage.
        """
        self.assertTrue(url_body_suggests_page_moved(html))

    def test_normal_page_not_flagged(self):
        from dream_blue.url_check import url_body_suggests_page_moved

        html = (
            '<html><body><h1>Rural Energy for America Program</h1>'
            '<p>Apply for grants supporting renewable energy.</p></body></html>'
        )
        self.assertFalse(url_body_suggests_page_moved(html))

    def test_short_snippet_not_flagged(self):
        from dream_blue.url_check import url_body_suggests_page_moved

        self.assertFalse(url_body_suggests_page_moved('moved'))

    def test_soft404_style_page(self):
        from dream_blue.url_check import url_body_suggests_page_moved

        html = """<!DOCTYPE html><html><body>
        <h1>Page Not Found.</h1>
        <p>Error 404.</p>
        <p>Sorry, this page is not available.</p>
        </body></html>"""
        self.assertTrue(url_body_suggests_page_moved(html))

    @patch('dream_blue.url_check.requests.get')
    def test_http_200_placeholder_counts_as_unreachable(self, mock_get):
        from dream_blue.url_check import source_url_is_reachable

        body = (
            b'<!DOCTYPE html><html><body><p>The page you are looking for has moved!</p>'
            b'<p>Please update your bookmarks.</p></body></html>'
        )
        resp = MagicMock()
        resp.status_code = 200
        resp.iter_content.side_effect = lambda **kwargs: [body]
        ctx = MagicMock()
        ctx.__enter__.return_value = resp
        ctx.__exit__.return_value = False
        mock_get.return_value = ctx

        self.assertFalse(source_url_is_reachable('https://commerce.state.mn.us/old'))


class GrantScoutUrlValidationTests(TestCase):
    @patch('dream_blue.grantscout_agent.source_url_is_reachable')
    def test_keeps_unreachable_urls_flagged(self, mock_reach):
        mock_reach.return_value = False
        from dream_blue.grantscout_agent import normalize_agent_payload

        data = normalize_agent_payload(
            {
                'coverage_summary': 'x',
                'search_queries': [],
                'opportunities': [
                    {
                        'category': 'grant',
                        'summary': 'Test',
                        'source_url': 'https://example.org/dead',
                        'priority_score': 1,
                    }
                ],
            },
            validate_urls=True,
        )
        self.assertEqual(len(data['opportunities']), 1)
        self.assertIs(data['opportunities'][0]['source_url_check_passed'], False)

    @patch('dream_blue.grantscout_agent.source_url_is_reachable')
    def test_keeps_when_reachable(self, mock_reach):
        mock_reach.return_value = True
        from dream_blue.grantscout_agent import normalize_agent_payload

        data = normalize_agent_payload(
            {
                'coverage_summary': 'x',
                'search_queries': [],
                'opportunities': [
                    {
                        'category': 'grant',
                        'summary': 'Test',
                        'source_url': 'https://example.org/ok',
                        'priority_score': 1,
                    }
                ],
            },
            validate_urls=True,
        )
        self.assertEqual(len(data['opportunities']), 1)
        self.assertIs(data['opportunities'][0]['source_url_check_passed'], True)


class GrantScoutRunAgentCommandTests(TestCase):
    @patch('dream_blue.management.commands.grantscout_run_agent.run_grantscout_agent')
    def test_command_creates_completed_run(self, mock_agent):
        mock_agent.return_value = {
            'coverage_summary': 'Cov',
            'search_queries': ['a'],
            'opportunities': [
                {
                    'category': GrantScoutCategory.GRANT,
                    'opportunity_type': 't',
                    'eligibility': 'e',
                    'deadline': None,
                    'summary': 'S',
                    'action_recommended': 'Act',
                    'source_url': 'https://example.gov/x',
                    'priority_score': 10,
                    'dedupe_key': 'a' * 64,
                }
            ],
        }
        call_command('grantscout_run_agent', '--period=2099-05', '--no-drift')
        run = GrantScoutRun.objects.get(period_label='2099-05')
        self.assertEqual(run.status, GrantScoutRunStatus.COMPLETED)
        self.assertEqual(run.opportunities.count(), 1)
        self.assertIn('GrantScout run report', run.compiled_report)
        self.assertEqual(len(run.agent_snapshot.get('opportunities', [])), 1)
