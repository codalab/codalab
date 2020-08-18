from datetime import timedelta

from django.conf import settings
from django.contrib.sites.models import Site
from django.core.mail import EmailMultiAlternatives
from django.template import Template
from django.core.management.base import BaseCommand
from django.utils.timezone import now

from lxml import html

from apps.authenz.models import ClUser
from apps.web.models import CompetitionSubmission, Competition


class Command(BaseCommand):
    help = """
    Sends email to certain users given some template
    
    Examples:
        $ python manage.py send_email --template=moving_servers.txt --subject "Hello World!"
        $ python manage.py send_email --template=apps/web/templates/emails/notifications/participation_requested.html --subject "Hello World!"
        $ python manage.py send_email --template=moving_servers.txt --subject "Hello World!" --dry-run
    """

    def add_arguments(self, parser):
        parser.add_argument(
            '--active-users', '-a',
            dest='only_active_users',
            action="store_false",
            default=True,
            help="Only message active participants + organizers"
        ),
        parser.add_argument(
            '--dry-run', '-d',
            dest='dry_run',
            action="store_true",
            default=False,
            help="Do a dry run first"
        ),
        parser.add_argument(
            '--subject', '-s',
            dest='subject',
            action="store",
            help="Email subject",
        ),
        parser.add_argument(
            '--template', '-t',
            dest='template',
            action="store",
            help="Template to use for email, it extends the base email template",
        ),
        parser.add_argument(
            '--email_to', '-e',
            dest='email_to',
            action="store",
            help="Overrides other behaviors (like 'send only to active users') and sends to only the specified email",
        )

    def handle(self, *args, **options):
        assert options['template'], "Template argument is required"
        assert options['subject'], "Subject argument is required"

        users_to_send_to = []

        if options['only_active_users']:
            competition_owners_query = Competition.objects.filter(creator__allow_admin_status_updates=True).distinct('creator').order_by('creator')
            competition_owners = [c.creator for c in competition_owners_query]
            active_users_query = CompetitionSubmission.objects.filter(
                started_at__gte=now() - timedelta(days=60),
                participant__user__allow_admin_status_updates=True
            ).distinct('participant__user'
            ).order_by('participant__user').select_related('participant')
            active_users = [s.participant.user for s in active_users_query]
            users_to_send_to = set().union(competition_owners, active_users)

        if options['email_to']:
            # Filter instead of get here to return a list
            users_to_send_to = ClUser.objects.filter(email=options['email_to'])

        assert users_to_send_to, "No users to send to, no template to render!"

        if options['dry_run']:
            print("If this were a real run, I'd send the following to {} users:".format(len(users_to_send_to)))
            html_content, text_content = self._render_template(options['template'], list(users_to_send_to)[0])
            print(text_content)
            print("\n\n------------- HTML BELOW -------------\n\n")
            print(html_content)
        else:
            for user in users_to_send_to:
                html_content, text_content = self._render_template(options['template'], user)
                self._send_email(
                    options['subject'],
                    html_content,
                    text_content,
                    user.email,
                )

    def _render_template(self, template_file, user):
        context = {
            "site": Site.objects.get_current(),
            "user": user,
        }

        # First render HTML version
        template_content = open(template_file, 'r').read()
        template = Template(template_content)

        context = context
        html_content = template.render(context)

        # Then the text version, replacing base.html with base.txt
        template = Template(template_content.replace('base_email.html', 'base_email.txt'))
        text_content_unprocessed = template.render(context)
        html_doc = html.fromstring(text_content_unprocessed)
        text_content = html_doc.text_content()

        return html_content, text_content

    def _send_email(self, subject, html_content, text_content, to_email):
        from_email = settings.DEFAULT_FROM_EMAIL

        message = EmailMultiAlternatives(subject, text_content, from_email, [to_email])
        message.attach_alternative(html_content, 'text/html')
        message.send()
