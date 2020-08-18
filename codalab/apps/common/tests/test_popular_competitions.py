import mock

from django.test import TestCase
from django.contrib.auth import get_user_model

from ..competition_utils import get_most_popular_competitions
from apps.web.models import (Competition,
                             CompetitionParticipant,
                             ParticipantStatus)

User = get_user_model()


class PopularCompetitionsTests(TestCase):

    def setUp(self):
        '''
        1. Create two different users
        2. Create few compettions where publised is True
        3. Add participants to competitions
        3. Return all competitions
        4. Return competitions with more participants
        '''

        self.user = User.objects.create(email="user1@tes.com", username="user1", password="pass")
        self.user1 = User.objects.create(email="user@test.com", username="user", password="pass")
        self.user2 = User.objects.create(email="user2@test.com", username="user2", password="pass")
        self.user3 = User.objects.create(email="user3@test.com", username="user3", password="pass")
        self.user4 = User.objects.create(email="user4@test.com", username="user4", password="pass")
        self.user5 = User.objects.create(email="user5@test.com", username="user5", password="pass")

        self.competition1 = Competition.objects.create(creator=self.user, modified_by=self.user, published=True)
        self.competition2 = Competition.objects.create(creator=self.user, modified_by=self.user, published=True)
        self.competition3 = Competition.objects.create(creator=self.user, modified_by=self.user, published=True)
        self.competition4 = Competition.objects.create(creator=self.user, modified_by=self.user, published=True)
        self.competition5 = Competition.objects.create(creator=self.user, modified_by=self.user, published=True)

        # 3 participants in comp1
        self.participant1 = CompetitionParticipant.objects.create(
            user=self.user,
            competition=self.competition1,
            status=ParticipantStatus.objects.get_or_create(name='approved', codename=ParticipantStatus.APPROVED)[0]
        )
        self.participant2 = CompetitionParticipant.objects.create(
            user=self.user2,
            competition=self.competition1,
            status=ParticipantStatus.objects.get_or_create(name='approved', codename=ParticipantStatus.APPROVED)[0]
        )
        self.participant3 = CompetitionParticipant.objects.create(
            user=self.user3,
            competition=self.competition1,
            status=ParticipantStatus.objects.get_or_create(name='approved', codename=ParticipantStatus.APPROVED)[0]
        )

        # 2 participants in comp2
        self.participant4 = CompetitionParticipant.objects.create(
            user=self.user1,
            competition=self.competition2,
            status=ParticipantStatus.objects.get_or_create(name='approved', codename=ParticipantStatus.APPROVED)[0]
        )
        self.participant5 = CompetitionParticipant.objects.create(
            user=self.user5,
            competition=self.competition2,
            status=ParticipantStatus.objects.get_or_create(name='approved', codename=ParticipantStatus.APPROVED)[0]
        )

        # NO participants in comp3

        # 1 participant in comp4
        self.participant6 = CompetitionParticipant.objects.create(
            user=self.user4,
            competition=self.competition4,
            status=ParticipantStatus.objects.get_or_create(name='approved', codename=ParticipantStatus.APPROVED)[0])

    def test_get_popular_competitions_returns_all_published_competitions(self):
        '''
        Return published competitions
        '''
        competitions = Competition.objects.filter(published=True)
        self.assertTrue(len(competitions), 4)

    def test_get_popular_competitions_returns_empty_queryset(self):
        '''
        Return 0 competitions
        '''
        with mock.patch('apps.common.competition_utils.get_most_popular_competitions') as popular_competitions:
            self.competition1.published = False
            self.competition2.published = False
            self.competition3.published = False
            self.competition4.published = False
            self.competition5.published = False

            self.competition1.save()
            self.competition2.save()
            self.competition3.save()
            self.competition4.save()
            self.competition5.save()

        competitions = get_most_popular_competitions()
        self.assertEqual(len(competitions), 0)

    def test_get_popular_competitions_returns_most_popular_competitions(self):
        '''
        will return most popular competitions
        '''
        competitions = get_most_popular_competitions(min_participants=2, fill_in=False)
        # Should only return #1 and #2 because they have > 2 participants
        self.assertEqual(len(competitions), 2)

        competitions = get_most_popular_competitions(min_participants=0, fill_in=False)
        # Should return all comps
        self.assertEqual(len(competitions), 5)
