from datetime import date
from unittest.mock import patch

from django.contrib.auth.models import User
from django.http import QueryDict
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from braindump.dashboard_filters import apply_dashboard_filters, filter_query_has_params
from braindump.gtd_partition import partition_active_items
from braindump.morning_digest import run_morning_digest_send
from braindump.recurrence_logic import advance_after_spawn, last_weekday_of_month
from braindump.work_category import (
    CATEGORY_DREAM_BLUE,
    CATEGORY_MDH,
    CATEGORY_SIOUX_CHEF,
    canonical_work_stream_label,
    resolve_work_category,
    work_category_from_body,
)
from braindump.models import (
    CaptureItem,
    CaptureStatus,
    GTDBucket,
    NonActionableDisposition,
    TaskPriority,
)


@override_settings(
    BRAINDUMP_OWNER_USERNAME='owner1',
    BRAINDUMP_OWNER_USER_ID='',
)
class BraindumpOwnerTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user('owner1', password='pw')
        self.other = User.objects.create_user('other', password='pw')

    def test_non_owner_forbidden(self):
        c = Client()
        c.login(username='other', password='pw')
        r = c.get(reverse('braindump:dashboard'))
        self.assertEqual(r.status_code, 403)

    def test_non_owner_morning_digest_forbidden(self):
        c = Client()
        c.login(username='other', password='pw')
        r = c.post(reverse('braindump:morning_digest_send_now'))
        self.assertEqual(r.status_code, 403)

    @patch('braindump.views.run_morning_digest_send')
    def test_morning_digest_send_now(self, mock_run):
        mock_run.return_value = {'ok': True, 'message': 'Sent test digest.'}
        c = Client()
        c.login(username='owner1', password='pw')
        r = c.post(reverse('braindump:morning_digest_send_now'))
        self.assertEqual(r.status_code, 302)
        mock_run.assert_called_once_with()

    def test_capture_and_list(self):
        c = Client()
        c.login(username='owner1', password='pw')
        r = c.post(
            reverse('braindump:capture_create'),
            {'body': 'Buy milk tomorrow'},
        )
        self.assertEqual(r.status_code, 302)
        self.assertEqual(CaptureItem.objects.filter(user=self.owner).count(), 1)
        it = CaptureItem.objects.get()
        self.assertTrue(it.title or it.body)
        r2 = c.get(reverse('braindump:dashboard'))
        self.assertEqual(r2.status_code, 200)
        self.assertContains(r2, 'Buy milk')

    def test_capture_splits_on_semicolon(self):
        c = Client()
        c.login(username='owner1', password='pw')
        r = c.post(
            reverse('braindump:capture_create'),
            {'body': 'Buy tickets; do laundry;  ; empty fridge'},
        )
        self.assertEqual(r.status_code, 302)
        qs = CaptureItem.objects.filter(user=self.owner).order_by('pk')
        self.assertEqual(qs.count(), 3)
        self.assertEqual(
            list(qs.values_list('body', flat=True)),
            ['Buy tickets', 'do laundry', 'empty fridge'],
        )

    def test_mark_done_archives(self):
        c = Client()
        c.login(username='owner1', password='pw')
        it = CaptureItem.objects.create(user=self.owner, body='x', title='Task')
        c.post(reverse('braindump:item_status', args=[it.pk]), {'status': 'done'})
        it.refresh_from_db()
        self.assertEqual(it.status, CaptureStatus.DONE)
        self.assertTrue(it.archived)
        self.assertIsNotNone(it.completed_at)

    def test_item_archive(self):
        c = Client()
        c.login(username='owner1', password='pw')
        it = CaptureItem.objects.create(user=self.owner, body='noise', title='t')
        c.post(reverse('braindump:item_archive', args=[it.pk]), {})
        it.refresh_from_db()
        self.assertTrue(it.archived)

    def test_item_update_meta(self):
        c = Client()
        c.login(username='owner1', password='pw')
        it = CaptureItem.objects.create(
            user=self.owner,
            body='x',
            title='t',
            category_label='Old',
            priority=TaskPriority.NORMAL,
        )
        c.post(
            reverse('braindump:item_update_meta', args=[it.pk]),
            {'category_label': 'Health', 'priority': TaskPriority.URGENT},
        )
        it.refresh_from_db()
        self.assertEqual(it.category_label, 'Health')
        self.assertEqual(it.priority, TaskPriority.URGENT)

    def test_dashboard_gtd_sections(self):
        c = Client()
        c.login(username='owner1', password='pw')
        CaptureItem.objects.create(
            user=self.owner,
            body='clarify me',
            title='u',
            is_actionable=None,
        )
        r = c.get(reverse('braindump:dashboard'))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'Clarify queue')

    def test_dashboard_filter_by_person(self):
        c = Client()
        c.login(username='owner1', password='pw')
        CaptureItem.objects.create(user=self.owner, body='x', title='Call Alice soon')
        CaptureItem.objects.create(user=self.owner, body='y', title='Other task')
        r = c.get(reverse('braindump:dashboard'), {'person': 'Alice'})
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'Call Alice')
        self.assertNotContains(r, 'Other task')

    def test_dashboard_reset_clears_session_filters(self):
        c = Client()
        c.login(username='owner1', password='pw')
        c.get(reverse('braindump:dashboard'), {'person': 'Zoe'})
        self.assertEqual(c.session.get('braindump_filter_query'), 'person=Zoe')
        r = c.get(reverse('braindump:dashboard'), {'__reset': '1'})
        self.assertEqual(r.status_code, 302)
        self.assertNotIn('person=', r['Location'])
        self.assertNotIn('braindump_filter_query', c.session)

    def test_post_redirect_preserves_session_filters(self):
        c = Client()
        c.login(username='owner1', password='pw')
        s = c.session
        s['braindump_filter_query'] = 'person=Pat'
        s.save()
        it = CaptureItem.objects.create(user=self.owner, body='b', title='t')
        r = c.post(reverse('braindump:item_status', args=[it.pk]), {'status': 'done'})
        self.assertEqual(r.status_code, 302)
        self.assertIn('person=Pat', r['Location'])


class DashboardFiltersUnitTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user('fu', password='pw')

    def test_filter_work_type_and_gtd_bucket(self):
        a = CaptureItem.objects.create(
            user=self.owner,
            body='a',
            category_label=CATEGORY_MDH,
            gtd_bucket=GTDBucket.NEXT_ACTION,
            is_actionable=True,
        )
        CaptureItem.objects.create(
            user=self.owner,
            body='b',
            category_label=CATEGORY_DREAM_BLUE,
            gtd_bucket=GTDBucket.PROJECT,
            is_actionable=True,
            is_project=True,
        )
        qs = CaptureItem.objects.filter(user=self.owner)
        q1 = apply_dashboard_filters(qs, QueryDict(f'work_type={CATEGORY_MDH}'))
        self.assertEqual(list(q1), [a])
        q2 = apply_dashboard_filters(qs, QueryDict(f'gtd_bucket={GTDBucket.PROJECT.value}'))
        self.assertEqual(q2.count(), 1)

    def test_filter_query_has_params(self):
        self.assertTrue(filter_query_has_params(QueryDict('person=x')))
        self.assertFalse(filter_query_has_params(QueryDict('__reset=1')))


@override_settings(
    BRAINDUMP_OWNER_USERNAME='owner1',
    BRAINDUMP_OWNER_USER_ID='',
)
class MorningDigestTests(TestCase):
    def setUp(self):
        User.objects.create_user('owner1', password='pw')

    def test_morning_digest_dry_run(self):
        r = run_morning_digest_send(dry_run=True)
        self.assertTrue(r['ok'])
        self.assertIn('Dry run', r['message'])


class RecurrenceLogicTests(TestCase):
    def test_last_monday_jan_2026(self):
        d = last_weekday_of_month(2026, 1, 0)
        self.assertEqual(d.weekday(), 0)
        self.assertEqual(d.month, 1)
        self.assertEqual(d.day, 26)

    def test_advance_weekly(self):
        d = date(2026, 4, 6)
        nxt = advance_after_spawn('weekly', d, weekday=0)
        self.assertEqual(nxt, date(2026, 4, 13))


class WorkCategoryRulesTests(TestCase):
    def test_default_mdh(self):
        self.assertEqual(work_category_from_body('Buy toner'), CATEGORY_MDH)

    def test_mdh_names(self):
        self.assertEqual(work_category_from_body('Email Abby about report'), CATEGORY_MDH)
        self.assertEqual(work_category_from_body('Call Tim'), CATEGORY_MDH)

    def test_dream_blue_wendy(self):
        self.assertEqual(work_category_from_body('Talk to Wendy about lease'), CATEGORY_DREAM_BLUE)

    def test_dream_blue_property(self):
        self.assertEqual(work_category_from_body('Fix vacancy in unit 3'), CATEGORY_DREAM_BLUE)

    def test_sioux_chef_priority_over_dream_blue_terms(self):
        self.assertEqual(
            work_category_from_body('NOMOAR launch and property page'),
            CATEGORY_SIOUX_CHEF,
        )

    def test_sioux_chef_sean(self):
        self.assertEqual(work_category_from_body('Sean feedback on menu'), CATEGORY_SIOUX_CHEF)

    def test_sioux_chef_phrase(self):
        self.assertEqual(work_category_from_body('Sioux Chef catering order'), CATEGORY_SIOUX_CHEF)


class ResolveWorkCategoryTests(TestCase):
    def test_ai_upgrades_default_mdh_to_dream_blue(self):
        self.assertEqual(
            resolve_work_category('Buy toner for office', 'Dream Blue'),
            CATEGORY_DREAM_BLUE,
        )

    def test_keyword_sioux_beats_ai_mdh(self):
        self.assertEqual(
            resolve_work_category('NOMOAR launch checklist', 'MDH'),
            CATEGORY_SIOUX_CHEF,
        )

    def test_canonical_stream_labels(self):
        self.assertEqual(canonical_work_stream_label('  Sioux Chef '), CATEGORY_SIOUX_CHEF)
        self.assertEqual(canonical_work_stream_label('dream-blue'), CATEGORY_DREAM_BLUE)
        self.assertIsNone(canonical_work_stream_label('Side project'))


class GtdPartitionTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user('part', password='pw')

    def test_partition_unclear_trash_calendar_next(self):
        u = self.owner
        unclear = CaptureItem(user=u, body='a', is_actionable=None)
        trash = CaptureItem(
            user=u,
            body='b',
            is_actionable=False,
            non_actionable_disposition=NonActionableDisposition.TRASH,
        )
        cal = CaptureItem(
            user=u,
            body='c',
            is_actionable=True,
            calendar_date=date(2026, 6, 15),
            calendar_is_hard_date=True,
        )
        nxt = CaptureItem(user=u, body='d', is_actionable=True, title='n')
        parts = partition_active_items([unclear, trash, cal, nxt])
        self.assertEqual(parts['unclear'], [unclear])
        self.assertEqual(parts['trash_list'], [trash])
        self.assertEqual(parts['calendar_hard'], [cal])
        self.assertEqual(parts['next_actions'], [nxt])
