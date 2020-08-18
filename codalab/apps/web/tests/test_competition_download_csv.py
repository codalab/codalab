import mock
import datetime

from django.conf import settings
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model

from apps.web.models import (Competition,
                             CompetitionParticipant,
                             CompetitionPhase,
                             CompetitionSubmission,
                             CompetitionSubmissionStatus,
                             ParticipantStatus,
                             PhaseLeaderBoard,
                             PhaseLeaderBoardEntry,
                             SubmissionResultGroup,
                             SubmissionResultGroupPhase,
                             SubmissionScore,
                             SubmissionScoreDef,
                             SubmissionScoreDefGroup,
                             SubmissionScoreSet,)


User = get_user_model()


class CompetitionDownloadCSVTests(TestCase):
    def setUp(self):
        super(CompetitionDownloadCSVTests, self).setUp()

        self.user = User.objects.create(email='test@user.com', username='testuser\u2020')
        self.other_user = User.objects.create(email='other@user.com', username='other')
        self.competition = Competition.objects.create(creator=self.user, modified_by=self.user)
        self.participant_1 = CompetitionParticipant.objects.create(
            user=self.user,
            competition=self.competition,
            status=ParticipantStatus.objects.get_or_create(name='approved', codename=ParticipantStatus.APPROVED)[0]
        )
        self.phase_1 = CompetitionPhase.objects.create(
            competition=self.competition,
            phasenumber=1,
            start_date=datetime.datetime.now() - datetime.timedelta(days=30),
        )

        submission_finished = CompetitionSubmissionStatus.objects.create(name="finished", codename="finished")

        self.submission_1 = CompetitionSubmission.objects.create(
            participant=self.participant_1,
            phase=self.phase_1,
            status=submission_finished,
            submitted_at=datetime.datetime.now() - datetime.timedelta(days=29),
            description="Some description with unicode \u2020"
        )
        self.leader_board = PhaseLeaderBoard.objects.create(phase=self.phase_1)
        self.leader_board_entry_1 = PhaseLeaderBoardEntry.objects.create(
            board=self.leader_board,
            result=self.submission_1
        )

        result_group = SubmissionResultGroup.objects.create(
            competition=self.competition,
            key="Key",
            label="Test \u2020",
            ordering=1
        )
        submission_result_group_phase = SubmissionResultGroupPhase.objects.create(phase=self.phase_1, group=result_group)
        score_def = SubmissionScoreDef.objects.create(
            competition=self.competition,
            key="Key",
            label="Test \u2020",
        )
        SubmissionScoreDefGroup.objects.create(
            scoredef=score_def,
            group=result_group,
        )
        SubmissionScore.objects.create(
            result=self.submission_1,
            scoredef=score_def,
            value=123,
        )
        SubmissionScoreSet.objects.create(
            competition=self.competition,
            key="Key",
            label="Test \u2020",
            scoredef=score_def,
        )

        self.url = reverse("competitions:competition_results_complete_download", kwargs={"id": self.competition.pk,
                                                                                         "phase": self.phase_1.pk})

    def test_download_competition_csv_returns_200_with_unicode_labels(self):
        '''Unicode set in setUp method'''
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
