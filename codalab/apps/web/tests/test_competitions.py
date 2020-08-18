import io
import zipfile

import mock
import pytz
from django.core.files.base import ContentFile

from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test.client import Client
from django.contrib.auth import get_user_model
from django.utils.timezone import now, timedelta, datetime

from apps.web.models import (Competition,
                             CompetitionParticipant,
                             CompetitionPhase,
                             CompetitionSubmission,
                             CompetitionSubmissionStatus,
                             ParticipantStatus,
                             PhaseLeaderBoard,
                             PhaseLeaderBoardEntry, CompetitionDump, get_first_previous_active_and_next_phases)

User = get_user_model()


class CompetitionPhaseToPhase(TestCase):
    def setUp(self):
        self.user = User.objects.create(email='test@user.com', username='testuser')
        self.other_user = User.objects.create(email='other@user.com', username='other')
        self.competition = Competition.objects.create(creator=self.user, modified_by=self.user)
        self.participant_1 = CompetitionParticipant.objects.create(
            user=self.user,
            competition=self.competition,
            status=ParticipantStatus.objects.get_or_create(name='approved', codename=ParticipantStatus.APPROVED)[0]
        )
        self.participant_2 = CompetitionParticipant.objects.create(
            user=self.other_user,
            competition=self.competition,
            status=ParticipantStatus.objects.get_or_create(name='approved', codename=ParticipantStatus.APPROVED)[0]
        )
        self.phase_1 = CompetitionPhase.objects.create(
            competition=self.competition,
            phasenumber=1,
            start_date=datetime.datetime.now() - datetime.timedelta(days=30),
        )
        self.phase_2 = CompetitionPhase.objects.create(
            competition=self.competition,
            phasenumber=2,
            start_date=datetime.datetime.now() - datetime.timedelta(days=15),
            auto_migration=True
        )

        submission_finished = CompetitionSubmissionStatus.objects.create(name="finished", codename="finished")

        self.submission_1 = CompetitionSubmission.objects.create(
            participant=self.participant_1,
            phase=self.phase_1,
            status=submission_finished,
            submitted_at=datetime.datetime.now() - datetime.timedelta(days=29)
        )
        self.submission_2 = CompetitionSubmission.objects.create(
            participant=self.participant_1,
            phase=self.phase_1,
            status=submission_finished,
            submitted_at=datetime.datetime.now() - datetime.timedelta(days=28)
        )

        self.submission_3 = CompetitionSubmission.objects.create(
            participant=self.participant_2,
            phase=self.phase_1,
            status=submission_finished,
            submitted_at=datetime.datetime.now() - datetime.timedelta(days=28)
        )

        self.leader_board = PhaseLeaderBoard.objects.create(phase=self.phase_1)
        self.leader_board_entry_1 = PhaseLeaderBoardEntry.objects.create(
            board=self.leader_board,
            result=self.submission_2
        )
        self.leader_board_entry_2 = PhaseLeaderBoardEntry.objects.create(
            board=self.leader_board,
            result=self.submission_3
        )

        self.client = Client()

    # TODO, FIX TEXT cases
    # def test_phase_migrations_works_even_with_max_submissions(self):
    #     self.phase_1.max_submissions_per_day = 3
    #     self.phase_1.save()
    #     self.phase_2.max_submissions_per_day = 1
    #     self.phase_2.save()

    #     with mock.patch('apps.web.tasks.evaluate_submission') as evaluate_mock:
    #         self.competition.check_future_phase_sumbmissions()

    #     # The submissions still made it
    #     CompetitionSubmission.objects.get(phase=self.phase_2, participant=self.participant_1)
    #     CompetitionSubmission.objects.get(phase=self.phase_2, participant=self.participant_2)

    #     # And the competition is not stuck migrating
    #     self.assertEquals(self.competition.last_phase_migration, 2)
    #     self.assertTrue(CompetitionPhase.objects.get(pk=self.phase_2.pk).is_migrated)
    #     self.assertFalse(self.competition.is_migrating)

    # def test_phase_migrations_delayed_until_submissions_not_marked_running(self):
    #     self.submission_1.status = CompetitionSubmissionStatus.objects.get_or_create(name="running", codename="running")[0]
    #     self.submission_1.save()
    #     with mock.patch('apps.web.tasks.evaluate_submission') as evaluate_mock:
    #         self.competition.check_future_phase_sumbmissions()
    #     self.assertFalse(evaluate_mock.called)

    #     self.submission_1.status = CompetitionSubmissionStatus.objects.get_or_create(name="finished", codename="finished")[0]
    #     self.submission_1.save()
    #     PhaseLeaderBoardEntry.objects.create(
    #         board=self.leader_board,
    #         result=self.submission_1
    #     )
    #     with mock.patch('apps.web.tasks.evaluate_submission') as evaluate_mock:
    #         self.competition.check_future_phase_sumbmissions()
    #     self.assertTrue(evaluate_mock.called)

    # def test_phase_migrations_handles_delay_with_failed_submissions(self):
    #     self.submission_1.status = CompetitionSubmissionStatus.objects.get_or_create(name="running", codename="running")[0]
    #     self.submission_1.save()
    #     with mock.patch('apps.web.tasks.evaluate_submission') as evaluate_mock:
    #         self.competition.check_future_phase_sumbmissions()
    #     self.assertFalse(evaluate_mock.called)

    #     self.submission_1.status = CompetitionSubmissionStatus.objects.get_or_create(name="failed", codename="failed")[0]
    #     self.submission_1.save()
    #     with mock.patch('apps.web.tasks.evaluate_submission') as evaluate_mock:
    #         self.competition.check_future_phase_sumbmissions()
    #     self.assertTrue(evaluate_mock.called)

    # def test_phase_migrations_delayed_marks_competition(self):
    #     self.submission_1.status = CompetitionSubmissionStatus.objects.get_or_create(name="running", codename="running")[0]
    #     self.submission_1.save()
    #     self.assertFalse(self.competition.is_migrating_delayed)
    #     with mock.patch('apps.web.tasks.evaluate_submission') as evaluate_mock:
    #         self.competition.check_future_phase_sumbmissions()
    #     self.assertFalse(self.competition.is_migrating_delayed)


