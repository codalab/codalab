
# -*- coding: cp1252 -*-
"""
Tests for Codalab functionality.
"""
import datetime
import json
import yaml

from django.conf import settings
from django.core import management
from django.test import TestCase
from django.test.client import Client
from django.contrib.auth import get_user_model

from pytz import utc

from apps.web.models import (Competition,
                             CompetitionDefBundle,
                             CompetitionParticipant,
                             CompetitionPhase,
                             ParticipantStatus,)

User = get_user_model()


class Competitions(TestCase):

    def setUp(self):
        self.user = User.objects.create(
            email='test@user.com', username='testuser')
        ParticipantStatus.objects.get_or_create(
            name='Pending', codename=ParticipantStatus.PENDING)
        self.test_data_path = settings.TEST_DATA_PATH
        management.call_command('create_competition', title='Test Title',
                                description='Test Description', creator=self.user.email)
        self.competitions = [x.id for x in Competition.objects.all()]

    def test_add_participant(self):
        """
        Add a participant to a competition.
        """
        management.call_command(
            'add_participant', email='user1@test.com', competition=self.competitions[0])
        p = CompetitionParticipant.objects.get(
            user__email='user1@test.com', competition_id=self.competitions[0])
        assert(p.competition_id == self.competitions[0])

    def test_create_competition_api(self):
        """
        Create a competition programmatically.
        TODO: Does not authenticate (YET)
        """
        client = Client()

        res = client.post('/api/competition/', {'title': 'Test Title',
                                                'description': 'Description',
                                                'creator': self.user.pk,
                                                'modified_by': self.user.pk,
                                                })
        # Status 201: Created
        self.assertEqual(int(res.status_code), int(201))
        data = json.loads(res.content)

        # Just checking to make sure the data was returned correctly
        self.assertTrue('id' in data and data['id'] >= 1)

    def test_get_competition_api(self):
        """
        Create a competition programmatically.
        TODO: Does not authenticate (YET)
        """
        client = Client()
        res = client.post('/api/competition/', {'title': 'Test Title',
                                                'description': 'Description',
                                                'creator': self.user.pk,
                                                'modified_by': self.user.pk,
                                                })
        data = json.loads(res.content)

        # get competition id
        res = client.get('/api/competition/' + str(data['id']) + '/')
        data = json.loads(res.content)
        self.assertEqual(data['title'], 'Test Title')
        self.assertEqual(data['description'], 'Description')
        self.assertEqual(data['creator'], self.user.pk)
        self.assertEqual(data['modified_by'], self.user.pk)

    # def test_delete_competition_api(self):

    #    client = Client()

    # create a competition
    #    res = client.post('/api/competition/', {'title': 'Test Title',
    #                                             'description': 'Description',
    #                                             'creator': self.user.pk,
    #                                             'modified_by': self.user.pk,
    #                                             })
    #    create_data = json.loads(res.content)

    # delete a competition
    #    res = client.delete('/api/competition/'+ str(create_data['id'])+'/')
    #    delete_data = json.loads(res.content)

    # try to access the deleted comp
    #    res = client.get('/api/competition/'+ delete_data + '/')
    #    self.assertEqual(int(res.status_code), int(404))

    # def test_delete_one_from_two_competitions_api(self):

    #    client = Client()

    # create a competition
    #    res = client.post('/api/competition/', {'title': 'Test Title 1',
    #                                             'description': 'Description',
    #                                             'creator': self.user.pk,
    #                                             'modified_by': self.user.pk,
    #                                             })
    #    create_data1 = json.loads(res.content)

    # create another
    #    res = client.post('/api/competition/', {'title': 'Test Title 2',
    #                                             'description': 'Description',
    #                                             'creator': self.user.pk,
    #                                             'modified_by': self.user.pk,
    #                                             })

    #    create_data2 = json.loads(res.content)


    # delete  first competition
    #    res = client.delete('/api/competition/'+ str(create_data1['id'])+'/')
    #    delete_data = json.loads(res.content)


    # try to access the deleted comp
    #    res = client.get('/api/competition/'+ str(create_data1['id'])+'/')
    #    self.assertEqual(int(res.status_code), int(404))

