"""
Basic tests for All Minnesota app.
"""
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User


class AllminnesotaViewsTest(TestCase):
    """Smoke tests for login-required views."""

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.client = Client()

    def test_dashboard_requires_login(self):
        response = self.client.get(reverse('allminnesota:dashboard'))
        self.assertEqual(response.status_code, 302)

    def test_dashboard_ok_when_logged_in(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('allminnesota:dashboard'))
        self.assertEqual(response.status_code, 200)

    def test_contact_list_requires_login(self):
        response = self.client.get(reverse('allminnesota:contact_list'))
        self.assertEqual(response.status_code, 302)

    def test_task_board_ok_when_logged_in(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('allminnesota:task_board'))
        self.assertEqual(response.status_code, 200)
