import datetime
import json

import StringIO
import zipfile

import mock
from django.core.files.base import ContentFile

from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test.client import Client
from django.contrib.auth import get_user_model

from apps.jobs.models import Job
from apps.web.models import (Competition,
                             CompetitionParticipant,
                             CompetitionPhase,
                             CompetitionSubmission,
                             CompetitionSubmissionStatus,
                             ParticipantStatus,
                             PhaseLeaderBoard,
                             PhaseLeaderBoardEntry,
                             add_submission_to_leaderboard, SubmissionResultGroup, SubmissionResultGroupPhase,
                             SubmissionScoreDef, SubmissionScoreDefGroup, SubmissionScore, SubmissionScoreSet)
from apps.web.tasks import update_submission

User = get_user_model()


class SubmissionLeaderboardTests(TestCase):
    def setUp(self):
        self.organizer = User.objects.create_user(username="organizer", password="pass")
        self.participant_user = User.objects.create_user(username="participant", password="pass")
        self.other_user = User.objects.create_user(username="other", password="pass")
        self.competition = Competition.objects.create(creator=self.organizer, modified_by=self.organizer,
                                                      published=True)
        self.participant_1 = CompetitionParticipant.objects.create(
            user=self.participant_user,
            competition=self.competition,
            status=ParticipantStatus.objects.get_or_create(name='approved', codename=ParticipantStatus.APPROVED)[0]
        )
        self.organizer_participant = CompetitionParticipant.objects.create(
            user=self.organizer,
            competition=self.competition,
            status=ParticipantStatus.objects.get_or_create(name='approved', codename=ParticipantStatus.APPROVED)[0]
        )
        self.phase_1 = CompetitionPhase.objects.create(
            competition=self.competition,
            phasenumber=1,
            start_date=datetime.datetime.now() - datetime.timedelta(days=30),
        )

        self.phase_1.reference_data.save('test-file.txt', ContentFile("This is some fake reference data"))
        self.phase_1.save()

        assert self.phase_1.reference_data.name

        submission_finished = CompetitionSubmissionStatus.objects.create(name="finished", codename="finished")
        submission_failed = CompetitionSubmissionStatus.objects.create(name="failed", codename="failed")

        self.submission_1 = CompetitionSubmission.objects.create(
            participant=self.participant_1,
            phase=self.phase_1,
            status=submission_finished,
            submitted_at=datetime.datetime.now() - datetime.timedelta(days=29)
        )
        self.submission_2 = CompetitionSubmission.objects.create(
            participant=self.organizer_participant,
            phase=self.phase_1,
            status=submission_finished,
            submitted_at=datetime.datetime.now() - datetime.timedelta(days=29)
        )
        self.submission_3 = CompetitionSubmission.objects.create(
            participant=self.participant_1,
            phase=self.phase_1,
            status=submission_failed,
            submitted_at=datetime.datetime.now() - datetime.timedelta(days=29)
        )
        self.submission_4 = CompetitionSubmission.objects.create(
            participant=self.participant_1,
            phase=self.phase_1,
            status=submission_finished,
            submitted_at=datetime.datetime.now() - datetime.timedelta(days=29)
        )

        # Scores setup

        self.leader_board = PhaseLeaderBoard.objects.create(phase=self.phase_1)
        self.leader_board_entry_1 = PhaseLeaderBoardEntry.objects.create(
            board=self.leader_board,
            result=self.submission_1
        )

        self.result_group = SubmissionResultGroup.objects.create(
            competition=self.competition,
            key="Key",
            label=u"Test \u2020",
            ordering=1
        )
        self.submission_result_group_phase = SubmissionResultGroupPhase.objects.create(phase=self.phase_1,
                                                                                       group=self.result_group)
        self.score_def = SubmissionScoreDef.objects.create(
            competition=self.competition,
            key="Key",
            label=u"Test \u2020",
            sorting='desc',
        )
        SubmissionScoreDefGroup.objects.create(
            scoredef=self.score_def,
            group=self.result_group,
        )
        SubmissionScore.objects.create(
            result=self.submission_1,
            scoredef=self.score_def,
            value=123,
        )
        SubmissionScore.objects.create(
            result=self.submission_2,
            scoredef=self.score_def,
            value=120,
        )
        SubmissionScoreSet.objects.create(
            competition=self.competition,
            key="Key",
            label=u"Test \u2020",
            scoredef=self.score_def,
        )

        # End scores setup

        self.submission_1.status = submission_finished
        self.submission_1.save()
        self.submission_2.status = submission_finished
        self.submission_2.save()
        self.submission_3.status = submission_failed
        self.submission_3.save()
        self.submission_4.status = submission_finished
        self.submission_4.save()

        add_submission_to_leaderboard(self.submission_2)

        self.client = Client()
        self.toggle_url = reverse("competitions:submission_toggle_leaderboard", kwargs={"submission_pk": self.submission_1.pk})

    def test_toggle_leaderboard_returns_404_if_not_competition_owner(self):
        self.client.login(username="other", password="pass")
        resp = self.client.post(self.toggle_url)
        self.assertEquals(resp.status_code, 404)

    def test_toggle_leaderboard_returns_404_if_participant_not_owner(self):
        self.client.login(username="participant", password="pass")
        resp = self.client.post(self.toggle_url)
        self.assertEquals(resp.status_code, 404)

    def test_toggle_leaderboard_returns_200_and_removes_submission_from_leaderboard(self):
        add_submission_to_leaderboard(self.submission_1)
        self.client.login(username="organizer", password="pass")
        resp = self.client.post(self.toggle_url)
        self.assertEquals(resp.status_code, 200)
        submission_exists_on_leaderboard = PhaseLeaderBoardEntry.objects.filter(
            result=self.submission_1
        ).exists()
        self.assertFalse(submission_exists_on_leaderboard)

        # Make sure the other submission remains untouched
        self.assertTrue(PhaseLeaderBoardEntry.objects.get(result=self.submission_2))

    def test_toggle_leaderboard_returns_200_and_adds_submission_to_leaderboard(self):
        self.client.login(username="organizer", password="pass")
        resp = self.client.post(self.toggle_url)
        self.assertEquals(resp.status_code, 200)
        submission_exists_on_leaderboard = PhaseLeaderBoardEntry.objects.filter(
            board=self.leader_board,
            result=self.submission_1
        )
        assert not submission_exists_on_leaderboard
        # The submission is automatically added due to the setup for the competition. So we re-toggle to remove it
        resp = self.client.post(self.toggle_url)
        self.assertEquals(resp.status_code, 200)
        submission_exists_on_leaderboard = PhaseLeaderBoardEntry.objects.filter(
            board=self.leader_board,
            result=self.submission_1
        )
        assert submission_exists_on_leaderboard

        # Make sure the other submission remains untouched
        self.assertTrue(PhaseLeaderBoardEntry.objects.get(result=self.submission_2))

    def test_toggle_leaderboard_returns_400_if_submission_was_not_marked_finished(self):
        # Any submission that is not status = Finished should fail, submission_3 is marked 'failed'
        self.client.login(username="organizer", password="pass")
        url = reverse("competitions:submission_toggle_leaderboard", kwargs={"submission_pk": self.submission_3.pk})
        resp = self.client.post(url)
        self.assertEquals(resp.status_code, 400)

    def test_submission_scoring_forced_best_to_leaderboard_puts_higher_score_on_leaderboard_when_descending(self):
        self.competition.force_submission_to_leaderboard = True
        self.competition.disallow_leaderboard_modifying = True
        self.competition.save()
        self.phase_1.force_best_submission_to_leaderboard = True
        self.phase_1.save()
        SubmissionScore.objects.create(
            result=self.submission_4,
            scoredef=self.score_def,
            value=125,
        )
        self.submission_4.execution_key = json.dumps({'score': 125})
        self.submission_4.save()

        zip_buffer = StringIO.StringIO()
        zip_name = "{0}.zip".format('submission_output')
        zip_file = zipfile.ZipFile(zip_buffer, "w")

        zip_file.writestr('scores.txt', 'key: 150\n')

        zip_file.close()

        self.submission_4.output_file.save(zip_name, ContentFile(zip_buffer.getvalue()))
        self.submission_4.save()

        print("SUBMISSION SECRET IS {}".format(self.submission_4.secret))

        task_args = {
            'submission_id': self.submission_4.id
        }
        json_task_args = json.dumps(task_args)
        new_job = Job.objects.create(task_args_json=json_task_args, task_type='evaluate_submission')

        with mock.patch('apps.web.tasks.score') as mock_score:
            update_submission(new_job.id, {'status': 'finished'}, str(self.submission_4.secret))

        assert PhaseLeaderBoardEntry.objects.filter(board=self.leader_board, result=self.submission_4)

    def test_submission_scoring_forced_best_to_leaderboard_does_not_put_lower_score_on_leaderboard_when_descending(self):
        self.competition.force_submission_to_leaderboard = True
        self.competition.disallow_leaderboard_modifying = True
        self.competition.save()
        self.phase_1.force_best_submission_to_leaderboard = True
        self.phase_1.save()
        SubmissionScore.objects.create(
            result=self.submission_4,
            scoredef=self.score_def,
            value=120,
        )
        self.submission_4.execution_key = json.dumps({'score': 120})
        self.submission_4.save()

        zip_buffer = StringIO.StringIO()
        zip_name = "{0}.zip".format('submission_output')
        zip_file = zipfile.ZipFile(zip_buffer, "w")

        zip_file.writestr('scores.txt', 'key: 150\n')

        zip_file.close()

        self.submission_4.output_file.save(zip_name, ContentFile(zip_buffer.getvalue()))
        self.submission_4.save()

        print("SUBMISSION SECRET IS {}".format(self.submission_4.secret))

        task_args = {
            'submission_id': self.submission_4.id
        }
        json_task_args = json.dumps(task_args)
        new_job = Job.objects.create(task_args_json=json_task_args, task_type='evaluate_submission')

        with mock.patch('apps.web.tasks.score') as mock_score:
            update_submission(new_job.id, {'status': 'finished'}, str(self.submission_4.secret))

        assert not PhaseLeaderBoardEntry.objects.filter(board=self.leader_board, result=self.submission_4)

    def test_submission_scoring_forced_best_to_leaderboard_puts_lower_score_on_leaderboard_when_ascending(self):
        self.score_def.sorting = 'asc'
        self.score_def.save()
        self.competition.force_submission_to_leaderboard = True
        self.competition.disallow_leaderboard_modifying = True
        self.competition.save()
        self.phase_1.force_best_submission_to_leaderboard = True
        self.phase_1.save()
        SubmissionScore.objects.create(
            result=self.submission_4,
            scoredef=self.score_def,
            value=120,
        )
        self.submission_4.execution_key = json.dumps({'score': 120})
        self.submission_4.save()

        zip_buffer = StringIO.StringIO()
        zip_name = "{0}.zip".format('submission_output')
        zip_file = zipfile.ZipFile(zip_buffer, "w")

        zip_file.writestr('scores.txt', 'key: 150\n')

        zip_file.close()

        self.submission_4.output_file.save(zip_name, ContentFile(zip_buffer.getvalue()))
        self.submission_4.save()

        print("SUBMISSION SECRET IS {}".format(self.submission_4.secret))

        task_args = {
            'submission_id': self.submission_4.id
        }
        json_task_args = json.dumps(task_args)
        new_job = Job.objects.create(task_args_json=json_task_args, task_type='evaluate_submission')

        with mock.patch('apps.web.tasks.score') as mock_score:
            update_submission(new_job.id, {'status': 'finished'}, str(self.submission_4.secret))

        assert PhaseLeaderBoardEntry.objects.filter(board=self.leader_board, result=self.submission_4)

    def test_submission_scoring_forced_best_to_leaderboard_does_not_put_higher_score_on_leaderboard_when_ascending(self):
        self.score_def.sorting = 'asc'
        self.score_def.save()
        self.competition.force_submission_to_leaderboard = True
        self.competition.disallow_leaderboard_modifying = True
        self.competition.save()
        self.phase_1.force_best_submission_to_leaderboard = True
        self.phase_1.save()
        SubmissionScore.objects.create(
            result=self.submission_4,
            scoredef=self.score_def,
            value=125,
        )
        self.submission_4.execution_key = json.dumps({'score': 125})
        self.submission_4.save()

        zip_buffer = StringIO.StringIO()
        zip_name = "{0}.zip".format('submission_output')
        zip_file = zipfile.ZipFile(zip_buffer, "w")

        zip_file.writestr('scores.txt', 'key: 150\n')

        zip_file.close()

        self.submission_4.output_file.save(zip_name, ContentFile(zip_buffer.getvalue()))
        self.submission_4.save()

        print("SUBMISSION SECRET IS {}".format(self.submission_4.secret))

        task_args = {
            'submission_id': self.submission_4.id
        }
        json_task_args = json.dumps(task_args)
        new_job = Job.objects.create(task_args_json=json_task_args, task_type='evaluate_submission')

        with mock.patch('apps.web.tasks.score') as mock_score:
            update_submission(new_job.id, {'status': 'finished'}, str(self.submission_4.secret))

        assert not PhaseLeaderBoardEntry.objects.filter(board=self.leader_board, result=self.submission_4)
