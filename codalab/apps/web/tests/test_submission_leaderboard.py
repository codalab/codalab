import datetime
# from apps.jobs.models import Job
from apps.web.models import (Competition,
                             CompetitionParticipant,
                             CompetitionPhase,
                             CompetitionSubmission,
                             CompetitionSubmissionStatus,
                             ParticipantStatus,
                             PhaseLeaderBoard,
                             PhaseLeaderBoardEntry,
                             add_submission_to_leaderboard, SubmissionResultGroup, SubmissionResultGroupPhase,
                             SubmissionScoreDef, SubmissionScoreDefGroup, SubmissionScore, SubmissionScoreSet,
                             SubmissionComputedScore, SubmissionComputedScoreField)
# from apps.web.tasks import update_submission
from apps.web.utils import push_submission_to_leaderboard_if_best
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test.client import Client

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

        self.phase_1.reference_data.save('test-file.txt', ContentFile("This is some fake reference data".encode('utf-8')))
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
            label="Test \u2020",
            ordering=1
        )
        self.submission_result_group_phase = SubmissionResultGroupPhase.objects.create(phase=self.phase_1, group=self.result_group)
        self.score_def = SubmissionScoreDef.objects.create(
            competition=self.competition,
            key="Key",
            label="Test \u2020",
            sorting='desc',
        )
        self.score_def_2 = SubmissionScoreDef.objects.create(
            competition=self.competition,
            key="TestKey2",  # avoids conflict with Key2 below
            label=u"Test2 \u2020",
            sorting='desc',
        )

        SubmissionScoreDefGroup.objects.create(scoredef=self.score_def, group=self.result_group)
        SubmissionScoreDefGroup.objects.create(scoredef=self.score_def_2, group=self.result_group)
        SubmissionScore.objects.create(result=self.submission_1, scoredef=self.score_def, value=123)
        SubmissionScore.objects.create(result=self.submission_2, scoredef=self.score_def, value=120)

        SubmissionScoreSet.objects.create(competition=self.competition, key="Key", label=u"Test \u2020", scoredef=self.score_def)
        SubmissionScoreSet.objects.create(competition=self.competition, key="TestKey2", label=u"Test2 \u2020", scoredef=self.score_def_2)

        # Weights additions
        self.weighted_score_def = SubmissionScoreDef.objects.create(
            competition=self.competition,
            key="WeightedKey",
            label=u"Weighted Test \u2020",
            sorting='desc',
            computed=True,
        )
        SubmissionScoreDefGroup.objects.create(scoredef=self.weighted_score_def, group=self.result_group)
        SubmissionScoreSet.objects.create(competition=self.competition, key="WeightedKey", label=u"Test \u2020", scoredef=self.weighted_score_def)
        self.weighted_submission_computed_score = SubmissionComputedScore.objects.create(
            scoredef=self.weighted_score_def,
            operation="Avg",
            weights="0.8, 0.2"
        )
        weighted_fields = (self.score_def, self.score_def_2)
        for f in weighted_fields:
            SubmissionComputedScoreField.objects.get_or_create(computed=self.weighted_submission_computed_score, scoredef=f)

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
        self.toggle_url = reverse("competitions:submission_toggle_leaderboard",
                                  kwargs={"submission_pk": self.submission_1.pk})

    def test_toggle_leaderboard_returns_404_if_not_competition_owner(self):
        self.client.login(username="other", password="pass")
        resp = self.client.post(self.toggle_url)
        self.assertEqual(resp.status_code, 404)

    def test_toggle_leaderboard_returns_404_if_participant_not_owner(self):
        self.client.login(username="participant", password="pass")
        resp = self.client.post(self.toggle_url)
        self.assertEqual(resp.status_code, 404)

    def test_toggle_leaderboard_returns_200_and_removes_submission_from_leaderboard(self):
        add_submission_to_leaderboard(self.submission_1)
        self.client.login(username="organizer", password="pass")
        resp = self.client.post(self.toggle_url)
        self.assertEqual(resp.status_code, 200)
        submission_exists_on_leaderboard = PhaseLeaderBoardEntry.objects.filter(
            result=self.submission_1
        ).exists()
        self.assertFalse(submission_exists_on_leaderboard)

        # Make sure the other submission remains untouched
        self.assertTrue(PhaseLeaderBoardEntry.objects.get(result=self.submission_2))

    def test_toggle_leaderboard_returns_200_and_adds_submission_to_leaderboard(self):
        self.client.login(username="organizer", password="pass")
        resp = self.client.post(self.toggle_url)
        self.assertEqual(resp.status_code, 200)
        submission_exists_on_leaderboard = PhaseLeaderBoardEntry.objects.filter(
            board=self.leader_board,
            result=self.submission_1
        )
        assert not submission_exists_on_leaderboard
        # The submission is automatically added due to the setup for the competition. So we re-toggle to remove it
        resp = self.client.post(self.toggle_url)
        self.assertEqual(resp.status_code, 200)
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
        self.assertEqual(resp.status_code, 400)

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
        push_submission_to_leaderboard_if_best(self.submission_4)

        assert PhaseLeaderBoardEntry.objects.filter(board=self.leader_board, result=self.submission_4)

    def test_submission_scoring_forced_best_to_leaderboard_does_not_put_lower_score_on_leaderboard_when_descending(
            self):
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
        push_submission_to_leaderboard_if_best(self.submission_4)

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
        push_submission_to_leaderboard_if_best(self.submission_4)

        assert PhaseLeaderBoardEntry.objects.filter(board=self.leader_board, result=self.submission_4)

    def test_submission_scoring_forced_best_to_leaderboard_does_not_put_higher_score_on_leaderboard_when_ascending(
            self):
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
        push_submission_to_leaderboard_if_best(self.submission_4)

        assert not PhaseLeaderBoardEntry.objects.filter(board=self.leader_board, result=self.submission_4)

    def test_submission_scoring_forced_best_to_leaderboard_exact_conditions(self):
        self.competition.force_submission_to_leaderboard = True
        self.competition.disallow_leaderboard_modifying = True
        self.competition.save()
        self.phase_1.force_best_submission_to_leaderboard = True
        self.phase_1.save()

        # Score def 2
        self.result_group2 = SubmissionResultGroup.objects.create(competition=self.competition, key="Key2", label="Test2 \u2020", ordering=2)
        self.submission_result_group_phase = SubmissionResultGroupPhase.objects.create(phase=self.phase_1, group=self.result_group2)
        self.score_def2 = SubmissionScoreDef.objects.create(competition=self.competition, key="Key2", label="Test2 \u2020", sorting='desc', ordering=2)
        SubmissionScoreDefGroup.objects.create(scoredef=self.score_def2, group=self.result_group2)

        # Score def 3
        self.resultgroup3 = SubmissionResultGroup.objects.create(competition=self.competition, key="Key3", label="Test3 \u2020", ordering=3)
        self.submission_result_group_phase = SubmissionResultGroupPhase.objects.create(phase=self.phase_1, group=self.resultgroup3)
        self.score_def3 = SubmissionScoreDef.objects.create(competition=self.competition, key="Key3", label="Test3 \u2020", sorting='asc', ordering=3)
        SubmissionScoreDefGroup.objects.create(scoredef=self.score_def3, group=self.resultgroup3)

        # Score def 4
        self.resultgroup4 = SubmissionResultGroup.objects.create(competition=self.competition, key="Key4", label="Test4 \u2020", ordering=4)
        self.submission_result_group_phase = SubmissionResultGroupPhase.objects.create(phase=self.phase_1, group=self.resultgroup4)
        self.score_def4 = SubmissionScoreDef.objects.create(competition=self.competition, key="Key4", label="Test4 \u2020", sorting='asc', ordering=4)
        SubmissionScoreDefGroup.objects.create(scoredef=self.score_def4, group=self.resultgroup4)

        # Score def 5
        self.resultgroup5 = SubmissionResultGroup.objects.create(competition=self.competition, key="Key5", label="Test5 \u2020", ordering=5)
        self.submission_result_group_phase = SubmissionResultGroupPhase.objects.create(phase=self.phase_1, group=self.resultgroup5)
        self.score_def5 = SubmissionScoreDef.objects.create(competition=self.competition, key="Key5", label="Test5 \u2020", sorting='desc', ordering=5)
        SubmissionScoreDefGroup.objects.create(scoredef=self.score_def5, group=self.resultgroup5)

        # Score def 6
        self.resultgroup6 = SubmissionResultGroup.objects.create(competition=self.competition, key="Key6", label="Test6 \u2020", ordering=6)
        self.submission_result_group_phase = SubmissionResultGroupPhase.objects.create(phase=self.phase_1, group=self.resultgroup6)
        self.score_def6 = SubmissionScoreDef.objects.create(competition=self.competition, key="Key6", label="Test6 \u2020", sorting='desc', ordering=6)
        SubmissionScoreDefGroup.objects.create(scoredef=self.score_def6, group=self.resultgroup6)

        # score def 7
        self.resultgroup7 = SubmissionResultGroup.objects.create(competition=self.competition, key="Key7", label="Test7 \u2020", ordering=7)
        self.submission_result_group_phase = SubmissionResultGroupPhase.objects.create(phase=self.phase_1, group=self.resultgroup7)
        self.score_def7 = SubmissionScoreDef.objects.create(competition=self.competition, key="Key7", label="Test7 \u2020", sorting='desc', ordering=7)
        SubmissionScoreDefGroup.objects.create(scoredef=self.score_def7, group=self.resultgroup7)

        submission_finished = CompetitionSubmissionStatus.objects.get(name="finished", codename="finished")

        self.sub_test = CompetitionSubmission.objects.create(
            participant=self.participant_1,
            phase=self.phase_1,
            status=submission_finished,
            submitted_at=datetime.datetime.now() - datetime.timedelta(days=29)
        )
        SubmissionScore.objects.create(result=self.sub_test, scoredef=self.score_def, value=float(1.0510))
        SubmissionScore.objects.create(result=self.sub_test, scoredef=self.score_def2, value=0.5)
        SubmissionScore.objects.create(result=self.sub_test, scoredef=self.score_def3, value=1.0)
        SubmissionScore.objects.create(result=self.sub_test, scoredef=self.score_def4, value=1.0)
        SubmissionScore.objects.create(result=self.sub_test, scoredef=self.score_def5, value=1.0)
        SubmissionScore.objects.create(result=self.sub_test, scoredef=self.score_def6, value=1.0)
        SubmissionScore.objects.create(result=self.sub_test, scoredef=self.score_def7, value=1.0)

        add_submission_to_leaderboard(self.sub_test)

        print(PhaseLeaderBoardEntry.objects.filter(board=self.leader_board,
                                                   result__participant=self.participant_1).first().result)

        self.sub_test_two = CompetitionSubmission.objects.create(
            participant=self.participant_1,
            phase=self.phase_1,
            status=submission_finished,
            submitted_at=datetime.datetime.now() - datetime.timedelta(days=29)
        )
        SubmissionScore.objects.create(result=self.sub_test_two, scoredef=self.score_def, value=float(1.0533))
        SubmissionScore.objects.create(result=self.sub_test_two, scoredef=self.score_def2, value=0.4)
        SubmissionScore.objects.create(result=self.sub_test_two, scoredef=self.score_def3, value=0.65)
        SubmissionScore.objects.create(result=self.sub_test_two, scoredef=self.score_def4, value=0.65)
        SubmissionScore.objects.create(result=self.sub_test_two, scoredef=self.score_def5, value=0.65)
        SubmissionScore.objects.create(result=self.sub_test_two, scoredef=self.score_def6, value=0.65)
        SubmissionScore.objects.create(result=self.sub_test_two, scoredef=self.score_def7, value=0.65)

        push_submission_to_leaderboard_if_best(self.sub_test_two)
        # result__participant = self.participant_1).first().result)
        assert PhaseLeaderBoardEntry.objects.filter(board=self.leader_board, result=self.sub_test_two)

    def test_weighted_scores_calculations(self):
        self.leader_board_entry_1.result = self.submission_4
        self.leader_board_entry_1.save()

        SubmissionScore.objects.create(
            result=self.submission_4,
            scoredef=self.score_def,
            value=100,
        )
        SubmissionScore.objects.create(
            result=self.submission_4,
            scoredef=self.score_def_2,
            value=100,
        )

        scores = self.phase_1.scores()[0]['scores']
        organizer_score = scores[0][1]
        participant_score = scores[1][1]

        # these vals correspond to: score 1, score 2, and the weighted scores (weights = 0.8 and 0.2)
        assert organizer_score['values'][0]['val'] == '120.0'
        assert organizer_score['values'][1]['val'] == '-'
        assert organizer_score['values'][2]['val'] == '1.2'

        assert participant_score['values'][0]['val'] == '100.0'
        assert participant_score['values'][1]['val'] == '100.0'
        assert participant_score['values'][2]['val'] == '1.8'
