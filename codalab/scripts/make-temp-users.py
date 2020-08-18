#!/usr/bin/env python
# Run this with the python from the CodaLab virtual environment
#

import sys
import os.path
import os
# This is a really, really long way around saying that if the script is in
# codalab\scripts\users.py, we need to add, ../../../codalab to the
# sys.path to find the settings
root_dir = os.path.join(os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "codalab")
sys.path.append(root_dir)

# Set things for django configurations
os.environ.setdefault("DJANGO_CONFIGURATION", "Dev")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "codalab.settings")

# Import the configuration
from configurations import importer
importer.install()

# Import the user model
from django.contrib.auth import get_user_model
User = get_user_model()

# Make some users
for i in range(1, 11):
    name = "guest%d" % i
    email = "%s@live.com" % name
    password = "abc123"

    print("Creating user %s with email %s and password %s" % (name, email, password))

    new_user, _ = User.objects.get_or_create(email=email, username=name)
    new_user.set_password(password)
    new_user.save()
