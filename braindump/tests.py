from django.contrib.auth.models import User
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from braindump.models import CaptureItem, CaptureStatus


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

    def test_mark_done_archives(self):
        c = Client()
        c.login(username='owner1', password='pw')
        it = CaptureItem.objects.create(user=self.owner, body='x', title='Task')
        c.post(reverse('braindump:item_status', args=[it.pk]), {'status': 'done'})
        it.refresh_from_db()
        self.assertEqual(it.status, CaptureStatus.DONE)
        self.assertTrue(it.archived)
        self.assertIsNotNone(it.completed_at)
