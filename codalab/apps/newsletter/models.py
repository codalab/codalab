import hashlib
import json
import logging
import requests

from django.db import models
from django.conf import settings

logger = logging.getLogger(__name__)


class NewsletterSubscription(models.Model):
    email = models.EmailField(null=False, blank=False, unique=True)
    date_added = models.DateTimeField(auto_now_add=True)
    subscription_active = models.BooleanField(default=False)
    needs_retry = models.BooleanField(default=False)

    def __str__(self):
        return self.email

    @property
    def get_user_hash(self):
        user_hash = hashlib.md5(self.email.encode().lower()).hexdigest()
        return user_hash

    def subscribe(self):
        self.subscription_active = True
        self.save()
        if not all([settings.MAILCHIMP_MEMBERS_ENDPOINT_NEWSLETTER, settings.MAILCHIMP_API_KEY]):
            self.needs_retry = True
            self.save()
            return

        data = {
            "email_address": self.email,
            "status": "subscribed",
        }

        try:
            response = requests.patch(
                settings.MAILCHIMP_MEMBERS_ENDPOINT_NEWSLETTER + '/' + self.get_user_hash,
                auth=("", settings.MAILCHIMP_API_KEY),
                data=json.dumps(data)
            )

            if response.ok:
                self.needs_retry = False
                self.save()

            elif 'The requested resource could not be found' in response.json().get('detail'):
                response = requests.post(
                    settings.MAILCHIMP_MEMBERS_ENDPOINT_NEWSLETTER,
                    auth=("", settings.MAILCHIMP_API_KEY),
                    data=json.dumps(data)
                )

                self.needs_retry = not response.ok
                self.save()
            else:
                self.needs_retry = True
                self.save()

        except requests.exceptions.RequestException:
            self.needs_retry = True
            self.save()

    def unsubscribe(self):
        self.subscription_active = False
        self.save()
        if not all([settings.MAILCHIMP_MEMBERS_ENDPOINT_NEWSLETTER, settings.MAILCHIMP_API_KEY]):
            self.needs_retry = True
            self.save()
            return

        data = {
            "status": "unsubscribed",
        }

        try:
            response = requests.patch(
                settings.MAILCHIMP_MEMBERS_ENDPOINT_NEWSLETTER + '/' + self.get_user_hash,
                auth=("", settings.MAILCHIMP_API_KEY),
                data=json.dumps(data)
            )

            if response.ok:
                self.delete()
            else:
                self.needs_retry = True
                self.save()

        except requests.exceptions.RequestException as e:
            self.needs_retry = True
            self.save()
            logger.error(e)

    def retry(self):
        if self.subscription_active:
            self.subscribe()
        else:
            self.unsubscribe()
