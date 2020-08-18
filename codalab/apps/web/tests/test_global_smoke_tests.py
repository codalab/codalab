from django.core.urlresolvers import reverse
from django.test import TestCase
from django.contrib.auth import get_user_model

from apps.web.models import Competition


User = get_user_model()


class GlobalSmokeTests(TestCase):

    def setUp(self):
        self.organizer = User.objects.create_superuser(username="organizer", email="admin@example.com", password="pass")
        self.other_admin = User.objects.create_user(username="other_admin", password="pass")
        self.user = User.objects.create_user(username="user", password="pass")
        self.competition = Competition.objects.create(
            title="Test Competition",
            creator=self.organizer,
            modified_by=self.organizer,
            published=True,
        )
        self.competition.admins.add(self.other_admin)

    def test_home_page_returns_200(self):
        resp = self.client.get(reverse("home"))
        self.assertEqual(resp.status_code, 200)

    def test_competition_list_returns_200(self):
        resp = self.client.get(reverse("competitions:list"))
        self.assertEqual(resp.status_code, 200)

    def test_competition_detail_returns_200(self):
        resp = self.client.get(reverse("competitions:view", kwargs={"pk": self.competition.pk}))
        self.assertEqual(resp.status_code, 200)

    def test_my_datasets_page_returns_200(self):
        self.client.login(username="user", password="pass")
        resp = self.client.get(reverse("my_datasets"))
        self.assertEqual(resp.status_code, 200)

    def test_my_datasets_page_returns_302_when_not_logged_in(self):
        resp = self.client.get(reverse("my_datasets"))
        self.assertEqual(resp.status_code, 302)

    def test_participants_view_as_admin_returns_200(self):
        self.client.login(username="organizer", password="pass")
        resp = self.client.get(reverse("my_competition_participants", kwargs={"competition_id": self.competition.pk}))
        self.assertEqual(resp.status_code, 200)

    def test_participants_view_as_owner_returns_200(self):
        self.client.login(username="other_admin", password="pass")
        resp = self.client.get(reverse("my_competition_participants", kwargs={"competition_id": self.competition.pk}))
        self.assertEqual(resp.status_code, 200)

    def test_participants_view_as_logged_in_non_owner_or_admin_returns_404(self):
        self.client.login(username="user", password="pass")
        resp = self.client.get(reverse("my_competition_participants", kwargs={"competition_id": self.competition.pk}))
        self.assertEqual(resp.status_code, 404)

    def test_participants_view_as_non_logged_in_returns_302(self):
        resp = self.client.get(reverse("my_competition_participants", kwargs={"competition_id": self.competition.pk}))
        self.assertEqual(resp.status_code, 302)

