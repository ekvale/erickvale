from datetime import date
from unittest.mock import patch

from django.test import SimpleTestCase, TestCase, override_settings

from mdh_briefings.agents import LEADERS, leader_by_id
from mdh_briefings.models import LeaderBriefing
from mdh_briefings.briefing_store import save_briefing
from mdh_briefings.bureaus import (
    digest_leader_ids_for_date,
    is_digest_weekday,
    spotlight_bureau_for_date,
)
from mdh_briefings.digest import (
    build_digest_context,
    get_digest_recipients,
    render_digest_html,
    run_daily_digest_send,
)


@override_settings(MDH_BRIEFINGS_DIGEST_RECIPIENTS='eric.kvale@state.mn.us')
class DigestRecipientTests(SimpleTestCase):
    def test_parse_recipients(self):
        self.assertEqual(get_digest_recipients(), ['eric.kvale@state.mn.us'])


class BureauSpotlightTests(SimpleTestCase):
    def test_weekday_rotation(self):
        mon = date(2026, 5, 18)  # Monday
        self.assertEqual(spotlight_bureau_for_date(mon)['slug'], 'health_operations')
        ids, bureau = digest_leader_ids_for_date(mon)
        self.assertIn('commissioner', ids)
        self.assertIn('ac_health_operations', ids)
        self.assertEqual(bureau['slug'], 'health_operations')

    def test_weekend_skip(self):
        sat = date(2026, 5, 23)
        self.assertFalse(is_digest_weekday(sat))
        self.assertIsNone(spotlight_bureau_for_date(sat))


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


class DigestTemplateTests(TestCase):
    def test_render_spotlight_digest(self):
        today = date(2026, 5, 20)  # Wednesday → health improvement
        leader = next(x for x in LEADERS if x['id'] == 'ac_health_improvement')
        comm = next(x for x in LEADERS if x['id'] == 'commissioner')
        briefing = LeaderBriefing.objects.create(
            leader_id=leader['id'],
            name=leader['name'],
            title=leader['title'],
            bureau=leader['bureau'],
            date=today,
            schedule=[],
            core_beliefs='',
            vision='',
            top_priorities=['Improvement priority'],
        )
        comm_b = LeaderBriefing.objects.create(
            leader_id=comm['id'],
            name=comm['name'],
            title=comm['title'],
            bureau=comm['bureau'],
            date=today,
            schedule=[],
            core_beliefs='',
            vision='',
            top_priorities=['Commissioner priority'],
        )
        bureau = spotlight_bureau_for_date(today)
        ctx = build_digest_context(
            today,
            briefings=[comm_b, briefing],
            news_items=[{'headline': 'Test', 'summary': 'S', 'why_it_matters': ''}],
            digest_leader_ids=['commissioner', 'ac_health_improvement'],
            spotlight_bureau=bureau,
        )
        subject, html = render_digest_html(today, ctx)
        self.assertIn('Health Improvement Bureau', subject)
        self.assertIn('Improvement priority', html)
        self.assertIn('Commissioner priority', html)

    def test_roster_has_bureaus_and_org_chart_roles(self):
        self.assertGreaterEqual(len(LEADERS), 28)
        ids = {x['id'] for x in LEADERS}
        self.assertIn('director_center_health_statistics', ids)
        self.assertIn('director_data_strategy_interop', ids)
        self.assertIn('facilities_manager', ids)
        self.assertEqual(leader_by_id('facilities_manager')['name'], 'Kevin Umidon')


@override_settings(MDH_BRIEFINGS_DIGEST_RECIPIENTS='eric.kvale@state.mn.us')
class DigestSendDryRunTests(TestCase):
    @patch('mdh_briefings.digest.ensure_briefings_for_date')
    @patch('mdh_briefings.services.fetch_daily_news_digest')
    def test_dry_run_weekday(self, mock_news, mock_ensure):
        today = date(2026, 5, 19)  # Tuesday
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
        result = run_daily_digest_send(dry_run=True, today=today)
        self.assertTrue(result['ok'])
        self.assertFalse(result.get('skipped'))

    def test_skip_weekend(self):
        result = run_daily_digest_send(dry_run=True, today=date(2026, 5, 24))  # Sunday
        self.assertTrue(result.get('skipped'))

