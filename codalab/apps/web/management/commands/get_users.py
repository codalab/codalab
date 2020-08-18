from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = """Print the list of users."""

    def handle(self, *args, **options):
        # Print out users.
        User = get_user_model()
        for x in User.objects.all():
            print('\t'.join(map(str, [x.id, x.username, x.email, x.date_joined, x.last_login])))
