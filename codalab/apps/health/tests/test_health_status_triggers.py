import datetime
import mock

from django.core import mail
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.contrib.auth import get_user_model

from apps.health.models import HealthSettings

User = get_user_model()


class HealthStatusTriggerTests(TestCase):
    def setUp(self):
        self.health_settings = HealthSettings.objects.get_or_create(pk=1)[0]
        self.health_settings.emails = "test@test.com, test2@test.com"
        self.health_settings.save()

    def test_health_status_triggers_when_jobs_in_queue_greater_than_25(self):
        with mock.patch('apps.health.views.get_health_metrics') as get_health_metrics_mock:
            get_health_metrics_mock.return_value = {
                "jobs_pending_count": 510,
                "jobs_lasting_longer_than_10_minutes": [_ for _ in range(0, 5)],
                "alert_emails": self.health_settings.emails,
            }

            self.client.get(reverse("health_status_check_thresholds"))

            self.assertEqual(len(mail.outbox), 1)
            self.assertIn("test@test.com", mail.outbox[0].recipients())
            self.assertIn("test2@test.com", mail.outbox[0].recipients())
            self.assertEqual(mail.outbox[0].subject, "Codalab Warning: Jobs pending > 25!")

    def test_health_status_triggers_when_a_job_takes_greater_than_10_minutes_to_process(self):
        with mock.patch('apps.health.views.get_health_metrics') as get_health_metrics_mock:
            get_health_metrics_mock.return_value = {
                "jobs_pending_count": 5,
                "jobs_lasting_longer_than_10_minutes": [_ for _ in range(0, 15)],
                "alert_emails": self.health_settings.emails,
            }

            self.client.get(reverse("health_status_check_thresholds"))

            self.assertEqual(len(mail.outbox), 1)
            self.assertIn("test@test.com", mail.outbox[0].recipients())
            self.assertIn("test2@test.com", mail.outbox[0].recipients())
            self.assertEqual(mail.outbox[0].subject, "Codalab Warning: Many jobs taking > 10 minutes!")

    def test_health_status_trigger_emails_without_commas_works(self):
        self.health_settings.emails = "test_only_one@test.com"
        self.health_settings.save()

        with mock.patch('apps.health.views.get_health_metrics') as get_health_metrics_mock:
            get_health_metrics_mock.return_value = {
                "jobs_pending_count": 510,
                "jobs_lasting_longer_than_10_minutes": None,
                "alert_emails": self.health_settings.emails,
            }

            self.client.get(reverse("health_status_check_thresholds"))

            self.assertEqual(len(mail.outbox), 1)
            self.assertIn("test_only_one@test.com", mail.outbox[0].recipients())
