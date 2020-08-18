from django.core.urlresolvers import reverse
from django.test import TestCase
from django.contrib.auth import get_user_model


User = get_user_model()


class AnalyticsPageTests(TestCase):
    def setUp(self):
        self.admin_user = User.objects.create_user(username="admin", password="pass")
        self.admin_user.is_staff = True
        self.admin_user.save()
        self.regular_user = User.objects.create_user(username="regular", password="pass")

    def test_analytics_detail_page_returns_404_for_logged_in_user(self):
        resp = self.client.get(reverse("analytics_detail"))
        self.assertEqual(resp.status_code, 302)

    def test_analytics_detail_page_returns_404_for_non_admin(self):
        self.client.login(username="regular", password="pass")
        resp = self.client.get(reverse("analytics_detail"))
        self.assertEqual(resp.status_code, 404)

    def test_analytics_detail_page_returns_200_for_admin(self):
        self.client.login(username="admin", password="pass")
        resp = self.client.get(reverse("analytics_detail"))
        self.assertEqual(resp.status_code, 200)
