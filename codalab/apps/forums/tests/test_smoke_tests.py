from django.core.urlresolvers import reverse
from django.test import TestCase
from django.contrib.auth import get_user_model

from apps.web.models import Competition
from ..models import Forum, Thread, Post


User = get_user_model()


class ForumSmokeTests(TestCase):

    def setUp(self):
        self.admin_user = User.objects.create_user(username="admin", password="pass")
        self.admin_user.is_staff = True
        self.admin_user.save()
        self.regular_user = User.objects.create_user(username="regular", password="pass")

        self.competition = Competition.objects.create(
            title="Test Competition",
            creator=self.admin_user,
            modified_by=self.admin_user,
            published=False,
        )
        self.forum = self.competition.forum
        self.thread = Thread.objects.create(forum=self.forum, started_by=self.regular_user)

    def test_forum_thread_list_view_returns_200(self):
        resp = self.client.get(reverse("forum_detail", kwargs={'forum_pk': self.forum.pk}))
        self.assertEqual(resp.status_code, 200)

    def test_forum_post_new_thread_non_logged_in_returns_302(self):
        resp = self.client.get(reverse("forum_new_thread", kwargs={'forum_pk': self.forum.pk}))
        self.assertEqual(resp.status_code, 302)

    def test_forum_post_new_thread_view_returns_200(self):
        self.client.login(username="regular", password="pass")
        resp = self.client.get(reverse("forum_new_thread", kwargs={'forum_pk': self.forum.pk}))
        self.assertEqual(resp.status_code, 200)

    def test_forum_view_thread_returns_200(self):
        resp = self.client.get(reverse("forum_thread_detail", kwargs={'forum_pk': self.forum.pk,
                                                                      'thread_pk': self.thread.pk}))
        self.assertEqual(resp.status_code, 200)

    def test_forum_new_post_requires_login_returns_302(self):
        resp = self.client.get(reverse("forum_new_post", kwargs={'forum_pk': self.forum.pk,
                                                                 'thread_pk': self.thread.pk}))
        self.assertEqual(resp.status_code, 302)

    def test_forum_new_post_returns_200(self):
        self.client.login(username="regular", password="pass")
        resp = self.client.get(reverse("forum_new_post", kwargs={'forum_pk': self.forum.pk,
                                                                 'thread_pk': self.thread.pk}))
        self.assertEqual(resp.status_code, 200)
