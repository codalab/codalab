from django.core.urlresolvers import reverse
from django.test import TestCase
from django.contrib.auth import get_user_model

from apps.web.models import (Competition,
                             CompetitionParticipant,
                             ParticipantStatus,)

User = get_user_model()


class CompetitionSecretKey(TestCase):

    def setUp(self):
        self.organizer_user = User.objects.create_user(username="organizer", password="pass")
        self.participant_user = User.objects.create_user(username="participant", password="pass")
        self.competition = Competition.objects.create(
            title="Test Competition",
            creator=self.organizer_user,
            modified_by=self.organizer_user,
            published=False
        )
        self.competition.participants.add(
            CompetitionParticipant.objects.create(
                competition=self.competition,
                user=self.participant_user,
                status=ParticipantStatus.objects.get_or_create(name='approved', codename=ParticipantStatus.APPROVED)[0]
            )
        )

    def test_competition_view_unpublished_returns_404_for_non_creator(self):
        resp = self.client.get(reverse("competitions:view", kwargs={"pk": self.competition.pk}))
        self.assertEqual(resp.status_code, 404)

    def test_competition_view_unpublished_returns_404_for_non_creator_with_invalid_secret_key(self):
        resp = self.client.get(reverse("competitions:view", kwargs={"pk": self.competition.pk}), {"secret_key": "gibberish"})
        self.assertEqual(resp.status_code, 404)

    def test_competition_view_unpublished_returns_200_for_non_creator_with_valid_secret_key(self):
        resp = self.client.get(reverse("competitions:view", kwargs={"pk": self.competition.pk}), {"secret_key": self.competition.secret_key})
        self.assertEqual(resp.status_code, 200)

    def test_competition_view_unpublished_returns_200_for_creator(self):
        self.client.login(username="organizer", password="pass")
        resp = self.client.get(reverse("competitions:view", kwargs={"pk": self.competition.pk}))
        self.assertEqual(resp.status_code, 200)

    def test_competition_view_unpublished_returns_200_for_competition_admins(self):
        some_admin = User.objects.create_user(username="some_admin", password="pass")
        self.client.login(username="some_admin", password="pass")
        self.competition.admins.add(some_admin)
        self.competition.save()
        resp = self.client.get(reverse("competitions:view", kwargs={"pk": self.competition.pk}))
        self.assertEqual(resp.status_code, 200)

    def test_competition_view_unpublished_returns_200_for_participant(self):
        self.client.login(username="participant", password="pass")
        resp = self.client.get(reverse("competitions:view", kwargs={"pk": self.competition.pk}))
        self.assertEqual(resp.status_code, 200)
