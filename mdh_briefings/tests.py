from datetime import date
from unittest.mock import patch

from django.test import SimpleTestCase, TestCase, override_settings

from mdh_briefings.agents import LEADERS
from mdh_briefings.briefing_store import save_briefing
from mdh_briefings.digest import (
    build_digest_context,
    get_digest_recipients,
    render_digest_html,
    run_daily_digest_send,
)
from mdh_briefings.models import LeaderBriefing


@override_settings(MDH_BRIEFINGS_DIGEST_RECIPIENTS='eric.kvale@state.mn.us,other@example.com')
class DigestRecipientTests(SimpleTestCase):
    def test_parse_recipients(self):
        self.assertEqual(
            get_digest_recipients(),
            ['eric.kvale@state.mn.us', 'other@example.com'],
        )


class ExtendedBriefingTests(TestCase):
    def test_save_extended_fields(self):
        leader = next(x for x in LEADERS if x['id'] == 'senior_data_scientist_interop')
        today = date(2026, 5, 20)
        data = {
            'schedule': [],
            'core_beliefs': 'Beliefs',
            'vision': 'Vision',
            'top_priorities': ['P1'],
            'relevant_news': [{'headline': 'FHIR update', 'summary': 'Details'}],
            'high_value_projects': [
                {'title': 'MEDSS FHIR layer', 'impact': 'Faster outbreak response', 'next_step': 'Draft IG'},
            ],
        }
        b = save_briefing(leader, today, data)
        self.assertEqual(len(b.relevant_news), 1)
        self.assertEqual(b.high_value_projects[0]['title'], 'MEDSS FHIR layer')


class DigestTemplateTests(TestCase):
    def test_render_includes_leader_priorities(self):
        today = date(2026, 5, 19)
        leader = LEADERS[0]
        briefing = LeaderBriefing.objects.create(
            leader_id=leader['id'],
            name=leader['name'],
            title=leader['title'],
            bureau=leader['bureau'],
            date=today,
            schedule=[],
            core_beliefs='',
            vision='',
            top_priorities=['Priority A', 'Priority B'],
        )
        ctx = build_digest_context(
            today,
            briefings=[briefing],
            news_items=[{'headline': 'Test headline', 'summary': 'Summary', 'why_it_matters': 'Matters'}],
        )
        subject, html = render_digest_html(today, ctx)
        self.assertIn('MDH Leadership Daily', subject)
        self.assertIn('Priority A', html)
        self.assertIn('Test headline', html)
        self.assertIn(leader['name'], html)

    def test_roster_includes_key_roles(self):
        self.assertEqual(len(LEADERS), 20)
        ids = {x['id'] for x in LEADERS}
        self.assertIn('senior_data_scientist_interop', ids)
        self.assertIn('director_center_health_statistics', ids)


@override_settings(
    MDH_BRIEFINGS_DIGEST_RECIPIENTS='eric.kvale@state.mn.us',
    PERPLEXITY_API_KEY='',
)
class DigestSendDryRunTests(TestCase):
    @patch('mdh_briefings.digest.ensure_briefings_for_date')
    @patch('mdh_briefings.services.fetch_daily_news_digest')
    def test_dry_run(self, mock_news, mock_ensure):
        today = date(2026, 5, 19)
        leader = LEADERS[0]
        briefing = LeaderBriefing(
            leader_id=leader['id'],
            name=leader['name'],
            title=leader['title'],
            bureau=leader['bureau'],
            date=today,
            schedule=[],
            core_beliefs='',
            vision='',
            top_priorities=['One'],
        )
        mock_ensure.return_value = ([briefing], [])
        mock_news.return_value = []
        result = run_daily_digest_send(dry_run=True, today=today, include_news=True)
        self.assertTrue(result['ok'])
        self.assertIn('eric.kvale@state.mn.us', result['recipients'][0])
