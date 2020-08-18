from django.contrib.sites.models import Site
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = """
    Set the site (e.g., to codalab.org) so that SendGrid emails have the correct
    URLs inside them pointing back to this site.
    """

    def handle(self, *args, **options):
        site = Site.objects.all()[0]
        print('Old site domain: %s' % site.domain)
        print('Old site name: %s' % site.name)

        if len(args) < 1:
            print('Usage: <domain (e.g., worksheets.codalab.org)> [<name (e.g., CodaLab Worksheets)>]')
            return
        domain = args[0]
        name = args[1] if len(args) > 1 else domain

        site.domain = domain
        site.name = name
        site.save()
