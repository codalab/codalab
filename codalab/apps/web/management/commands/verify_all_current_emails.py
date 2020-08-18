from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

from allauth.account.models import EmailAddress


User = get_user_model()


class Command(BaseCommand):
    help = "Verifies all currently active emails, so no one has to do an activation email if they already have a valid account"

    def handle(self, *args, **options):
        for email in EmailAddress.objects.all():
            email.verified = True
            email.save()
