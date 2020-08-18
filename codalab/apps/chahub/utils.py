from django.conf import settings

import logging
import requests

logger = logging.getLogger(__name__)


def send_to_chahub(endpoint, data, update=False):
    """
    Does a post request to the specified API endpoint on chahub with the inputted data.
    :param endpoint: String designating which API endpoint; IE: 'producers/'
    :param data: Dictionary containing data we are sending away to the endpoint.
    :return:
    """
    assert endpoint, Exception("No ChaHub API endpoint given")
    assert settings.CHAHUB_API_URL, "CHAHUB_API_URL env var required to send to Chahub "

    url = "{}{}".format(settings.CHAHUB_API_URL, endpoint)

    logger.info("ChaHub :: Sending to ChaHub ({}) the following data: \n{}".format(url, data))
    try:
        kwargs = {
            'url': url,
            'data': data,
            'headers': {
                'Content-type': 'application/json',
                'X-CHAHUB-API-KEY': settings.CHAHUB_API_KEY,
            }
        }
        return requests.post(**kwargs)
    except requests.ConnectionError:
        return None
