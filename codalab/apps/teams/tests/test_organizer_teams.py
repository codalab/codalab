
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse

from apps.web.models import Competition
from apps.teams.models import Team, TeamStatus, TeamMembershipStatus

User = get_user_model()


class CompetitionOrganizerTeamsTests(TestCase):
    def setUp(self):
        self.creator = User.objects.create(email='test@user.com', username='testuser')
        self.creator.set_password('test')
        self.creator.save()

        self.admin = User.objects.create(email='testadmin@user.com', username='testadminuser')
        self.admin.set_password('testadmin')
        self.admin.save()

        self.user = User.objects.create(email='testclient@user.com', username='testclientuser')
        self.user.set_password('testclient')
        self.user.save()

        self.competition = Competition.objects.create(creator=self.creator, modified_by=self.creator)
        self.competition.admins.add(self.admin)
        self.competition.save()

        team_status = [("Denied", "denied", "Team was denied."),
                       ("Approved", "approved", "Team was approved."),
                       ("Pending", "pending", "Team is pending approval."),
                       ("Deleted", "deleted", "Team has been deleted.")]

        for name, codename, description in team_status:
            _, _ = TeamStatus.objects.get_or_create(name=name, codename=codename, description=description)

            team_membership_status = [("Rejected", "rejected", "User membership rejected."),
                                      ("Approved", "approved", "User membership approved."),
                                      ("Pending", "pending", "User membership is pending approval."),
                                      ("Canceled", "canceled", "User membership canceled.")]

        for name, codename, description in team_membership_status:
            _, _ = TeamMembershipStatus.objects.get_or_create(name=name, codename=codename,
                                                              description=description)

    # def test_organizer_teams_permissions(self):
    def test_organizer_teams_competition_creator_can_create_teams(self):
        # Creator and Admin should be allowed.
        self.client.login(username='testuser', password='test')

        resp = self.client.post(
            reverse('create_org_team', kwargs={
                'competition_pk': self.competition.pk
            }),
            {"text_members": "test@user.com", "name": "Test Team 1", "description": "Test Team"}
        )

        assert resp.status_code == 302
        assert resp.url == '/my/competition/1/participants/'

    def test_organizer_teams_competition_admin_can_create_teams(self):
        self.client.login(username='testadminuser', password='testadmin')

        resp = self.client.post(
            reverse('create_org_team', kwargs={
                'competition_pk': self.competition.pk
            }),
            {"text_members": "testadmin@user.com", "name": "Test Team 3", "description": "Test Team"}
        )

        assert resp.status_code == 302
        assert resp.url == '/my/competition/1/participants/'

    def test_organizer_teams_regular_user_cannot_create_teams(self):
        # Random users should not be allowed, nor anonymous users
        self.client.login(username='testclientuser', password='testclient')

        resp = self.client.post(
            reverse('create_org_team', kwargs={
                'competition_pk': self.competition.pk
            }),
            {"text_members": "testclient@user.com", "name": "Test Team 2", "description": "Test Team"}
        )

        assert resp.status_code == 403

    def test_organizer_teams_random_user_cannot_create_teams(self):
        resp = self.client.post(
            reverse('create_org_team', kwargs={
                'competition_pk': self.competition.pk
            }),
            {"text_members": "testadmin@user.com", "name": "Test Team 4", "description": "Test Team"}
        )

        assert resp.status_code == 302
        assert resp.url == '/accounts/login/?next=/teams/1/create_org_team/'

    def test_organizer_team_form_with_creator(self):
        self.client.login(username='testuser', password='test')

        resp = self.client.post(
            reverse('create_org_team', kwargs={
                'competition_pk': self.competition.pk
            }),
            {"text_members": "test@user.com", "name": "Test Team 1", "description": "Test Team"}
        )

        assert resp.status_code == 302
        # Make sure new team was created
        new_team = Team.objects.get(name="Test Team 1", description="Test Team")

        assert self.creator in new_team.members.all()

        resp = self.client.post(
            reverse('edit_org_team',kwargs={
                'competition_pk': self.competition.pk, 'pk': new_team.pk
            }),
            {"text_members": "test@user.com", "name": "Test Team 1", "description": "Test Team"}
        )

        assert resp.status_code == 302
        other_teams = Team.objects.all().exclude(pk=new_team.pk)
        # Make sure we still only have one instance
        assert not other_teams
        # Make sure we can still grab it by the same name and description. We didnt change anything.
        new_team = Team.objects.get(name="Test Team 1", description="Test Team")

        resp = self.client.post(
            reverse('edit_org_team', kwargs={
                'competition_pk': self.competition.pk, 'pk': new_team.pk
            }),
            {"text_members": "test@user.com", "name": "Test Team @@@", "description": "Test Team @@@"}
        )

        assert resp.status_code == 302
        new_team = Team.objects.get(name="Test Team @@@", description="Test Team @@@")
        # Make sure we can grab it by the new name and description.
        # We should still have the creator as a member
        assert self.creator in new_team.members.all()

        resp = self.client.post(
            reverse('edit_org_team',kwargs={
                'competition_pk': self.competition.pk, 'pk': new_team.pk
            }),
            {"text_members": "test@user.com, testclientuser", "name": "Test Team @@@", "description": "Test Team @@@"}
        )

        assert resp.status_code == 302
        new_team = Team.objects.get(name="Test Team @@@", description="Test Team @@@")
        # Make sure we can grab it by the new name and description.
        # We should still have the creator as a member, and now a regular user
        assert self.creator in new_team.members.all()
        assert self.user in new_team.members.all()

        # Create a new team with our creator as a member. This should remove us from the first team.
        resp = self.client.post(
            reverse('create_org_team', kwargs={
                'competition_pk': self.competition.pk
            }),
            {"text_members": "test@user.com", "name": "@@@Test@@@", "description": "@@@Test@@@"}
        )

        assert resp.status_code == 302
        new_team_to_leave_for = Team.objects.get(name="@@@Test@@@", description="@@@Test@@@")
        # Check that our creator got removed from the first team, and added to the second.
        assert self.creator not in new_team.members.all()
        assert self.creator in new_team_to_leave_for.members.all()

    def test_organizer_teams_csv_file_form(self):
        test_csv = SimpleUploadedFile(
            "test_team.csv",
            "Team 1, test@user.com, team_member2, team_member3\nTeam 2, team_member_1, team_member_2".encode('utf-8'),
            content_type='multipart/form-data'
        )

        creator = self.client
        creator.login(username='testuser', password='test')

        resp = creator.post(
            reverse('create_org_teams_from_csv', kwargs={
                'competition_pk': self.competition.pk
            }),
            {"csv_file": test_csv}
        )
        assert resp.status_code == 302
        assert resp.url == '/my/competition/1/participants/'

        new_team = Team.objects.get(name="Team 1", description="Team 1")
        print("NEW MEMBERS: {}".format(new_team.members.all()))
        # Make sure we can grab it by the new name and description.
        # We should still have the creator as a member
        assert self.creator in new_team.members.all()

        resp = creator.post(
            reverse('edit_org_team', kwargs={
                'competition_pk': self.competition.pk, 'pk': new_team.pk
            }),
            {"text_members": "test@user.com, testclientuser", "name": "Test Team @@@", "description": "Test Team @@@"}
        )

        assert resp.status_code == 302
        assert resp.url == '/my/competition/1/participants/'

        new_team = Team.objects.get(name="Test Team @@@", description="Test Team @@@")
        assert self.creator in new_team.members.all()
        assert self.user in new_team.members.all()

        test_csv_two = SimpleUploadedFile(
            "test_team.csv",
            "Team 1, test@user.com, team_member2, team_member3\n".encode('utf-8'),
            content_type='multipart/form-data'
        )

        resp = creator.post(
            reverse('create_org_teams_from_csv', kwargs={
                'competition_pk': self.competition.pk
            }),
            {"csv_file": test_csv_two}
        )

        assert resp.status_code == 302
        assert resp.url == '/my/competition/1/participants/'

        new_team = Team.objects.get(name="Team 1", description="Team 1")
        # Make sure we can grab it by the new name and description.
        # We should still have the creator as a member
        assert self.creator in new_team.members.all()

        test_csv_three = SimpleUploadedFile(
            "test_team.csv",
            "Team 1, team_member2, team_member3\n".encode('utf-8'),
            content_type='multipart/form-data'
        )

        resp = creator.post(
            reverse('create_org_teams_from_csv', kwargs={
                'competition_pk': self.competition.pk
            }),
            {"csv_file": test_csv_three}
        )

        assert resp.status_code == 302
        assert resp.url == '/my/competition/1/participants/'

        new_team = Team.objects.get(name="Team 1", description="Team 1")
        # Make sure we can grab it by the new name and description.
        # We should not have the creator as a member
        assert self.creator not in new_team.members.all()

    def test_organizer_teams_competition_creator_can_delete_teams(self):
        new_team = Team.objects.create(
            name="Test Team!", description="Test Team!",
            competition=self.competition,
            creator=self.creator,
            allow_requests=False,
            status=TeamStatus.objects.get(codename=TeamStatus.APPROVED)
        )

        self.client.login(username='testuser', password='test')

        resp = self.client.post(
            reverse(
                'delete_org_team',
                kwargs={
                    'competition_pk': self.competition.pk,
                    'team_pk': new_team.pk
                }
            )
        )

        assert resp.status_code == 302
        assert resp.url == '/my/competition/1/participants/'

    def test_organizer_teams_competition_admin_can_delete_teams(self):
        new_team = Team.objects.create(
            name="Test Team!", description="Test Team!",
            competition=self.competition,
            creator=self.creator,
            allow_requests=False,
            status=TeamStatus.objects.get(codename=TeamStatus.APPROVED)
        )

        self.client.login(username='testadminuser', password='testadmin')

        resp = self.client.post(
            reverse(
                'delete_org_team',
                kwargs={
                    'competition_pk': self.competition.pk,
                    'team_pk': new_team.pk
                }
            )
        )

        assert resp.status_code == 302
        assert resp.url == '/my/competition/1/participants/'

    def test_organizer_teams_regular_user_cannot_delete_teams(self):
        new_team = Team.objects.create(
            name="Test Team!", description="Test Team!",
            competition=self.competition,
            creator=self.creator,
            allow_requests=False,
            status=TeamStatus.objects.get(codename=TeamStatus.APPROVED)
        )

        self.client.login(username='testclientuser', password='testclient')

        resp = self.client.post(
            reverse(
                'delete_org_team',
                kwargs={
                    'competition_pk': self.competition.pk,
                    'team_pk': new_team.pk
                }
            )
        )

        assert resp.status_code == 403

    def test_organizer_teams_random_user_cannot_delete_teams(self):
        new_team = Team.objects.create(
            name="Test Team!", description="Test Team!",
            competition=self.competition,
            creator=self.creator,
            allow_requests=False,
            status=TeamStatus.objects.get(codename=TeamStatus.APPROVED)
        )

        resp = self.client.post(
            reverse(
                'delete_org_team',
                kwargs={
                    'competition_pk': self.competition.pk,
                    'team_pk': new_team.pk
                }
            )
        )

        assert resp.status_code == 302
        assert resp.url == '/accounts/login/?next=/teams/1/delete_org_team/1'

    def test_organizer_teams_test_allowed_methods_for_delete(self):
        new_team = Team.objects.create(
            name="Test Team!", description="Test Team!",
            competition=self.competition,
            creator=self.creator,
            allow_requests=False,
            status=TeamStatus.objects.get(codename=TeamStatus.APPROVED)
        )

        self.client.login(username='testuser', password='test')

        resp = self.client.get(
            reverse(
                'delete_org_team',
                kwargs={
                    'competition_pk': self.competition.pk,
                    'team_pk': new_team.pk
                }
            )
        )

        assert resp.status_code == 405

        resp = self.client.post(
            reverse(
                'delete_org_team',
                kwargs={
                    'competition_pk': self.competition.pk,
                    'team_pk': new_team.pk
                }
            )
        )

        assert resp.status_code == 302
        assert resp.url == '/my/competition/1/participants/'
