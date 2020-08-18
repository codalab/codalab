import re

from django import forms
from django.contrib.auth import get_user_model
from django.utils.translation import ugettext_lazy as _

from allauth.account.adapter import DefaultAccountAdapter
from allauth.account import app_settings

USERNAME_REGEX = re.compile(r'^[a-zA-Z_][a-zA-Z0-9_\.\-]+$', re.UNICODE)


# Have to override this because of USERNAME_REGEX and the ValidationError message associated with it
# https://github.com/pennersr/django-allauth/blob/master/allauth/account/adapter.py
class CodalabAccountAdapter(DefaultAccountAdapter):

    def clean_username(self, username):
        """
        Validates the username. You can hook into this if you want to
        (dynamically) restrict what usernames can be chosen.
        """
        if not USERNAME_REGEX.match(username):
            raise forms.ValidationError(_("Usernames can only contain "
                                          "letters, digits and ./-/_ "))

        username_blacklist_lower = [ub.lower()
                                    for ub in app_settings.USERNAME_BLACKLIST]
        if username.lower() in username_blacklist_lower:
            raise forms.ValidationError(_("Username can not be used. "
                                          "Please use other username."))

        user_model = get_user_model()
        try:
            query = {'username__iexact': username}
            user_model.objects.get(**query)
        except user_model.DoesNotExist:
            return username
        raise forms.ValidationError(_("This username is already taken. Please "
                                      "choose another."))
