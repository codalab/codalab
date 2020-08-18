import datetime

from django.core.urlresolvers import reverse
from django.test import TestCase
from django.contrib.auth import get_user_model

from apps.jobs import models as jobs_models

User = get_user_model()


class HealthStatusPageTests(TestCase):
    def setUp(self):
        self.admin_user = User.objects.create_user(username="admin", password="pass")
        self.admin_user.is_staff = True
        self.admin_user.save()
        self.regular_user = User.objects.create_user(username="regular", password="pass")

    def test_health_status_page_returns_404_for_logged_in_user(self):
        resp = self.client.get(reverse("health_status"))
        self.assertEqual(resp.status_code, 302)

    def test_health_status_page_returns_404_for_non_admin(self):
        self.client.login(username="regular", password="pass")
        resp = self.client.get(reverse("health_status"))
        self.assertEqual(resp.status_code, 404)

    def test_health_status_page_returns_200_for_admin(self):
        self.client.login(username="admin", password="pass")
        resp = self.client.get(reverse("health_status"))
        self.assertEqual(resp.status_code, 200)

    def test_health_status_page_context_contains_jobs_pending_and_count(self):
        self.client.login(username="admin", password="pass")
        job1 = jobs_models.Job.objects.create(status=jobs_models.Job.PENDING)
        job2 = jobs_models.Job.objects.create(status=jobs_models.Job.PENDING)
        resp = self.client.get(reverse("health_status"))

        self.assertIn(job1, resp.context["jobs_pending"])
        self.assertIn(job2, resp.context["jobs_pending"])
        self.assertEqual(resp.context["jobs_pending_count"], 2)

    def test_health_status_page_context_contains_average_job_time(self):
        self.client.login(username="admin", password="pass")
        one_min_ago = datetime.datetime.now() - datetime.timedelta(minutes=1)
        job1 = jobs_models.Job.objects.create(status=jobs_models.Job.FINISHED)
        job1.created = one_min_ago
        job1.save()
        job2 = jobs_models.Job.objects.create(status=jobs_models.Job.FINISHED)
        job2.created = one_min_ago
        job2.save()

        resp = self.client.get(reverse("health_status"))

        self.assertAlmostEqual(resp.context["jobs_finished_in_last_2_days_avg"], 60)

    def test_health_status_page_context_contains_jobs_lasting_longer_than_10_minutes(self):
        self.client.login(username="admin", password="pass")
        job1 = jobs_models.Job.objects.create(status=jobs_models.Job.PENDING)
        job1.created = datetime.datetime.now() - datetime.timedelta(minutes=1)
        job1.save()
        job2 = jobs_models.Job.objects.create(status=jobs_models.Job.PENDING)
        job2.created = datetime.datetime.now() - datetime.timedelta(minutes=15)
        job2.save()

        resp = self.client.get(reverse("health_status"))

        self.assertEqual(resp.context["jobs_lasting_longer_than_10_minutes"][0].pk, job2.pk)
        self.assertEqual(len(resp.context["jobs_lasting_longer_than_10_minutes"]), 1)

    def test_health_status_page_context_contains_jobs_that_failed(self):
        self.client.login(username="admin", password="pass")
        job1 = jobs_models.Job.objects.create(status=jobs_models.Job.FAILED)
        job2 = jobs_models.Job.objects.create(status=jobs_models.Job.FAILED)
        resp = self.client.get(reverse("health_status"))

        self.assertIn(job1, resp.context["jobs_failed"])
        self.assertIn(job2, resp.context["jobs_failed"])
        self.assertEqual(resp.context["jobs_failed_count"], 2)
