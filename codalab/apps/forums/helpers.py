from django.conf import settings
from django.contrib.sites.models import Site
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string


def send_mail(context=None, from_email=None, html_file=None, text_file=None, subject=None, to_email=None):
    """
    Function to send emails to a particular user.

    :param context: Site info.
    :param from_email: Sender's email.
    :param html_file: Email's html content.
    :param text_file: Email's text content.
    :param subject: Email's subject.
    :param to_email: Recipient's email.
    """
    from_email = from_email if from_email else settings.DEFAULT_FROM_EMAIL

    context["site"] = Site.objects.get_current()

    text = render_to_string(text_file, context)
    html = render_to_string(html_file, context)

    message = EmailMultiAlternatives(subject, text, from_email, [to_email])
    message.attach_alternative(html, 'text/html')
    message.send(fail_silently=False)
