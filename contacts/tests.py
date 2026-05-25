from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from .import_parsers import parse_linkedin_csv
from .import_service import import_parsed_rows
from .models import Contact, ContactSource

User = get_user_model()


class ContactsAppTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='eric', password='pw')
        self.client = Client()
        self.client.login(username='eric', password='pw')

    def test_list_requires_login(self):
        Client().get(reverse('contacts:list'))
        self.assertEqual(Client().get(reverse('contacts:list')).status_code, 302)

    def test_create_and_list_contact(self):
        Contact.objects.create(
            first_name='Ada',
            last_name='Lovelace',
            email='ada@example.com',
            source=ContactSource.MANUAL,
        )
        r = self.client.get(reverse('contacts:list'))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'Ada')

    def test_linkedin_csv_import_dedupes_email(self):
        csv_body = (
            'First Name,Last Name,Email Address,Company,Position,Connected On\n'
            'Jane,Doe,jane@example.com,Acme,Director,01 Jan 2024\n'
        )
        rows = parse_linkedin_csv(csv_body)
        self.assertEqual(len(rows), 1)
        r1 = import_parsed_rows(rows)
        self.assertEqual(r1.added, 1)
        r2 = import_parsed_rows(rows)
        self.assertEqual(r2.added, 0)
        self.assertEqual(r2.skipped_existing, 1)

    def test_file_import_view(self):
        csv_body = (
            'First Name,Last Name,Email Address,Company,Position,Connected On\n'
            'Bob,Smith,bob@example.com,Org,Lead,01 Jan 2024\n'
        )
        upload = SimpleUploadedFile(
            'contacts.csv',
            csv_body.encode('utf-8'),
            content_type='text/csv',
        )
        r = self.client.post(
            reverse('contacts:import_file'),
            {'file': upload},
        )
        self.assertEqual(r.status_code, 302)
        self.assertTrue(Contact.objects.filter(email='bob@example.com').exists())
