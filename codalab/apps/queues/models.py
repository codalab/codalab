from urllib.parse import urlparse

from django.conf import settings
from django.db import models
from django_extensions.db.fields import UUIDField
from pyrabbit.http import HTTPError
from django.contrib.sites.models import Site

from apps.queues import rabbit


class Queue(models.Model):
    name = models.CharField(max_length=64)
    vhost = UUIDField(unique=True)
    is_public = models.BooleanField(default=False)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL)
    organizers = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='organizers',
        blank=True,
        null=True,
        help_text="(Organizers allowed to view this queue when they assign their competition to a queue)"
    )

    def __str__(self):
        return self.name

    @property
    def broker_url(self):
        # Start with pyamqp://guest:guest@localhost:5672//
        broker_url_parts = urlparse(settings.BROKER_URL)
        # Get localhost:5672
        host = Site.objects.get_current().domain

        return "pyamqp://{}:{}@{}:{}/{}".format(
            self.owner.rabbitmq_username,
            self.owner.rabbitmq_password,
            host,
            settings.RABBITMQ_PORT,
            self.vhost
        )

    def delete(self, using=None):
        try:
            rabbit.delete_vhost(self.vhost)
        except HTTPError:
            # Vhost not found or something
            pass
        return super(Queue, self).delete(using)
