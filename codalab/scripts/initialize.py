#!/usr/bin/env python
# Run this script from the CodaLab virtual environment to insert
# initial data required by the web app into the database.

# NOTE: This is no longer called from `run_django.sh`, instead we use the fixture `initial_data` under web/fixtures.
# If changes are needed, reset the db, migrate, make your changes here, call this from shell via
# from scripts.initialize import insert_data
# insert_data()
# Then use `python manage.py dumpdata <app> --output <fixture-name>.json` to create a new initial_data fixture file.
# You'll need to do this for both the web and team apps.
# Move the new fixture file from the project root to web/fixtures and replace the old one. You could of course create the
# objects manually, but this seems more convenient.

import sys, os.path, os

root_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "codalab")
sys.path.append(root_dir)

# Set things for django configurations
os.environ.setdefault("DJANGO_CONFIGURATION", "Dev")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "codalab.settings")

# Import the configuration
from configurations import importer
importer.install()

from django.contrib.sites.models import Site
from apps.web.models import (CompetitionSubmissionStatus,
                             ContentCategory,
                             ContentVisibility,
                             DefaultContentItem,
                             ParticipantStatus)
from apps.web.models import (Page)
from django.conf import settings
from apps.teams.models import TeamStatus, TeamMembershipStatus

def migrate_data():
    """
    Run necessary data migrations.
    """

    # For https://github.com/codalab/codalab/issues/322

    categories = ContentCategory.objects.filter(codename='participate')
    for category in categories:

        dcitems = DefaultContentItem.objects.filter(category=category, rank=1, required=True)
        for dcitem in dcitems:
            if dcitem.label == "Submit Results":
                dcitem.label = "Submit / View Results"
                dcitem.save()

        pages = Page.objects.filter(category=category, rank=1)
        for page in pages:
            if page.label == "Submit Results":
                page.label = "Submit / View Results"
                page.save()

def insert_data():
    """
    Inserts initial data required by the web app into the database defined by the Django settings.

    The script's first action is to check the value of the Site's name. If the name is already the
    expected value (as defined by settings.CODALAB_SITE_NAME) then no additional data is inserted.
    Therefore, it is safe to run the script multiple times; the deployment code takes advantage of
    this fact.
    """
    #
    # Site info
    #

    site, created = Site.objects.get_or_create(pk=settings.SITE_ID)
    site.domain = settings.CODALAB_SITE_DOMAIN
    site.name = settings.CODALAB_SITE_NAME
    site.save()

    if ContentCategory.objects.all().count() > 0:
        print("Initial data has been detected in the database: skipping all inserts. Running data migration...")
        migrate_data()
        print("Data migration complete.")
        return

    #
    # Initialize web content
    #

    cvs = [ ("Visible", "visible", "viewStateOn"),
            ("Visible Always", "visible_always", "viewStateAlwaysOn"),
            ("Hidden", "hidden", "viewStateOff") ]

    content_visibility_items = dict()
    for name, codename, classname in cvs:
        ncv, _ = ContentVisibility.objects.get_or_create(name=name, codename=codename, classname=classname)
        ncv.save()
        content_visibility_items[codename] = ncv


    ccs = [ { 'parent' : None,
              'name' : "Learn the Details",
              'codename' : "learn_the_details",
              'visibility' : content_visibility_items['visible'],
              'is_menu' : True,
              'content_limit' : 1 },
            { 'parent' : None,
              'name' : "Participate",
              'codename' : "participate",
              'visibility' : content_visibility_items['visible'],
              'is_menu' : True,
              'content_limit' : 1 },
            { 'parent' : None,
              'name' : "Results",
              'codename' : "results",
              'visibility' : content_visibility_items['visible'],
              'is_menu' : True,
              'content_limit' : 1 } ]

    content_categories = dict()
    for category in ccs:
        nc, _ = ContentCategory.objects.get_or_create(parent=category['parent'], name=category['name'],
                            codename=category['codename'], visibility=category['visibility'],
                            is_menu=category['is_menu'], content_limit=category['content_limit'])
        nc.save()
        content_categories[category['codename']] = nc

    cis = [ { 'category' : content_categories['learn_the_details'],
              'initial_visibility' : content_visibility_items['visible'],
              'required' : True,
              'rank' : 0,
              'codename' : "overview",
              'label' : "Overview" },
            { 'category' : content_categories['learn_the_details'],
              'initial_visibility' : content_visibility_items['visible'],
              'required' : True,
              'rank' : 1,
              'codename' : "evaluate",
              'label' : "Evaluate" },
            { 'category' : content_categories['learn_the_details'],
              'initial_visibility' : content_visibility_items['visible'],
              'required' : True,
              'rank' : 2,
              'codename' : "terms_and_conditions",
              'label' : "Terms and Conditions" },
            { 'category' : content_categories['participate'],
              'initial_visibility' : content_visibility_items['visible'],
              'required' : True,
              'rank' : 0,
              'codename' : "get_data",
              'label' : "Get Data" },
            { 'category' : content_categories['participate'],
              'initial_visibility' : content_visibility_items['visible'],
              'required' : True,
              'rank' : 1,
              'codename' : 'submit_results',
              'label' : "Submit / View Results" } ]

    for dci in cis:
        dcii, _ = DefaultContentItem.objects.get_or_create(category=dci['category'], label=dci['label'],
                                rank=dci['rank'], required=dci['required'],codename=dci['codename'],
                                initial_visibility=dci['initial_visibility'])
        dcii.save()


    pss = [ ("Denied", "denied", "Paricipation was denied."),
            ("Approved", "approved", "Paricipation was approved."),
            ("Pending", "pending", "Paricipation is pending approval.") ]

    for name, codename, description in pss:
        _, _ = ParticipantStatus.objects.get_or_create(name=name, codename=codename, description=description)

    submission_status_set = [("Submitting", "submitting"),
                             ("Submitted", "submitted"),
                             ("Running", "running"),
                             ("Failed", "failed"),
                             ("Cancelled", "cancelled"),
                             ("Finished", "finished")]

    for name, codename in submission_status_set:
        _, _ = CompetitionSubmissionStatus.objects.get_or_create(name=name, codename=codename)

    team_status = [("Denied", "denied", "Team was denied."),
                   ("Approved", "approved", "Team was approved."),
                   ("Pending", "pending", "Team is pending approval."),
                   ("Deleted", "deleted", "Team has been deleted.")]

    for name, codename, description in team_status:
        _, _ = TeamStatus.objects.get_or_create(name=name, codename=codename, description=description)

        team_membership_status = [("Rejected", "rejected", "User membership rejected."),
                                  ("Approved", "approved", "User membership approved."),
                                  ("Pending", "pending", "User membership is pending approval."),
                                  ("Canceled", "canceled", "User membership canceled.")]

    for name, codename, description in team_membership_status:
        _, _ = TeamMembershipStatus.objects.get_or_create(name=name, codename=codename,
                                                          description=description)


if __name__ == "__main__":

    insert_data()
