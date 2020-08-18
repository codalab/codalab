import os

from django.core.urlresolvers import reverse
from django.test import TestCase
from django.contrib.auth import get_user_model

from apps.health.models import HealthSettings

User = get_user_model()


class HealthStatusSettingsTests(TestCase):
    def setUp(self):
        self.admin_user = User.objects.create_user(username="admin", password="pass")
        self.admin_user.is_staff = True
        self.admin_user.save()
        self.regular_user = User.objects.create_user(username="regular", password="pass")

    def test_health_email_settings_returns_404_for_logged_in_user(self):
        resp = self.client.post(reverse("health_status_email_settings"))
        self.assertEqual(resp.status_code, 302)

    def test_health_email_settings_returns_404_for_non_admin(self):
        self.client.login(username="regular", password="pass")
        resp = self.client.post(reverse("health_status_email_settings"))
        self.assertEqual(resp.status_code, 404)

    def test_health_email_settings_returns_200_for_admin(self):
        self.client.login(username="admin", password="pass")
        resp = self.client.post(reverse("health_status_email_settings"))
        self.assertEqual(resp.status_code, 200)

    def test_health_email_settings_actually_changes_environment_variable(self):
        self.client.login(username="admin", password="pass")
        emails = "test@test.com,test2@test.com"
        resp = self.client.post(reverse("health_status_email_settings"), {"emails": emails})
        self.assertEqual(HealthSettings.objects.get_or_create(pk=1)[0].emails, emails)
