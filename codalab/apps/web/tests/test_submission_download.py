import datetime
import requests

from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test.client import Client
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from django.conf import settings

from apps.web.models import (Competition,
                             CompetitionParticipant,
                             CompetitionPhase,
                             CompetitionSubmission,
                             CompetitionSubmissionStatus,
                             ParticipantStatus)

User = get_user_model()


# Note: Previously seems that Django returned a 200 on redirect. Now if we redirect to AWS when using USE_AWS
# (apps.web.views, line 1225) we get a 302 and have to goto the response's url to make a request to AWS.

class CompetitionSubmissionDownloadTests(TestCase):
    def setUp(self):
        self.organizer = User.objects.create_user(username="organizer", password="pass")
        self.participant_user = User.objects.create_user(username="participant", password="pass")
        self.other_participant_user = User.objects.create_user(username="other_participant", password="pass")
        self.other_user = User.objects.create_user(username="other", password="pass")
        self.competition = Competition.objects.create(creator=self.organizer, modified_by=self.organizer, published=True)
        self.participant_1 = CompetitionParticipant.objects.create(
            user=self.participant_user,
            competition=self.competition,
            status=ParticipantStatus.objects.get_or_create(name='approved', codename=ParticipantStatus.APPROVED)[0]
        )
        self.participant_2 = CompetitionParticipant.objects.create(
            user=self.other_participant_user,
            competition=self.competition,
            status=ParticipantStatus.objects.get_or_create(name='approved', codename=ParticipantStatus.APPROVED)[0]
        )
        self.phase_1 = CompetitionPhase.objects.create(
            competition=self.competition,
            phasenumber=1,
            start_date=datetime.datetime.now() - datetime.timedelta(days=30),
        )

        self.submission_finished_status = CompetitionSubmissionStatus.objects.create(name="finished", codename="finished")
        CompetitionSubmissionStatus.objects.create(name="failed", codename="failed")

        self.submission_1 = CompetitionSubmission.objects.create(
            participant=self.participant_1,
            phase=self.phase_1,
            status=self.submission_finished_status,
            is_public=False,
            submitted_at=datetime.datetime.now() - datetime.timedelta(days=29),
            stdout_file=SimpleUploadedFile(name="test.txt", content="test std out".encode('utf-8'))
        )

        self.url = reverse("my_competition_output", kwargs={"submission_id": self.submission_1.pk,
                                                            "filetype": "stdout.txt"})

        self.client = Client()

        self.expected_return_value = 302 if settings.USE_AWS else 200

    def test_submission_info_download_when_submitter_returns_200(self):
        self.client.login(username="participant", password="pass")
        resp = self.client.get(self.url)

        self.assertEqual(resp.status_code, self.expected_return_value)

    def test_submission_info_download_when_admin_returns_200(self):
        self.client.login(username="organizer", password="pass")
        resp = self.client.get(self.url)

        self.assertEqual(resp.status_code, self.expected_return_value)

    def test_submission_info_download_when_non_admin_and_non_submitter_returns_404(self):
        self.client.login(username="other", password="pass")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 404)

    def test_submission_info_download_when_non_logged_in_returns_404(self):
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 404)

    def test_submission_info_download_returns_proper_data(self):
        self.client.login(username="participant", password="pass")
        resp = self.client.get(self.url)

        self.assertEqual(resp.status_code, self.expected_return_value)

        if self.expected_return_value == 302:
            redirect_resp = requests.get(resp.url)

            self.assertEqual(redirect_resp.status_code, 200)
            self.assertEqual(redirect_resp.content, self.submission_1.stdout_file.read())
        else:
            self.assertEqual(resp.content, self.submission_1.stdout_file.read())

    # def test_submission_download_public_requires_participation_access(self):
    #     self.submission_1.is_public = True
    #     self.submission_1.save()
    #     self.competition.has_registration = True
    #     self.competition.save()
    #
    #     self.client.login(username="other", password="pass")
    #     resp = self.client.get(self.url)
    #     self.assertEquals(resp.status_code, 404)
    #     self.client.logout()
    #
    #     self.client.login(username="other_participant", password="pass")
    #     resp = self.client.get(self.url)
    #     self.assertEquals(resp.status_code, 200)

    def test_submission_download_public_without_registration_allows_access(self):
        self.competition.has_registration = False
        self.competition.save()
        self.submission_1.is_public = True
        self.submission_1.save()
        self.client.login(username="other", password="pass")
        resp = self.client.get(self.url)

        self.assertEqual(resp.status_code, self.expected_return_value)

    def test_submission_deleted_then_re_evaluated_does_not_make_output_corrupted(self):
        self.submission_1.delete()

        new_submission = CompetitionSubmission.objects.create(
            participant=self.participant_1,
            phase=self.phase_1,
            status=self.submission_finished_status,
            is_public=False,
            submitted_at=datetime.datetime.now() - datetime.timedelta(days=29),
            stdout_file=SimpleUploadedFile(name="test.txt", content="new stdout".encode('utf-8'))
        )
        new_url = reverse(
            "my_competition_output",
            kwargs={
                "submission_id": new_submission.pk,
                "filetype": "stdout.txt"
            }
        )
        self.client.login(username="participant", password="pass")
        resp = self.client.get(new_url)

        self.assertEqual(resp.status_code, self.expected_return_value)

        if self.expected_return_value == 302:
            redirect_resp = requests.get(resp.url)

            self.assertEqual(redirect_resp.status_code, 200)
            self.assertEqual(redirect_resp.content, b"new stdout")
        else:
            self.assertEqual(resp.content, b"new stdout")
