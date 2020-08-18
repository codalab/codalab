import datetime

from django.core.urlresolvers import reverse
from django.test import TestCase
from django.contrib.auth import get_user_model

from apps.web.models import Competition, CompetitionSubmission, ParticipantStatus, CompetitionParticipant, \
    CompetitionPhase


User = get_user_model()


class CoopetitionsSmokeTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username="user", password="pass")
        self.competition = Competition.objects.create(creator=self.user, modified_by=self.user)

        self.participant = CompetitionParticipant.objects.create(
            user=self.user,
            competition=self.competition,
            status=ParticipantStatus.objects.get_or_create(name='approved', codename=ParticipantStatus.APPROVED)[0]
        )
        self.phase = CompetitionPhase.objects.create(
            competition=self.competition,
            phasenumber=1,
            start_date=datetime.datetime.now() - datetime.timedelta(days=30),
        )
        self.submission = CompetitionSubmission.objects.create(
            participant=self.participant,
            phase=self.phase,
            submitted_at=datetime.datetime.now() - datetime.timedelta(days=29)
        )

    def test_like_returns_200_for_logged_in_user(self):
        self.client.login(username="user", password="pass")
        resp = self.client.get(reverse("coopetitions:like", kwargs={'submission_pk': self.submission.pk}))
        self.assertEqual(resp.status_code, 200)

    def test_like_returns_302_for_non_logged_in_user(self):
        resp = self.client.get(reverse("coopetitions:like", kwargs={'submission_pk': self.submission.pk}))
        self.assertEqual(resp.status_code, 302)

    def test_like_returns_404_for_non_existing_submission(self):
        self.client.login(username="user", password="pass")
        resp = self.client.get(reverse("coopetitions:like", kwargs={'submission_pk': 0}))
        self.assertEqual(resp.status_code, 404)
