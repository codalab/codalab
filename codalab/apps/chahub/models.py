import hashlib
import json
import logging
import os

from django.conf import settings
from django.db import models, IntegrityError
from django.utils import timezone

from apps.chahub.utils import send_to_chahub

logger = logging.getLogger(__name__)


class ChaHubSaveMixin(models.Model):
    """Helper mixin for saving model data to ChaHub.

    To use:
    1) Override `get_chahub_endpoint()` to return the endpoint on ChaHub API for this model
    2) Override `get_chahub_data()` to return a dictionary to send to ChaHub
    3) Override `get_chahub_is_valid()` to return True/False on whether or not the object is ready to send to ChaHub
    4) Data is sent on `save()` and `chahub_timestamp` timestamp is set

    To update remove the `chahub_timestamp` timestamp and call `save()`"""
    # Timestamp set whenever a successful update happens
    chahub_timestamp = models.DateTimeField(null=True, blank=True)

    # A hash of the last json information that was sent to avoid sending duplicate information
    chahub_data_hash = models.TextField(null=True, blank=True)

    # If sending to chahub fails, we may need a retry. Signal that by setting this attribute to True
    chahub_needs_retry = models.BooleanField(default=False)

    class Meta:
        abstract = True

    # -------------------------------------------------------------------------
    # METHODS TO OVERRIDE WHEN USING THIS MIXIN!
    # -------------------------------------------------------------------------
    def get_chahub_endpoint(self):
        """Override this to return the endpoint URL for this resource

        Example:
            # If the endpoint is chahub.org/api/v1/competitions/ then...
            return "competitions/"
        """
        raise NotImplementedError()

    def get_chahub_data(self):
        """Override this to return a dictionary with data to send to chahub

        Example:
            return {"name": self.name}
        """
        raise NotImplementedError()

    def get_chahub_is_valid(self):
        """Override this to validate the specific model before it's sent

        Example:
            return comp.is_published
        """
        # By default, always push
        return True

    # -------------------------------------------------------------------------
    # Regular methods
    # -------------------------------------------------------------------------
    def save(self, force_to_chahub=False, *args, **kwargs):
        # We do a save here to give us an ID for generating URLs and such
        try:
            super(ChaHubSaveMixin, self).save(*args, **kwargs)
        except IntegrityError:
            logger.info("Object already has ID skipping save in Chahub mixin.")

        if os.environ.get('PYTEST') and not settings.PYTEST_FORCE_CHAHUB:
            # For tests let's just assume Chahub isn't available
            # We can mock proper responses
            return None

        # Make sure we're not sending these in tests
        if settings.CHAHUB_API_URL:
            is_valid = self.get_chahub_is_valid()

            logger.info("ChaHub :: {}={} is_valid = {}".format(self.__class__.__name__, self.pk, is_valid))

            if is_valid and self.chahub_needs_retry and not force_to_chahub:
                logger.info("ChaHub :: This has already been tried, waiting for do_retries to force resending")
            elif is_valid:
                # Encoded to utf-8 so we can hash it. (Py3)
                data = json.dumps(self.get_chahub_data()).encode('utf-8')
                data_hash = hashlib.md5(data).hexdigest()

                # Send to chahub if we haven't yet, we have new data
                if not self.chahub_timestamp or self.chahub_data_hash != data_hash:
                    resp = send_to_chahub(self.get_chahub_endpoint(), data)

                    if resp and resp.status_code in (200, 201):
                        logger.info("ChaHub :: Received response {} {}".format(resp.status_code, resp.content))
                        self.chahub_timestamp = timezone.now()
                        self.chahub_data_hash = data_hash
                        self.chahub_needs_retry = False
                    else:
                        status = resp.status_code if hasattr(resp, 'status_code') else 'N/A'
                        body = resp.content if hasattr(resp, 'content') else 'N/A'
                        logger.info("ChaHub :: Error sending to chahub, status={}, body={}".format(status, body))
                        self.chahub_needs_retry = True

                    # We save at the beginning, but then again at the end to save our new chahub timestamp and such
                    super(ChaHubSaveMixin, self).save(force_update=True)
            elif not is_valid and self.chahub_needs_retry:
                # This is NOT valid but also marked as need retry, unmark need retry until this is
                # valid again
                self.chahub_needs_retry = False
                super(ChaHubSaveMixin, self).save(force_update=True)
