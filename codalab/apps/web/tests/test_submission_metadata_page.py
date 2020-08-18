import datetime
import mock

from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test.client import Client
from django.contrib.auth import get_user_model

from apps.web.models import (Competition,
                             CompetitionParticipant,
                             CompetitionPhase,
                             CompetitionSubmission,
                             CompetitionSubmissionStatus,
                             ParticipantStatus,
                             PhaseLeaderBoard,
                             PhaseLeaderBoardEntry)

User = get_user_model()


class CompetitionSubmissionMetdataPageTests(TestCase):
    def setUp(self):
        self.organizer = User.objects.create_user(username="organizer", password="pass")
        self.other_admin = User.objects.create_user(username="other_admin", password="pass")
        self.other_user = User.objects.create_user(username="other", password="pass")
        self.competition = Competition.objects.create(creator=self.organizer,
                                                      modified_by=self.organizer,
                                                      published=True)
        self.competition.admins.add(self.other_admin)
        self.phase_1 = CompetitionPhase.objects.create(
            competition=self.competition,
            phasenumber=1,
            start_date=datetime.datetime.now() - datetime.timedelta(days=30),
        )

        self.url = reverse(
            "competitions:competition_submissions_metadata",
            kwargs={"competition_id": self.competition.pk, "phase_id": self.phase_1.pk}
        )

    def test_submissions_view_as_admin_returns_200(self):
        self.client.login(username="organizer", password="pass")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)

    def test_submissions_view_as_owner_returns_200(self):
        self.client.login(username="other_admin", password="pass")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)

    def test_submissions_view_as_logged_in_non_owner_or_admin_returns_404(self):
        self.client.login(username="other", password="pass")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 404)

    def test_submissions_view_as_non_logged_in_returns_302(self):
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 302)
