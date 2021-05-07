import datetime

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils.timezone import now

from apps.web.models import Competition, CompetitionParticipant, CompetitionPhase, ParticipantStatus

User = get_user_model()


class CompetitionParticipantDeletionCascade(TestCase):
    def setUp(self):
        self.user = User.objects.create(email='test@user.com', username='testuser')
        self.competition = Competition.objects.create(creator=self.user, modified_by=self.user)
        self.participant_1 = CompetitionParticipant.objects.create(
            user=self.user,
            competition=self.competition,
            status=ParticipantStatus.objects.get_or_create(name='approved', codename=ParticipantStatus.APPROVED)[0]
        )

    def test_competition_relation_is_normal_before_delete(self):
        assert Competition.objects.count() == 1
        assert CompetitionParticipant.objects.count() == 1

    def test_competition_relation_is_normal_after_delete(self):
        self.competition.delete()
        assert Competition.objects.count() == 0
        assert CompetitionParticipant.objects.count() == 0
