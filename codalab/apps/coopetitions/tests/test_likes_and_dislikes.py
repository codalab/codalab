import datetime

from django.core.urlresolvers import reverse
from django.test import TestCase
from django.contrib.auth import get_user_model

from apps.web.models import Competition, CompetitionSubmission, ParticipantStatus, CompetitionParticipant, \
    CompetitionPhase
from apps.coopetitions.models import Like, Dislike


User = get_user_model()


class CoopetitionsLikeDislikeTests(TestCase):

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
        self.client.login(username="user", password="pass")
        self.like_url = reverse("coopetitions:like", kwargs={'submission_pk': self.submission.pk})
        self.dislike_url = reverse("coopetitions:dislike", kwargs={'submission_pk': self.submission.pk})

    def test_like_creates_like_model(self):
        self.client.get(self.like_url)
        self.assertTrue(Like.objects.get(user=self.user, submission=self.submission))

    def test_like_deletes_dislike_model_if_it_exists(self):
        self.client.get(self.like_url)
        self.assertTrue(Like.objects.get(user=self.user, submission=self.submission))
        self.client.get(self.like_url)
        self.assertFalse(Like.objects.filter(user=self.user, submission=self.submission).exists())

    def test_like_increments_counter(self):
        self.assertEqual(self.submission.like_count, 0)
        self.client.get(self.like_url)
        self.submission = CompetitionSubmission.objects.get(pk=self.submission.pk)
        self.assertEqual(self.submission.like_count, 1)

    def test_like_when_liked_already_decrements_counter(self):
        self.client.get(self.like_url)
        self.submission = CompetitionSubmission.objects.get(pk=self.submission.pk)
        self.assertEqual(self.submission.like_count, 1)
        self.client.get(self.like_url)
        self.submission = CompetitionSubmission.objects.get(pk=self.submission.pk)
        self.assertEqual(self.submission.like_count, 0)

    def test_dislike_creates_dislike_model(self):
        self.client.get(self.dislike_url)
        self.assertTrue(Dislike.objects.get(user=self.user, submission=self.submission))

    def test_dislike_deletes_like_model_if_it_exists(self):
        self.client.get(self.dislike_url)
        self.assertTrue(Dislike.objects.get(user=self.user, submission=self.submission))
        self.client.get(self.dislike_url)
        self.assertFalse(Dislike.objects.filter(user=self.user, submission=self.submission).exists())

    def test_dislike_increments_counter(self):
        self.assertEqual(self.submission.dislike_count, 0)
        self.client.get(self.dislike_url)
        self.submission = CompetitionSubmission.objects.get(pk=self.submission.pk)
        self.assertEqual(self.submission.dislike_count, 1)

    def test_dislike_when_liked_already_decrements_counter(self):
        self.client.get(self.dislike_url)
        self.submission = CompetitionSubmission.objects.get(pk=self.submission.pk)
        self.assertEqual(self.submission.dislike_count, 1)
        self.client.get(self.dislike_url)
        self.submission = CompetitionSubmission.objects.get(pk=self.submission.pk)
        self.assertEqual(self.submission.dislike_count, 0)

    def test_like_or_dislike_quickly_maintains_proper_score_count(self):
        self.client.get(self.dislike_url)
        self.client.get(self.like_url)
        self.client.get(self.like_url)
        self.client.get(self.dislike_url)
        self.client.get(self.like_url)
        self.client.get(self.dislike_url)
        self.submission = CompetitionSubmission.objects.get(pk=self.submission.pk)
        self.assertEqual(self.submission.dislike_count, 1)
        self.assertEqual(self.submission.like_count, 0)