class CompetitionPhaseTests(TestCase):

    def validate(self, ids, expected_ranks, actual_ranks):
        self.assertEqual(len(ids), len(expected_ranks))
        self.assertEqual(len(ids), len(actual_ranks))
        for id in ids:
            self.assertEqual(expected_ranks[id], actual_ranks[id])

    def test_rank_values_1(self):
        ids = {"a", "b", "d", "f", "e"}
        input = {}
        expected = {"a": 1, "b": 1, "d": 1, "f": 1, "e": 1}
        self.validate(ids, expected, CompetitionPhase.rank_values(ids, input))

    def test_rank_values_2(self):
        ids = {"a", "b", "d", "f", "e"}
        input = {}
        expected = {"a": 1, "b": 1, "d": 1, "f": 1, "e": 1}
        self.validate(ids, expected, CompetitionPhase.rank_values(
            ids, input, sort_ascending=False))

    def test_rank_values_3(self):
        ids = {"a", "b", "d", "f", "e"}
        input = {"d": 1.0}
        expected = {"a": 2, "b": 2, "d": 1, "f": 2, "e": 2}
        self.validate(ids, expected, CompetitionPhase.rank_values(ids, input))

    def test_rank_values_4(self):
        ids = {"a", "b", "d", "f", "e"}
        input = {"d": 1.0}
        expected = {"a": 2, "b": 2, "d": 1, "f": 2, "e": 2}
        self.validate(ids, expected, CompetitionPhase.rank_values(
            ids, input, sort_ascending=False))

    def test_rank_values_5(self):
        ids = {"a", "b", "d", "f", "e"}
        input = {"e": 1.0, "a": 4.0}
        expected = {"a": 2, "b": 3, "d": 3, "f": 3, "e": 1}
        self.validate(ids, expected, CompetitionPhase.rank_values(ids, input))

    def test_rank_values_6(self):
        ids = {"a", "b", "d", "f", "e"}
        input = {"e": 1.0, "a": 4.0}
        expected = {"a": 1, "b": 3, "d": 3, "f": 3, "e": 2}
        self.validate(ids, expected, CompetitionPhase.rank_values(
            ids, input, sort_ascending=False))

    def test_rank_values_7(self):
        ids = {"a", "b", "d", "f", "e"}
        input = {"e": 1.0, "a": 1.0}
        expected = {"a": 1, "b": 2, "d": 2, "f": 2, "e": 1}
        self.validate(ids, expected, CompetitionPhase.rank_values(
            ids, input, sort_ascending=False))

    def test_rank_values_8(self):
        ids = {"a", "b", "d", "f", "e"}
        input = {"e": 1.0, "a": 1.001}
        expected = {"a": 1, "b": 2, "d": 2, "f": 2, "e": 1}
        self.validate(ids, expected, CompetitionPhase.rank_values(
            ids, input, sort_ascending=False, eps=0.01))

    def test_rank_values_9(self):
        ids = {"a", "b", "d", "f", "e"}
        input = {"e": 1.0, "a": 1.001}
        expected = {"a": 1, "b": 2, "d": 2, "f": 2, "e": 1}
        self.validate(ids, expected, CompetitionPhase.rank_values(
            ids, input, sort_ascending=True, eps=0.01))

    def test_rank_values_10(self):
        ids = {"a", "b", "d", "f", "e"}
        input = {"e": 1.0, "a": 1.001}
        expected = {"a": 2, "b": 3, "d": 3, "f": 3, "e": 1}
        self.validate(ids, expected,
                      CompetitionPhase.rank_values(ids, input, sort_ascending=True))

    def test_rank_values_11(self):
        ids = {"a", "b", "d", "f", "e"}
        input = {"e": 1.0, "a": 1.001}
        expected = {"a": 1, "b": 3, "d": 3, "f": 3, "e": 2}
        self.validate(ids, expected, CompetitionPhase.rank_values(
            ids, input, sort_ascending=False))

    def test_rank_values_12(self):
        ids = {"a", "b", "d", "f", "e"}
        input = {"a": 4.0, "b": 2.0, "d": 5.0, "f": 3.0, "e": 1.0}
        expected = {"a": 4, "b": 2, "d": 5, "f": 3, "e": 1}
        self.validate(ids, expected, CompetitionPhase.rank_values(ids, input))

    def test_rank_values_14(self):
        ids = {"a", "b", "d", "f", "e"}
        input = {"a": 4.0, "b": 2.0, "d": 5.0, "f": 3.0, "e": 1.0}
        expected = {"a": 2, "b": 4, "d": 1, "f": 3, "e": 5}
        self.validate(ids, expected, CompetitionPhase.rank_values(
            ids, input, sort_ascending=False))

    def test_format_values(self):
        x = 0.12834956
        self.assertEqual("0.1", CompetitionPhase.format_value(x, "1"))
        self.assertEqual("0.13", CompetitionPhase.format_value(x, "2"))
        self.assertEqual("0.128", CompetitionPhase.format_value(x, "3"))
        self.assertEqual("0.1283", CompetitionPhase.format_value(x, "4"))
        self.assertEqual("0.12835", CompetitionPhase.format_value(x, "5"))

        self.assertEqual("0.13", CompetitionPhase.format_value(x))

        self.assertEqual("0.1", CompetitionPhase.format_value(x, "0"))
        self.assertEqual("0.1283495600",
                         CompetitionPhase.format_value(x, "20"))

        self.assertEqual("0.1", CompetitionPhase.format_value(x, "-2"))
        self.assertEqual("0.1", CompetitionPhase.format_value(x, "2.13"))
        self.assertEqual("0.1", CompetitionPhase.format_value(x, "2fooo"))
        self.assertEqual("0.1", CompetitionPhase.format_value(x, ""))
        self.assertEqual("0.1", CompetitionPhase.format_value(x, None))


class CompetitionDefinitionTests(TestCase):

    @staticmethod
    def read_date(dt_str):
        """
        Simulates reading a date/datetime from a YAML file.

        dt_str: String value representing the date & time in the YAML file.
        """
        data = yaml.full_load("key: {0}".format(dt_str))
        return CompetitionDefBundle.localize_datetime(data['key'])

    # 2to3 converted to octal format, changed to kwargs to make more clear
    def test_import_date_1(self):
        dta = CompetitionDefinitionTests.read_date('2014-03-01')
        dte = utc.localize(datetime.datetime(year=2014, month=3, day=1))
        self.assertEqual(dte, dta)

    def test_import_date_2(self):
        dta = CompetitionDefinitionTests.read_date('2014-03-01 10:00:01')
        dte = utc.localize(datetime.datetime(year=2014, month=3, day=1, hour=10, minute=0, second=1))
        self.assertEqual(dte, dta)

    def test_import_date_3(self):
        dta = CompetitionDefinitionTests.read_date('2014-03-01 18:15')
        dte = utc.localize(datetime.datetime(year=2014, month=3, day=1, hour=18, minute=15))
        self.assertEqual(dte, dta)

    def test_import_date_4(self):
        self.assertRaises(ValueError, CompetitionDefinitionTests.read_date, 'not a date')

    def test_import_date_5(self):
        self.assertRaises(ValueError, CompetitionDefinitionTests.read_date, None)
