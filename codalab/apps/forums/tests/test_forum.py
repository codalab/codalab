from django.core.urlresolvers import reverse
from django.test import TestCase
from django.contrib.auth import get_user_model

from apps.web.models import Competition


User = get_user_model()


class ForumTests(TestCase):

    def setUp(self):
        self.admin_user = User.objects.create_superuser("admin", "admin@example.com", "pass")

        self.competition = Competition.objects.create(
            title="Test Competition",
            creator=self.admin_user,
            modified_by=self.admin_user,
            published=True,
        )

    def test_forum_created_when_competition_saved(self):
        self.assertTrue(self.competition.forum)

    def test_competition_detail_creates_forum_if_none_exists(self):
        # This is a test for legacy behavior, so let's put the competition in
        # legacy state (before forum post save)
        self.competition.forum.delete()
        resp = self.client.get(reverse("competitions:view", kwargs={"pk": self.competition.pk}))
        self.assertEqual(resp.status_code, 200)
        updated_competition = Competition.objects.get(pk=self.competition.pk)
        self.assertTrue(updated_competition.forum)
