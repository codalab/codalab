import mock
import datetime

from django.conf import settings
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model

from apps.web import models


User = get_user_model()


class CompetitionDownloadTests(TestCase):
    def setUp(self):
        super(CompetitionDownloadTests, self).setUp()

        self.user = User.objects.create_user(username="organizer", password="pass")
        self.other_user = User.objects.create_user(username="potentially_malicious", password="pass")
        self.competition = models.Competition.objects.create(creator=self.user, modified_by=self.user)

    def test_competition_download_returns_status_302_for_non_logged_in_user(self):
        resp = self.client.get(reverse("competitions:download", kwargs={"competition_pk": self.competition.pk}))
        self.assertEqual(resp.status_code, 302)

    def test_competition_download_returns_status_403_for_non_admin(self):
        self.client.login(username="organizer", password="pass")
        resp = self.client.get(reverse("competitions:download", kwargs={"competition_pk": self.competition.pk}))
        self.assertEqual(resp.status_code, 403)
