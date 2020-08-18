import datetime

from django.core.urlresolvers import reverse
from django.test import TestCase
from django.contrib.auth import get_user_model

from apps.web.models import Competition, CompetitionSubmission, ParticipantStatus, CompetitionParticipant, \
    CompetitionPhase
from apps.coopetitions.models import Like, Dislike


User = get_user_model()


class DownloadRecordTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username="user", password="pass")
        self.other_user = User.objects.create_user(username="other_user", password="pass")
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
        self.download_url = reverse("my_competition_output", kwargs={
            "submission_id": self.submission.pk,
            "filetype": "input.zip"
        })

    def test_download_submission_only_main_submission_download_increases_count(self):
        other_file_url = reverse("my_competition_output", kwargs={
            "submission_id": self.submission.pk,
            "filetype": "stdout.txt"
        })
        self.client.get(other_file_url)
        updated_submission = CompetitionSubmission.objects.get(pk=self.submission.pk)
        self.assertEqual(updated_submission.download_count, 0)

    def test_download_submissions_without_permissions_doesnt_increase_download_count(self):
        self.client.logout()
        self.client.login(username="other_user", password="pass")
        self.client.get(self.download_url)
        updated_submission = CompetitionSubmission.objects.get(pk=self.submission.pk)
        self.assertEqual(updated_submission.download_count, 0)

    def test_download_submission_increases_download_count_by_one(self):
        self.client.get(self.download_url)
        updated_submission = CompetitionSubmission.objects.get(pk=self.submission.pk)
        self.assertEqual(updated_submission.download_count, 1)

    def test_download_submission_multiple_times_only_increases_download_count_by_one(self):
        self.client.get(self.download_url)
        updated_submission = CompetitionSubmission.objects.get(pk=self.submission.pk)
        self.assertEqual(updated_submission.download_count, 1)
        self.client.get(self.download_url)
        updated_submission = CompetitionSubmission.objects.get(pk=self.submission.pk)
        self.assertEqual(updated_submission.download_count, 1)