class CompetitionTest(TestCase):

    def setUp(self):
        self.organizer_user = User.objects.create_user(username="organizer", password="pass")
        self.participant_user = User.objects.create_user(username="participant", password="pass")
        self.competition = Competition.objects.create(
            title="Test Competition",
            creator=self.organizer_user,
            modified_by=self.organizer_user
        )
        self.participant = CompetitionParticipant.objects.create(
            user=self.participant_user,
            competition=self.competition,
            status=ParticipantStatus.objects.get_or_create(name='approved', codename=ParticipantStatus.PENDING)[0]
        )


class CompetitionDeleteTests(CompetitionTest):

    def test_cant_view_delete_competition_template_if_you_dont_own_it(self):
        self.client.login(username="participant", password="pass")
        resp = self.client.get(reverse("competitions:delete", kwargs={"pk": self.competition.pk}))

        self.assertEqual(resp.status_code, 403)

    def test_can_view_delete_competition_with_ownership(self):
        self.client.login(username="organizer", password="pass")
        resp = self.client.get(reverse("competitions:delete", kwargs={"pk": self.competition.pk}))

        self.assertEqual(resp.status_code, 200)

    def test_cant_delete_competition_even_as_admin(self):
        some_admin = User.objects.create_user(username="some_admin", password="pass")
        self.client.logout()
        self.client.login(username="some_admin", password="pass")
        self.competition.admins.add(some_admin)
        self.competition.save()
        resp = self.client.get(reverse("competitions:delete", kwargs={"pk": self.competition.pk}))
        self.assertEqual(resp.status_code, 403)

    def test_cant_delete_competition_if_you_dont_own_it(self):
        self.client.login(username="participant", password="pass")
        resp = self.client.delete(reverse("competitions:delete", kwargs={"pk": self.competition.pk}))

        self.assertEqual(resp.status_code, 403)

    def test_can_delete_competition_with_ownership(self):
        self.client.login(username="organizer", password="pass")
        resp = self.client.delete(reverse("competitions:delete", kwargs={"pk": self.competition.pk}))

        self.assertEqual(resp.status_code, 302)
        self.assertEqual(len(Competition.objects.filter(pk=self.competition.pk)), 0)


