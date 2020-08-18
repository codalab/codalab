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


class SubmissionMarkAsFailedTests(TestCase):
    def setUp(self):
        self.organizer = User.objects.create_user(username="organizer", password="pass")
        self.participant_user = User.objects.create_user(username="participant", password="pass")
        self.other_user = User.objects.create_user(username="other", password="pass")
        self.competition = Competition.objects.create(creator=self.organizer, modified_by=self.organizer, published=True)
        self.participant_1 = CompetitionParticipant.objects.create(
            user=self.participant_user,
            competition=self.competition,
            status=ParticipantStatus.objects.get_or_create(name='approved', codename=ParticipantStatus.APPROVED)[0]
        )
        self.phase_1 = CompetitionPhase.objects.create(
            competition=self.competition,
            phasenumber=1,
            start_date=datetime.datetime.now() - datetime.timedelta(days=30),
        )

        submission_finished = CompetitionSubmissionStatus.objects.create(name="finished", codename="finished")
        CompetitionSubmissionStatus.objects.create(name="failed", codename="failed")

        self.submission_1 = CompetitionSubmission.objects.create(
            participant=self.participant_1,
            phase=self.phase_1,
            status=submission_finished,
            submitted_at=datetime.datetime.now() - datetime.timedelta(days=29)
        )

        self.client = Client()
        self.url = reverse("competitions:submission_mark_as_failed", kwargs={"submission_pk": self.submission_1.pk})

    def test_mark_as_failed_returns_404_if_not_competition_owner(self):
        self.client.login(username="other", password="pass")
        resp = self.client.post(self.url)
        self.assertEqual(resp.status_code, 404)

    def test_mark_as_failed_returns_404_if_participant_not_owner(self):
        self.client.login(username="participant", password="pass")
        resp = self.client.post(self.url)
        self.assertEqual(resp.status_code, 404)

    def test_mark_as_failed_returns_200_and_sets_submission_status_to_failed_for_owner(self):
        self.client.login(username="organizer", password="pass")
        resp = self.client.post(self.url)
        self.assertEqual(resp.status_code, 200)
        submission = CompetitionSubmission.objects.get(pk=self.submission_1.pk)
        self.assertEqual(submission.status.codename, "failed")
