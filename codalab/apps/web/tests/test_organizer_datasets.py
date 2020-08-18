import mock
import datetime

from django.conf import settings
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model

from apps.web import models
from apps.web.tasks import _make_url_sassy

User = get_user_model()


class OrganizerDataSetTestCase(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username="organizer", password="pass")
        self.other_user = User.objects.create_user(username="potentially_malicious", password="pass")
        self.dataset = models.OrganizerDataSet.objects.create(
            name="Test",
            type="None",
            data_file=SimpleUploadedFile("something.txt", "contents of file".encode('utf-8')),
            uploaded_by=self.user
        )


class OrganizerDataSetCreateTestsCase(OrganizerDataSetTestCase):

    def test_dataset_creation_returns_302_when_not_logged_in(self):
        resp = self.client.get(reverse("my_datasets_create"))
        self.assertEqual(resp.status_code, 302)


class OrganizerDataSetUpdateTestsCase(OrganizerDataSetTestCase):

    def test_dataset_update_returns_302_when_not_logged_in(self):
        resp = self.client.get(reverse("my_datasets_update", kwargs={"pk": self.dataset.pk}))
        self.assertEqual(resp.status_code, 302)

    def test_dataset_update_returns_404_when_not_dataset_owner(self):
        self.client.login(username="potentially_malicious", password="pass")
        resp = self.client.get(reverse("my_datasets_update", kwargs={"pk": self.dataset.pk}))
        self.assertEqual(resp.status_code, 404)

    def test_dataset_update_returns_200_when_owner(self):
        self.client.login(username="organizer", password="pass")
        resp = self.client.get(reverse("my_datasets_update", kwargs={"pk": self.dataset.pk}))
        self.assertEqual(resp.status_code, 200)


class OrganizerDataSetDeleteTestsCase(OrganizerDataSetTestCase):

    def test_dataset_delete_returns_302_when_not_logged_in(self):
        resp = self.client.get(reverse("my_datasets_delete", kwargs={"pk": self.dataset.pk}))
        self.assertEqual(resp.status_code, 302)

    def test_dataset_delete_returns_404_when_not_dataset_owner(self):
        self.client.login(username="potentially_malicious", password="pass")
        resp = self.client.get(reverse("my_datasets_delete", kwargs={"pk": self.dataset.pk}))
        self.assertEqual(resp.status_code, 404)

    def test_dataset_delete_returns_200_when_owner(self):
        self.client.login(username="organizer", password="pass")
        resp = self.client.get(reverse("my_datasets_delete", kwargs={"pk": self.dataset.pk}))
        self.assertEqual(resp.status_code, 200)

    def test_dataset_delete_actually_deletes(self):
        self.client.login(username="organizer", password="pass")
        resp = self.client.post(reverse("my_datasets_delete", kwargs={"pk": self.dataset.pk}))
        self.assertEqual(0, len(models.OrganizerDataSet.objects.filter(pk=self.dataset.pk)))

    def test_dataset_delete_doesnt_delete_phases_using_dataset(self):
        self.competition = models.Competition.objects.create(creator=self.user, modified_by=self.user)
        self.participant = models.CompetitionParticipant.objects.create(
            user=self.user,
            competition=self.competition,
            status=models.ParticipantStatus.objects.get_or_create(codename=models.ParticipantStatus.APPROVED)[0]
        )
        self.phase = models.CompetitionPhase.objects.create(
            competition=self.competition,
            phasenumber=1,
            start_date=datetime.datetime.now() - datetime.timedelta(days=30),
            input_data_organizer_dataset=self.dataset
        )

        self.client.login(username="organizer", password="pass")
        resp = self.client.post(reverse("my_datasets_delete", kwargs={"pk": self.dataset.pk}))
        self.assertEqual(1, len(models.CompetitionPhase.objects.filter(pk=self.phase.pk)))


class OrganizerDataSetListViewTestsCase(OrganizerDataSetTestCase):

    def test_dataset_list_view_returns_302_when_not_logged_in(self):
        resp = self.client.get(reverse("my_datasets"))
        self.assertEqual(resp.status_code, 302)


class OrganizerDataSetMultiDelete(OrganizerDataSetCreateTestsCase):

    def test_dataset_multidelete_returns_works_for_owner(self):
        self.client.login(username="organizer", password="pass")
        resp = self.client.get(reverse("datasets_delete_multiple"))
        self.assertEqual(resp.status_code, 200)

    def test_dataset_multidelete_actually_deletes_multiple_datasets(self):
        self.client.login(username="organizer", password="pass")

        second_dataset = models.OrganizerDataSet.objects.create(
            name="Test",
            type="None",
            data_file=SimpleUploadedFile("something.txt", "contents of file".encode('utf-8')),
            uploaded_by=self.user
        )

        resp = self.client.post(
            reverse("datasets_delete_multiple"),
            {"ids_to_delete[]": [self.dataset.pk, second_dataset.pk]}
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(models.OrganizerDataSet.objects.filter(pk=self.dataset.pk).count(), 0)
        self.assertEqual(models.OrganizerDataSet.objects.filter(pk=second_dataset.pk).count(), 0)

    def test_dataset_multidelete_doesnt_delete_datasets_you_dont_own(self):
        self.client.login(username="potentially_malicious", password="pass")

        second_dataset = models.OrganizerDataSet.objects.create(
            name="Test",
            type="None",
            data_file=SimpleUploadedFile("something.txt", "contents of file".encode('utf-8')),
            uploaded_by=self.user
        )

        resp = self.client.post(
            reverse("datasets_delete_multiple"),
            {"ids_to_delete[]": [self.dataset.pk, second_dataset.pk]}
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(models.OrganizerDataSet.objects.filter(pk=self.dataset.pk).count(), 1)
        self.assertEqual(models.OrganizerDataSet.objects.filter(pk=second_dataset.pk).count(), 1)
