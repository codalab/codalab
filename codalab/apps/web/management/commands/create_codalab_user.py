from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = """Create a root user called CodaLab (probably id 0), necessary for OAuth."""
    
    def handle(self, *args, **options):
        username = 'codalab'
        password = args[0] if len(args) > 0 else None
        User = get_user_model()
        user, created = User.objects.get_or_create(username=username)
        if created:
            print('Created a new user.')
        if password is not None:
            print('Setting user password.')
            user.password = password
            user.save()
        print('User ID: %s' % user.id)
        print('User name: %s' % user.username)
