from unittest.mock import MagicMock, patch

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, override_settings

from dream_blue.emailing import (
    DreamBlueEmailConfigError,
    get_digest_recipients,
    parse_recipient_list,
    send_html_digest,
)
from dream_blue.models import (
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
