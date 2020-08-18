import logging
import uuid
from django.conf import settings
from pyrabbit.api import Client
from pyrabbit.http import HTTPError

logger = logging.getLogger(__name__)


def _get_rabbit_connection():
    """Helper giving us a rabbit connection from settings.BROKER_URL"""
    host_with_port = "{}:{}/api/".format(settings.RABBITMQ_HOST, settings.RABBITMQ_MANAGEMENT_PORT)
    if settings.BROKER_USE_SSL:
        scheme = 'https'
    else:
        scheme = 'http'
    return Client(host_with_port, settings.RABBITMQ_DEFAULT_USER, settings.RABBITMQ_DEFAULT_PASS, scheme=scheme)


def check_user_needs_initialization(user):
    rabbit = _get_rabbit_connection()

    try:
        rabbit.get_user_permissions(user.rabbitmq_username)
        # We found the user, no need to initialize
        return False
    except HTTPError:
        # User not found, needs initialization
        return True


def initialize_user(user):
    """Check whether user has a rabbitmq account already, creates it if not."""
    logger.info("Making new rabbitmq user for {}".format(user))
    user.rabbitmq_username = uuid.uuid4()
    user.rabbitmq_password = uuid.uuid4()

    rabbit = _get_rabbit_connection()
    rabbit.create_user(str(user.rabbitmq_username), str(user.rabbitmq_password))

    # Give user permissions to send submission updates
    rabbit.set_vhost_permissions(
        '/',
        user.rabbitmq_username,
        '.*',
        '.*submission-updates.*',
        '.*submission-updates.*'
    )

    # Was successful, save now
    user.save()


def create_queue(user):
    """Create a new queue with a random name and give full permissions to the owner AND our base account"""
    vhost = str(uuid.uuid4())
    rabbit = _get_rabbit_connection()
    rabbit.create_vhost(vhost)

    # Set permissions for our end user
    rabbit.set_vhost_permissions(
        vhost,
        user.rabbitmq_username,
        '.*',
        '.*',
        '.*'
    )

    # Set permissions for ourselves
    rabbit.set_vhost_permissions(
        vhost,
        settings.RABBITMQ_DEFAULT_USER,
        '.*',
        '.*',
        '.*'
    )

    return vhost


def delete_vhost(vhost):
    rabbit = _get_rabbit_connection()
    rabbit.delete_vhost(vhost)
