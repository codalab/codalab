from django.core.urlresolvers import reverse
from django.test import TestCase
from django.contrib.auth import get_user_model

from apps.web.models import (Competition,
                             CompetitionParticipant,
                             ParticipantStatus,)

User = get_user_model()


class CompetitionYamlDownload(TestCase):

    def setUp(self):
        self.organizer_user = User.objects.create_user(username="organizer", password="pass")
        self.admin_user = User.objects.create_user(username="admin", password="pass")
        self.non_admin_user = User.objects.create_user(username="non_admin", password="pass")
        self.competition = Competition.objects.create(
            title="Test Competition",
            creator=self.organizer_user,
            modified_by=self.organizer_user,
            published=False,
            original_yaml_file="original yaml file contents"
        )
        self.competition.admins.add(self.admin_user)

    def test_competition_yaml_download_returns_404_for_non_existant_competition(self):
        self.client.login(username="organizer", password="pass")
        resp = self.client.get(reverse("competitions:download_yaml", kwargs={"competition_pk": 0}))
        self.assertEqual(resp.status_code, 404)

    def test_competition_yaml_download_returns_403_for_non_admin_and_non_creator(self):
        self.client.login(username="non_admin", password="pass")
        resp = self.client.get(reverse("competitions:download_yaml", kwargs={"competition_pk": self.competition.pk}))
        self.assertEqual(resp.status_code, 403)

    def test_competition_yaml_download_returns_200_for_admin(self):
        self.client.login(username="admin", password="pass")
        resp = self.client.get(reverse("competitions:download_yaml", kwargs={"competition_pk": self.competition.pk}))
        self.assertEqual(resp.status_code, 200)

    def test_competition_yaml_download_returns_200_for_creator(self):
        self.client.login(username="organizer", password="pass")
        resp = self.client.get(reverse("competitions:download_yaml", kwargs={"competition_pk": self.competition.pk}))
        self.assertEqual(resp.status_code, 200)

    def test_competition_yaml_download_returns_the_original_yaml_data(self):
        self.client.login(username="organizer", password="pass")
        resp = self.client.get(reverse("competitions:download_yaml", kwargs={"competition_pk": self.competition.pk}))
        self.assertEqual(resp.content, b"original yaml file contents")
        self.assertIn(('Content-Type', 'text/yaml'), list(resp.items()))
        self.assertIn(('Content-Disposition', 'attachment; filename="competition_%s.yaml"' % self.competition.pk), list(resp.items()))
