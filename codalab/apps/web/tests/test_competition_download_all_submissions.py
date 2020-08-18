import datetime

from django.core.urlresolvers import reverse
from django.test import TestCase
from django.contrib.auth import get_user_model

from apps.web.models import Competition, CompetitionPhase

User = get_user_model()


class CompetitionDownloadAllSubmissions(TestCase):

    def setUp(self):
        self.organizer_user = User.objects.create_user(username="organizer", password="pass")
        self.admin_user = User.objects.create_user(username="admin", password="pass")
        self.non_admin_user = User.objects.create_user(username="non_admin", password="pass")
        self.competition = Competition.objects.create(
            title="Test Competition",
            creator=self.organizer_user,
            modified_by=self.organizer_user,
            published=False,
        )
        self.competition.admins.add(self.admin_user)
        self.phase = CompetitionPhase.objects.create(competition=self.competition, phasenumber=1, start_date=datetime.datetime.now())

    def test_competition_download_all_submissions_returns_404_for_non_existant_competition(self):
        self.client.login(username="organizer", password="pass")
        resp = self.client.get(reverse("competitions:download_leaderboard_results", kwargs={"competition_pk": 0, "phase_pk": self.phase.pk}))
        self.assertEqual(resp.status_code, 404)

    def test_competition_download_all_submissions_returns_404_for_non_existant_phase(self):
        self.client.login(username="organizer", password="pass")
        resp = self.client.get(reverse("competitions:download_leaderboard_results", kwargs={"competition_pk": self.competition.pk, "phase_pk": 0}))
        self.assertEqual(resp.status_code, 404)

    def test_competition_download_all_submissions_returns_302_for_non_logged_in_user(self):
        resp = self.client.get(reverse("competitions:download_leaderboard_results", kwargs={"competition_pk": self.competition.pk, "phase_pk": self.phase.pk}))
        self.assertEqual(resp.status_code, 302)

    def test_competition_download_all_submissions_returns_200_on_success(self):
        self.client.login(username="organizer", password="pass")
        resp = self.client.get(reverse("competitions:download_leaderboard_results", kwargs={"competition_pk": self.competition.pk, "phase_pk": self.phase.pk}))
        self.assertEqual(resp.status_code, 200)
