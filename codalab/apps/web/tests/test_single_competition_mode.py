from django.conf import settings
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.test.utils import override_settings

from apps.web import models

User = get_user_model()


class TestSingleCompetitionMode(TestCase):
    def setUp(self):
        self.user = User.objects.create(email='test@user.com', username='testuser')
        self.other_user = User.objects.create(email='other@user.com', username='other')
        self.competition = models.Competition.objects.create(creator=self.user, modified_by=self.user)
        settings.SINGLE_COMPETITION_VIEW_PK = self.competition.pk

    def test_trying_to_view_unpublished_competition_shows_warning(self):
        resp = self.client.get(reverse("home"))
        self.assertContains(resp, "Warning, SINGLE_COMPETITION_VIEW_PK setting is set but the "
                                  "competition is not published so regular users won't be able to access it!")

    def test_trying_to_view_published_competition_works_fine(self):
        self.competition.published = True
        self.competition.save()
        resp = self.client.get(reverse("home"))
        self.assertEqual(resp.status_code, 200)
