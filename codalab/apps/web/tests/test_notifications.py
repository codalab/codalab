import mock

from django.conf import settings
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.core import mail
from django.contrib.auth import get_user_model

from apps.web.models import (Competition,
                             CompetitionParticipant,
                             ParticipantStatus,)
from apps.web import tasks

User = get_user_model()


class CompetitionTest(TestCase):

    def setUp(self):
        statuses = ['unknown', 'denied', 'approved', 'pending']
        for s in statuses:
            ParticipantStatus.objects.get_or_create(name=s, codename=s)

        self.organizer_user = User.objects.create_user(username="organizer", password="pass", email="org@anizer.com")
        self.participant_user = User.objects.create_user(username="participant", password="pass", email="participant@comp.com")
        self.competition = Competition.objects.create(
            title="Test Competition",
            creator=self.organizer_user,
            modified_by=self.organizer_user
        )
        self.participant = CompetitionParticipant.objects.create(
            user=self.participant_user,
            competition=self.competition,
            status=ParticipantStatus.objects.get_or_create(name='pending', codename=ParticipantStatus.PENDING)[0]
        )


class CompetitionMessageParticipantsTests(CompetitionTest):

    def test_msg_participants_view_returns_400_on_get(self):
        self.client.login(username="organizer", password="pass")
        resp = self.client.get(
            reverse("competitions:competition_message_participants", kwargs={"competition_id": self.competition.pk})
        )
        self.assertEqual(resp.status_code, 400)

    def test_msg_participants_view_returns_200_on_valid_POST_and_works(self):
        self.participant.status = ParticipantStatus.objects.get(codename=ParticipantStatus.APPROVED)
        self.participant.save()
        self.client.login(username="organizer", password="pass")
        with mock.patch('apps.web.tasks.send_mass_email.apply_async') as send_mass_email_mock:
            resp = self.client.post(
                reverse("competitions:competition_message_participants", kwargs={"competition_id": self.competition.pk}),
                data={"subject": "test", "body": "message body"}
            )
            self.assertEqual(resp.status_code, 200)
        self.assertTrue(send_mass_email_mock.called)

    def test_msg_participants_view_returns_400_on_no_data(self):
        self.client.login(username="organizer", password="pass")
        resp = self.client.post(
            reverse("competitions:competition_message_participants", kwargs={"competition_id": self.competition.pk})
        )

        self.assertEqual(resp.status_code, 400)
        self.assertIn("Missing subject or body of message!", str(resp.content))

    def test_msg_participants_view_returns_400_on_bad_data(self):
        self.client.login(username="organizer", password="pass")
        resp = self.client.post(
            reverse("competitions:competition_message_participants", kwargs={"competition_id": self.competition.pk}),
            data={"not_right": "bad data"}
        )

        self.assertEqual(resp.status_code, 400)
        self.assertIn("Missing subject or body of message!", str(resp.content))

    def test_msg_participants_view_returns_403_when_not_competition_owner(self):
        self.client.login(username="participant", password="pass")
        resp = self.client.post(
            reverse("competitions:competition_message_participants", kwargs={"competition_id": self.competition.pk})
        )
        self.assertEqual(resp.status_code, 403)

    def test_msg_participants_view_returns_404_when_competition_doesnt_exist(self):
        self.client.login(username="organizer", password="pass")
        non_existant_competition_id = 2398234
        resp = self.client.post(
            reverse("competitions:competition_message_participants", kwargs={"competition_id": non_existant_competition_id})
        )
        self.assertEqual(resp.status_code, 404)

    def test_msg_participants_view_returns_302_when_not_logged_in(self):
        resp = self.client.post(
            reverse("competitions:competition_message_participants", kwargs={"competition_id": self.competition.pk})
        )
        self.assertEqual(resp.status_code, 302)

    def test_msg_participants_view_returns_200_when_admin(self):
        some_admin = User.objects.create_user(username="some_admin", password="pass")
        self.client.login(username="some_admin", password="pass")
        self.competition.admins.add(some_admin)
        self.competition.save()
        resp = self.client.post(
            reverse("competitions:competition_message_participants", kwargs={"competition_id": self.competition.pk}),
            data={"subject": "test", "body": "Test body"}
        )
        self.assertEqual(resp.status_code, 200)

    def test_msg_participants_task_called_with_proper_args(self):
        self.participant.status = ParticipantStatus.objects.get(codename=ParticipantStatus.APPROVED)
        self.participant.save()
        self.client.login(username="organizer", password="pass")
        with mock.patch('apps.web.tasks.send_mass_email.apply_async') as send_mass_email_mock:
            resp = self.client.post(
                reverse("competitions:competition_message_participants", kwargs={"competition_id": self.competition.pk}),
                data={"subject": "test", "body": 'Injected!<script src="http://code_injection/bad_code.js"></script>'}
            )
            self.assertEqual(resp.status_code, 200)

        send_mass_email_mock.assert_called_with(
            (self.competition.pk,),
            dict(
                body='Injected!', # <script> tag was removed!
                subject='test',
                to_emails=[self.participant_user.email],
                from_email=settings.DEFAULT_FROM_EMAIL
            )
        )

    def test_msg_participants_email_not_sent_when_participant_disables_organizer_emails(self):
        self.participant_user.organizer_direct_message_updates = False
        self.participant_user.save()

        self.client.login(username="organizer", password="pass")

        with mock.patch('apps.web.tasks.send_mass_email.apply_async') as send_mass_email_mock:
            resp = self.client.post(
                reverse("competitions:competition_message_participants", kwargs={"competition_id": self.competition.pk}),
                data={"subject": "test", "body": 'Test body'}
            )
            self.assertEqual(resp.status_code, 200)

        self.assertFalse(send_mass_email_mock.called)

    def test_msg_participants_email_not_sent_to_denied_participants(self):
        self.participant.status = ParticipantStatus.objects.get(codename=ParticipantStatus.APPROVED)
        self.participant.save()

        denied_participant_user = User.objects.create_user(username="denied_participant", password="pass")
        denied_participant = CompetitionParticipant.objects.create(
            user=denied_participant_user,
            competition=self.competition,
            status=ParticipantStatus.objects.get_or_create(name='denied', codename=ParticipantStatus.DENIED)[0]
        )

        with mock.patch('apps.web.tasks.send_mass_email.apply_async') as send_mass_email_mock:
            self.client.login(username="organizer", password="pass")
            resp = self.client.post(
                reverse("competitions:competition_message_participants", kwargs={"competition_id": self.competition.pk}),
                data={"subject": "test", "body": "message body"}
            )
            self.assertEqual(resp.status_code, 200)

        send_mass_email_mock.assert_called_with(
            (self.competition.pk,),
            dict(
                body="message body",
                subject='test',
                to_emails=[self.participant_user.email], # denied participant, although a member of this competition, was not emailed
                from_email=settings.DEFAULT_FROM_EMAIL
            )
        )


class AccountSettingsTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username="user", password="pass", email="user@test.com")
        self.client.login(username="user", password="pass")

    def test_account_settings_view_returns_200(self):
        resp = self.client.get(reverse("user_settings"))
        self.assertEqual(resp.status_code, 200)

    def test_account_settings_view_returns_403_when_not_logged_in(self):
        self.client.logout()
        resp = self.client.get(reverse("user_settings"))
        self.assertEqual(resp.status_code, 302)

    def test_account_settings_view_returns_302_on_valid_POST(self):
        resp = self.client.post(
            reverse("user_settings"),
            {
                'participation_status_updates': True,
                'organizer_status_updates': False,
                'organizer_direct_message_updates': True
            }
        )
        self.assertEqual(resp.status_code, 302)

        updated_user = User.objects.get(pk=self.user.pk)
        self.assertFalse(updated_user.organizer_status_updates)


class SendMassEmailTests(TestCase):

    def setUp(self):
        self.users = []
        for count in range(10):
            self.users.append(User.objects.create_user(
                username="user%s" % count,
                password="pass",
                email="user%s@test.com" % count)
            )

        self.competition = Competition.objects.create(creator=self.users[0], modified_by=self.users[0])

    def test_send_mass_email_works(self):
        task_args = {
            "competition_pk": self.competition.pk,
            "body": "Body",
            "subject": "Subject",
            "from_email": "no-reply@test.com",
            "to_emails": [u.email for u in self.users]
        }
        tasks.send_mass_email(**task_args)

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(len(mail.outbox[0].to), 0)  # make sure we're only sending BCC!!
        self.assertEqual(len(mail.outbox[0].bcc), 10)

    def test_send_mass_email_has_valid_links(self):

        task_args = {
            "competition_pk": self.competition.pk,
            "body": "Body",
            "subject": "Subject",
            "from_email": "no-reply@test.com",
            "to_emails": [self.users[0].email]
        }
        tasks.send_mass_email(**task_args)

        m = mail.outbox[0]
        self.assertIn("http://example.com/my/settings", m.body)
        self.assertIn("http://example.com/competitions/%s" % self.competition.pk, m.body)
