import datetime
import mock
from apps.authenz.models import ClUser
from apps.web.models import CompetitionSubmission, Competition, CompetitionPhase, CompetitionParticipant, \
    ParticipantStatus
from django.conf import settings
from django.http.response import HttpResponseBase
from django.test import TestCase


class ChahubMixinTests(TestCase):

    def setUp(self):
        settings.PYTEST_FORCE_CHAHUB = True

        self.user = ClUser.objects.create_user(username="user", password="pass")
        self.competition = Competition.objects.create(
            title="Test Competition",
            creator=self.user,
            modified_by=self.user,
            published=True,
        )
        self.participant = CompetitionParticipant.objects.create(
            user=self.user,
            competition=self.competition,
            status=ParticipantStatus.objects.get_or_create(name='approved', codename=ParticipantStatus.APPROVED)[0],
        )
        self.phase = CompetitionPhase.objects.create(
            competition=self.competition,
            phasenumber=1,
            start_date=datetime.datetime.now() - datetime.timedelta(days=30),
        )

    def tearDown(self):
        settings.PYTEST_FORCE_CHAHUB = False

    def test_submission_mixin_save_doesnt_resend_same_data(self):
        submission = CompetitionSubmission(phase=self.phase, participant=self.participant)
        with mock.patch('apps.chahub.models.send_to_chahub') as send_to_chahub_mock:
            send_to_chahub_mock.return_value = HttpResponseBase(status=201)
            send_to_chahub_mock.return_value.content = ""
            submission.save()
            # attempts to send to Chahub once
            assert send_to_chahub_mock.called

            # reset
            send_to_chahub_mock.called = False

            # does not call again
            submission.save()
            assert not send_to_chahub_mock.called

    # We should probably have a test for an _invalid_ model, but for now all the models we have we send all the time
    # def test_submission_invalid_not_sent_to_chahub(self):
    #     # Make submission invalid
    #     self.competition.published = False
    #     self.competition.save()
    #
    #     submission = CompetitionSubmission(phase=self.phase, participant=self.participant)
    #     with mock.patch('apps.web.models.CompetitionSubmission.send_to_chahub') as send_to_chahub_mock:
    #         submission.save()
    #         assert not send_to_chahub_mock.called

    def test_submission_invalid_not_marked_for_retry_again(self):
        # Make submission invalid
        self.competition.published = False
        self.competition.save()

        # Mark submission for retry
        submission = CompetitionSubmission(phase=self.phase, participant=self.participant, chahub_needs_retry=True)
        with mock.patch('apps.chahub.models.send_to_chahub') as send_to_chahub_mock:
            submission.save()
            assert not send_to_chahub_mock.called

    def test_submission_valid_not_retried_again(self):
        # Mark submission for retry
        submission = CompetitionSubmission(phase=self.phase, participant=self.participant, chahub_needs_retry=True)
        with mock.patch('apps.chahub.models.send_to_chahub') as send_to_chahub_mock:
            send_to_chahub_mock.return_value = HttpResponseBase(status=201)
            send_to_chahub_mock.return_value.content = ""
            submission.save()  # NOTE! not called with force_to_chahub=True as retrying would set
            # It does not call send method, only during "do_retries" task should it
            assert not send_to_chahub_mock.called

    def test_submission_retry_valid_retried_then_sent_and_not_retried_again(self):
        # Mark submission for retry
        submission = CompetitionSubmission(phase=self.phase, participant=self.participant, chahub_needs_retry=True)
        with mock.patch('apps.chahub.models.send_to_chahub') as send_to_chahub_mock:
            send_to_chahub_mock.return_value = HttpResponseBase(status=201)
            send_to_chahub_mock.return_value.content = ""
            submission.save(force_to_chahub=True)
            # It does not need retry any more, and was successful
            assert send_to_chahub_mock.called
            assert not CompetitionSubmission.objects.get(pk=submission.pk).chahub_needs_retry

            # reset
            send_to_chahub_mock.called = False

            # Try sending again
            submission.save(force_to_chahub=True)
            assert not send_to_chahub_mock.called
