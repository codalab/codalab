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


class CompetitionSubmissionAdminPageTests(TestCase):
    def setUp(self):
        self.organizer = User.objects.create_user(username="organizer", password="pass")
        self.other_admin = User.objects.create_user(username="other_admin", password="pass")
        self.other_user = User.objects.create_user(username="other", password="pass")
        self.competition = Competition.objects.create(creator=self.organizer,
                                                      modified_by=self.organizer,
                                                      published=True)
        self.competition.admins.add(self.other_admin)
        self.phase_1 = CompetitionPhase.objects.create(
            competition=self.competition,
            phasenumber=1,
            start_date=datetime.datetime.now() - datetime.timedelta(days=30),
        )

        self.url = reverse("my_competition_submissions", kwargs={"competition_id": self.competition.pk})
        self.url = "%s?phase=%s" % (self.url, self.phase_1.id)

    def test_submissions_view_as_admin_returns_200(self):
        self.client.login(username="organizer", password="pass")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)

    def test_submissions_view_as_owner_returns_200(self):
        self.client.login(username="other_admin", password="pass")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)

    def test_submissions_view_as_logged_in_non_owner_or_admin_returns_404(self):
        self.client.login(username="other", password="pass")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 404)

    def test_submissions_view_as_non_logged_in_returns_302(self):
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 302)


class CompetitionSubmissionDeleteTests(TestCase):
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

    def test_delete_view_returns_404_if_not_competition_owner(self):
        self.client.login(username="other", password="pass")
        resp = self.client.post(reverse("competitions:submission_delete", kwargs={"pk": self.submission_1.pk}))
        self.assertEqual(resp.status_code, 404)

    def test_delete_view_returns_404_if_not_submission_owner(self):
        self.client.login(username="other", password="pass")
        resp = self.client.post(reverse("competitions:submission_delete", kwargs={"pk": self.submission_1.pk}))
        self.assertEqual(resp.status_code, 404)

    def test_delete_view_redirects_to_success_if_submission_owner(self):
        # There is currently no way for participants to delete their own submission, but I'll add this
        # behavior so it can be "switched on" easily later
        self.client.login(username="participant", password="pass")
        resp = self.client.post(reverse("competitions:submission_delete", kwargs={"pk": self.submission_1.pk}))
        self.assertRedirects(resp, reverse("competitions:view", kwargs={"pk": self.competition.pk}))

    def test_delete_view_redirects_to_success_if_competition_organizer_and_deletes_submission(self):
        self.client.login(username="organizer", password="pass")
        resp = self.client.post(reverse("competitions:submission_delete", kwargs={"pk": self.submission_1.pk}))
        self.assertRedirects(resp, reverse("competitions:view", kwargs={"pk": self.competition.pk}))
        self.assertEqual(0, len(CompetitionSubmission.objects.filter(pk=self.submission_1.pk)))

    def test_delete_view_returns_302_if_not_logged_in(self):
        resp = self.client.post(reverse("competitions:submission_delete", kwargs={"pk": self.submission_1.pk}))
        self.assertEqual(resp.status_code, 302)

    def test_failed_submissions_not_counted_when_saving_submissions(self):
        for _ in range(0, 3):
            sub = CompetitionSubmission.objects.create(
                participant=self.participant_1,
                phase=self.phase_1,
                submitted_at=datetime.datetime.now()
            )
            sub.status = CompetitionSubmissionStatus.objects.get(name=CompetitionSubmissionStatus.FAILED)
            sub.save()

        failed_count = CompetitionSubmission.objects.filter(phase=self.phase_1,
                                                            participant=self.participant_1,
                                                            status__name=CompetitionSubmissionStatus.FAILED).count()
        self.assertEqual(failed_count, 3)