class CompetitionDumpDeleteTests(CompetitionTest):

    def setUp(self):
        super(CompetitionDumpDeleteTests, self).setUp()
        zip_buffer = io.BytesIO()
        zip_name = "{0}.zip".format("Example_Title")
        zip_file = zipfile.ZipFile(zip_buffer, "w")
        zip_file.close()
        temp_comp_data = ContentFile(zip_buffer.getvalue())
        self.competitiondump = CompetitionDump.objects.create(
            competition=self.competition,
            status="Finished",
        )
        self.competitiondump.data_file.save(zip_name, temp_comp_data)

    def test_cant_view_delete_competition_template_if_you_dont_own_it(self):
        self.client.login(username="participant", password="pass")
        resp = self.client.get(reverse("competitions:delete_dump", kwargs={"pk": self.competitiondump.pk}))

        self.assertEqual(resp.status_code, 403)

    def test_can_view_delete_competition_with_ownership(self):
        self.client.login(username="organizer", password="pass")
        resp = self.client.get(reverse("competitions:delete_dump", kwargs={"pk": self.competitiondump.pk}))

        self.assertEqual(resp.status_code, 200)

    def test_cant_delete_competition_if_you_dont_own_it(self):
        self.client.login(username="participant", password="pass")
        resp = self.client.delete(reverse("competitions:delete_dump", kwargs={"pk": self.competitiondump.pk}))

        self.assertEqual(resp.status_code, 403)

    def test_can_delete_competition_with_ownership(self):
        self.client.login(username="organizer", password="pass")
        resp = self.client.delete(reverse("competitions:delete_dump", kwargs={"pk": self.competitiondump.pk}))

        self.assertEqual(resp.status_code, 302)
        self.assertEqual(len(CompetitionDump.objects.filter(pk=self.competitiondump.pk)), 0)

    def test_can_delete_competition_dump_with_admin(self):
        some_admin = User.objects.create_user(username="some_admin", password="pass")
        self.client.logout()
        self.client.login(username="some_admin", password="pass")
        self.competition.admins.add(some_admin)
        self.competition.save()
        resp = self.client.delete(reverse("competitions:delete_dump", kwargs={"pk": self.competitiondump.pk}))

        self.assertEqual(resp.status_code, 302)
        self.assertEqual(len(CompetitionDump.objects.filter(pk=self.competitiondump.pk)), 0)


class CompetitionEditPermissionsTests(CompetitionTest):

    def test_cant_view_edit_competition_template_if_you_dont_own_it(self):
        self.client.login(username="participant", password="pass")
        resp = self.client.get(reverse("competitions:edit", kwargs={"pk": self.competition.pk}))

        self.assertEqual(resp.status_code, 403)

    def test_can_view_edit_competition_with_ownership(self):
        self.client.login(username="organizer", password="pass")
        resp = self.client.get(reverse("competitions:edit", kwargs={"pk": self.competition.pk}))

        self.assertEqual(resp.status_code, 200)

    def test_can_view_edit_competition_as_admin(self):
        some_admin = User.objects.create_user(username="some_admin", password="pass")
        self.client.login(username="some_admin", password="pass")
        self.competition.admins.add(some_admin)
        self.competition.save()
        resp = self.client.get(reverse("competitions:edit", kwargs={"pk": self.competition.pk}))

        self.assertEqual(resp.status_code, 200)

    def test_cant_edit_competition_if_you_dont_own_it(self):
        self.client.login(username="participant", password="pass")
        resp = self.client.post(reverse("competitions:edit", kwargs={"pk": self.competition.pk}))

        self.assertEqual(resp.status_code, 403)

    def test_can_edit_competition_with_ownership(self):
        self.client.login(username="organizer", password="pass")
        with mock.patch('apps.web.views.CompetitionEdit.construct_inlines') as construct_inlines_mock:
            resp = self.client.post(
                reverse("competitions:edit", kwargs={"pk": self.competition.pk}),
                data={}
            )

        self.assertTrue(construct_inlines_mock.called)


