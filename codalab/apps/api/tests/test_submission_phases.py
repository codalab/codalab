
"""
test for competition creation via api
"""
import sys
import os
import json
import mock
from django.utils import timezone
from django.core.files.uploadedfile import SimpleUploadedFile

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.web.models import *

# Get the user model
User = get_user_model()


class SubmissionCreationTests(TestCase):

    def setUp(self):
        self.organizer_user = User.objects.create_user(username="organizer", password="pass")
        self.competition = Competition.objects.create(
            title="Test Competition",
            creator=self.organizer_user,
            modified_by=self.organizer_user
        )
        self.participant = CompetitionParticipant.objects.create(
            user=self.organizer_user,
            competition=self.competition,
            status=ParticipantStatus.objects.get_or_create(name='approved', codename=ParticipantStatus.APPROVED)[0]
        )
        # Make 3 phases where each is 15 days apart
        self.phase = CompetitionPhase.objects.create(
            competition=self.competition,
            phasenumber=1,
            start_date=datetime.datetime.now() - datetime.timedelta(days=30),
        )
        self.phase_2 = CompetitionPhase.objects.create(
            competition=self.competition,
            phasenumber=1,
            start_date=datetime.datetime.now() - datetime.timedelta(days=15),
            phase_never_ends=True,
        )
        self.phase_3 = CompetitionPhase.objects.create(
            competition=self.competition,
            phasenumber=1,
            start_date=datetime.datetime.now() - datetime.timedelta(days=1),
        )
        self.client.login(username="organizer", password="pass")

        self.url = reverse("api_competition_submission_post", kwargs={"competition_id": self.competition.pk})

        self.client.login(username="organizer", password="pass")
        the_file = SimpleUploadedFile('best_file_eva.txt', 'these are the file contents!'.encode('utf-8'))

        self.data = {
            'name': the_file.name,
            'type': '.zip',
            'size': the_file.size,
            'id': the_file.name,
        }

    def test_submission_creation_saves_given_phase_id(self):
        with mock.patch('apps.api.views.competition_views.evaluate_submission') as evaluate_submission_mock:
            self.client.post(self.url + "?phase_id=%s" % self.phase_2.pk, self.data)
        new_submission = CompetitionSubmission.objects.get(participant=self.participant)
        assert new_submission.phase == self.phase_2

    def test_submission_creation_fails_when_phase_id_not_given(self):
        try:
            self.client.post(self.url, self.data)
            assert False, "If no phase id is specified, submission should not be processed"
        except:
            assert True

    def test_submission_creation_works_mixed_phase_never_ends_and_regular_active(self):
        with mock.patch('apps.api.views.competition_views.evaluate_submission') as evaluate_submission_mock:
            self.client.post(self.url + "?phase_id=%s" % self.phase_3.pk, self.data)
        new_submission = CompetitionSubmission.objects.get(participant=self.participant)
        assert new_submission.phase == self.phase_3

    def test_submission_creation_fails_with_expired_phase(self):
        try:
            self.client.post(self.url + "?phase_id=%s" % self.phase_1.pk, self.data)
            assert False, "Should not be able to submit to a closed phase"
        except:
            assert True
