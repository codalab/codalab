from django.contrib import messages
from django.contrib.sites.models import Site
from django.http import Http404
from django.shortcuts import render
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

from codalab import settings
from .models import NewsletterSubscription
from .forms import NewsletterSubscriptionSignUpForm, NewsletterSubscriptionUnsubscribeForm


def _send_mail(context, from_email=None, html_file=None, text_file=None, subject=None, to_email=None):
    from_email = from_email if from_email else settings.DEFAULT_FROM_EMAIL

    context["site"] = Site.objects.get_current()

    text = render_to_string(text_file, context)
    html = render_to_string(html_file, context)

    message = EmailMultiAlternatives(subject, text, from_email, [to_email])
    message.attach_alternative(html, 'text/html')
    message.send()


def newsletter_signup(request):
    if not settings.MAILCHIMP_API_KEY:
        raise Http404("This version of CodaLab has not enabled Newsletters.")

    form = NewsletterSubscriptionSignUpForm(request.POST or None)

    if form.is_valid():
        instance = form.save(commit=False)
        if NewsletterSubscription.objects.filter(email=instance.email).exists():
            messages.warning(request, 'This email already signed up for newsletters',
                             'alert alert-warning alert-dismissible')
        else:
            data = {
                "email_address": instance.email,
                "status": "subscribed",
            }

            NewsletterSubscription.objects.create(email=instance.email).subscribe()

            messages.success(request, 'You have been added to the Codalab newsletter',
                             'alert alert-success alert-dismissible')

            subject = "Thank you for joining the Codalab newsletter"
            to_email = instance.email
            email_message = 'newsletter/signup_email.txt'
            html_template = 'newsletter/signup_email.html'

            _send_mail(data, html_file=html_template, text_file=email_message, subject=subject, to_email=to_email)

    context = {
        'form': form,
    }

    template = "newsletter/signup.html"

    storage = messages.get_messages(request)
    storage.used = True

    return render(request, template, context)


def newsletter_unsubscribe(request):
    if not settings.MAILCHIMP_API_KEY:
        raise Http404("This version of CodaLab has not enabled Newsletters.")

    form = NewsletterSubscriptionUnsubscribeForm(request.POST or None)

    if form.is_valid():
        email = form.cleaned_data['email']
        if NewsletterSubscription.objects.filter(email=email).exists():
            data = {
                "status": "unsubscribed",
            }

            NewsletterSubscription.objects.get(email=email).unsubscribe()

            messages.success(request, 'You have been removed from the Codalab newsletter',
                             'alert alert-success alert-dismissible')
            subject = "You have been unsubscribed from the Codalab newsletter"
            to_email = email
            email_message = 'newsletter/unsubscribe_email.txt'
            html_template = 'newsletter/unsubscribe_email.html'

            _send_mail(data, html_file=html_template, text_file=email_message, subject=subject, to_email=to_email)

        else:
            messages.warning(request, 'Your email was not found. We cannot remove that email from the newsletter',
                             'alert alert-warning alert-dismissible')

    context = {
        'form': form,
    }

    template = "newsletter/unsubscribe.html"

    storage = messages.get_messages(request)
    storage.used = True

    return render(request, template, context)
