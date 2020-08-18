
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse

from apps.web.models import Competition, CompetitionParticipant, ParticipantStatus
from apps.teams.models import Team, TeamStatus, get_user_team, TeamMembership

User = get_user_model()


class CompetitionTeamsTests(TestCase):
    def setUp(self):
        self.creator = User.objects.create(email='test@user.com', username='testuser')
        self.creator.set_password('test')
        self.creator.save()

        self.competition = Competition.objects.create(creator=self.creator, modified_by=self.creator)

        # Not sure why this status doesn't exist?
        self.part_status = ParticipantStatus.objects.create(
            name='Approved',
            codename=ParticipantStatus.APPROVED,
            description='Approved',
        )

        self.creator_part = CompetitionParticipant.objects.create(
            user=self.creator,
            competition=self.competition,
            status=self.part_status,
            reason="Creator"
        )

        TeamStatus.objects.get_or_create(name="Pending", codename="pending", description="Team is pending approval.")
        TeamStatus.objects.get_or_create(name="Approved", codename="approved", description="Team was approved")

    def test_organizer_is_member_after_creating_team(self):
        self.client.login(username='testuser', password='test')

        resp = self.client.post(
            reverse('team_new', kwargs={
                'competition_pk': self.competition.pk
            }),
            {'name': "Test Team", 'description': "A team for automated tests!", 'allow_requests': False}
        )

        new_team = Team.objects.first()
        new_team.status = TeamStatus.objects.get(codename=TeamStatus.APPROVED)
        new_team.save()

        assert resp.status_code == 302
        assert resp.url == '/teams/1/'
        assert get_user_team(self.creator_part, self.competition) != None