class CompetitionCurrentPhaseHandling(TestCase):
    def setUp(self):
        self.user = User.objects.create(email='test@user.com', username='testuser')
        self.competition = Competition.objects.create(
            creator=self.user,
            modified_by=self.user,
            end_date=now() + timedelta(days=30)
        )
        self.participant_1 = CompetitionParticipant.objects.create(
            user=self.user,
            competition=self.competition,
            status=ParticipantStatus.objects.get_or_create(name='approved', codename=ParticipantStatus.APPROVED)[0]
        )

    def test_get_previous_next_active_phase_works_two_simple_phases(self):
        self.phase_1 = CompetitionPhase.objects.create(
            competition=self.competition,
            phasenumber=1,
            start_date=now() - timedelta(days=30),
        )
        self.phase_2 = CompetitionPhase.objects.create(
            competition=self.competition,
            phasenumber=2,
            start_date=now() - timedelta(days=15),
        )

        first_phase, previous_phase, active_phase, next_phase = get_first_previous_active_and_next_phases(self.competition)
        assert first_phase == self.phase_1
        assert previous_phase == self.phase_1
        assert active_phase == self.phase_2
        assert next_phase is None

    def test_get_previous_next_active_phase_works_many_phases(self):
        self.phase_1 = CompetitionPhase.objects.create(
            competition=self.competition,
            phasenumber=1,
            start_date=now() - timedelta(days=30),
        )
        self.phase_2 = CompetitionPhase.objects.create(
            competition=self.competition,
            phasenumber=2,
            start_date=now() - timedelta(days=15),
        )
        self.phase_3 = CompetitionPhase.objects.create(
            competition=self.competition,
            phasenumber=3,
            start_date=now() - timedelta(days=5),
        )
        self.phase_4 = CompetitionPhase.objects.create(
            competition=self.competition,
            phasenumber=4,
            start_date=now() + timedelta(days=15),
        )

        first_phase, previous_phase, active_phase, next_phase = get_first_previous_active_and_next_phases(self.competition)
        assert first_phase == self.phase_1
        assert previous_phase == self.phase_2
        assert active_phase == self.phase_3
        assert next_phase == self.phase_4

    def test_get_previous_next_active_phase_works_no_next_phase_competition_ends(self):
        self.phase_1 = CompetitionPhase.objects.create(
            competition=self.competition,
            phasenumber=1,
            start_date=now() - timedelta(days=30),
        )
        self.phase_2 = CompetitionPhase.objects.create(
            competition=self.competition,
            phasenumber=2,
            start_date=now() - timedelta(days=15),
        )
        self.phase_3 = CompetitionPhase.objects.create(
            competition=self.competition,
            phasenumber=3,
            start_date=now() - timedelta(days=5),
        )

        first_phase, previous_phase, active_phase, next_phase = get_first_previous_active_and_next_phases(self.competition)
        assert first_phase == self.phase_1
        assert previous_phase == self.phase_2
        assert active_phase == self.phase_3
        assert next_phase is None

    def test_get_previous_next_active_phase_works_without_neverending_second_phase(self):
        self.phase_1 = CompetitionPhase.objects.create(
            competition=self.competition,
            phasenumber=1,
            start_date=datetime(2017, 6, 18, 23, 59),
        )
        self.phase_2 = CompetitionPhase.objects.create(
            competition=self.competition,
            phasenumber=2,
            start_date=datetime(2017, 6, 30, 23, 59),
        )
        self.phase_3 = CompetitionPhase.objects.create(
            competition=self.competition,
            phasenumber=3,
            start_date=datetime(2018, 5, 13, 23, 59),
        )

        first_phase, previous_phase, active_phase, next_phase = get_first_previous_active_and_next_phases(self.competition)
        assert first_phase == self.phase_1
        assert previous_phase == self.phase_2
        assert active_phase == self.phase_3
        assert next_phase is None

    def test_get_previous_next_active_phase_works_with_neverending_second_phase(self):
        self.phase_1 = CompetitionPhase.objects.create(
            competition=self.competition,
            phasenumber=1,
            start_date=datetime(2017, 6, 18, 23, 59),
        )
        self.phase_2 = CompetitionPhase.objects.create(
            competition=self.competition,
            phasenumber=2,
            start_date=datetime(2017, 6, 30, 23, 59),
            phase_never_ends=True,
        )
        self.phase_3 = CompetitionPhase.objects.create(
            competition=self.competition,
            phasenumber=3,
            start_date=datetime(2018, 5, 13, 23, 59),
        )

        first_phase, previous_phase, active_phase, next_phase = get_first_previous_active_and_next_phases(self.competition)
        assert first_phase == self.phase_1
        assert previous_phase == self.phase_2
        assert active_phase == self.phase_3
        assert next_phase is None

    def test_get_previous_next_active_phase_works_with_competition_that_never_ends(self):
        self.competition.end_date = None
        self.competition.save()

        self.phase_1 = CompetitionPhase.objects.create(
            competition=self.competition,
            phasenumber=1,
            start_date=datetime(2017, 6, 18, 23, 59),
        )
        self.phase_2 = CompetitionPhase.objects.create(
            competition=self.competition,
            phasenumber=2,
            start_date=datetime(2017, 6, 30, 23, 59),
            phase_never_ends=True,
        )
        self.phase_3 = CompetitionPhase.objects.create(
            competition=self.competition,
            phasenumber=3,
            start_date=datetime(2018, 5, 13, 23, 59),
        )

        first_phase, previous_phase, active_phase, next_phase = get_first_previous_active_and_next_phases(self.competition)
        assert first_phase == self.phase_1
        assert previous_phase == self.phase_2
        assert active_phase == self.phase_3
        assert next_phase is None

    def test_get_previous_next_active_phase_works_with_competition_that_has_ended(self):
        self.competition.end_date = datetime(2018, 5, 25, 23, 59, tzinfo=pytz.utc)
        self.competition.save()

        self.phase_1 = CompetitionPhase.objects.create(
            competition=self.competition,
            phasenumber=1,
            start_date=datetime(2017, 6, 18, 23, 59),
        )
        self.phase_2 = CompetitionPhase.objects.create(
            competition=self.competition,
            phasenumber=2,
            start_date=datetime(2017, 6, 30, 23, 59),
        )
        self.phase_3 = CompetitionPhase.objects.create(
            competition=self.competition,
            phasenumber=3,
            start_date=datetime(2018, 5, 13, 23, 59),
        )

        first_phase, previous_phase, active_phase, next_phase = get_first_previous_active_and_next_phases(
            self.competition)
        assert first_phase == self.phase_1
        assert previous_phase == self.phase_3
        assert active_phase is None
        assert next_phase is None

    def test_get_previous_next_active_phase_works_with_competition_that_has_ended_but_has_phase_that_never_ends(self):
        self.competition.end_date = datetime(2018, 5, 25, 23, 59, tzinfo=pytz.utc)
        self.competition.save()

        self.phase_1 = CompetitionPhase.objects.create(
            competition=self.competition,
            phasenumber=1,
            start_date=datetime(2017, 6, 18, 23, 59),
        )
        self.phase_2 = CompetitionPhase.objects.create(
            competition=self.competition,
            phasenumber=2,
            start_date=datetime(2017, 6, 30, 23, 59),
            phase_never_ends=True,
        )
        self.phase_3 = CompetitionPhase.objects.create(
            competition=self.competition,
            phasenumber=3,
            start_date=datetime(2018, 5, 13, 23, 59),
        )

        first_phase, previous_phase, active_phase, next_phase = get_first_previous_active_and_next_phases(
            self.competition)
        assert first_phase == self.phase_1
        assert previous_phase == self.phase_3
        assert active_phase == self.phase_2
        assert next_phase is None
