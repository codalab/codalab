import json
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = """
    CodaLab website supplies an OAuth server.  This script takes in a
    config.json file for the bundle service and substitutes the proper OAuth
    information.
    """

    def handle(self, *args, **options):
        User = get_user_model()
        user = User.objects.all()[0]  # Just get the first user (codalab).

        from oauth2_provider.models import Application

        client, created = Application.objects.get_or_create(
                            user=user,
                            client_type=Application.CLIENT_CONFIDENTIAL,
                            authorization_grant_type=Application.GRANT_CLIENT_CREDENTIALS,
                            name='Bundle service client')

        if len(args) != 1:
            print('Usage: ./manage set_oauth_key <bundle service config json file>')
            return
        json_path = args[0]

        # Replace the auth section of the JSON file and print it out.
        cfg = json.loads(open(json_path).read())
        auth = cfg['server']['auth']
        auth['class'] = 'OAuthHandler'
        if 'address' not in auth:  # Set default address.
            auth['address'] = 'http://localhost:8000'
        auth['app_id'] = client.client_id
        auth['app_key'] = client.client_secret
        print(json.dumps(cfg, sort_keys=True, indent=4, separators=(',', ': ')))
