from django.core.management.base import BaseCommand
from django.utils.timezone import utc
from django.core.files import File
from apps.web.models import Competition, CompetitionPhase
from django.contrib.auth import get_user_model
User = get_user_model()

import datetime
import os


class Command(BaseCommand):
    help = "Creates competition."

    def add_arguments(self, parser):
        parser.add_argument('--title',
                            dest='title',
                            help="Name ofthe competition"),
        parser.add_argument('--description',
                            dest='description',
                            help="Description of the competition"),
        parser.add_argument('--creator',
                            dest='creator',
                            help="Email address of creator"),
        parser.add_argument('--logo',
                            dest='logo',
                            help="The file of the logo for the competition"),
        parser.add_argument('--force_user_create',
                            dest='create_user',
                            action='store_true', default=False,
                            help="Create user if non existant"
                            ),
        parser.add_argument('--numphases',
                            dest='numphases',
                            default=0,
                            type=int,
                            help="Number of phases to create"
                            ),
        parser.add_argument('--phasedates',
                            dest='phasedates',
                            type=str,
                            default=None,
                            help="Comma-seprated list of the startdates of the phases: YYYY-MM-DD,YYYY-MM-DD"
                            )

    def handle(self, *args, **options):
        print(" ----- ")
        print("Creating competition")

        creator_email = options['creator']
        title = options['title']
        description = options['description']
        numphases = options['numphases']
        phasedates = []
        try:
            for d in options['phasedates'].split(','):
                phasedates.append(
                    datetime.datetime.strptime(d, "%Y-%m-%d").replace(tzinfo=utc))
            if len(phasedates) != numphases:
                raise Exception("Not enough dates for phases")

        except AttributeError as e:
            if numphases > 0:
                raise e

        if not creator_email or not title or not description:
            print("Need a title, description and email of creator")
            exit(1)
        try:
            creator = User.objects.get(email=creator_email)
        except User.DoesNotExist as e:
            if options['create_user']:
                creator = User.objects.create(email=creator_email,
                                              username=creator_email,
                                              )
                creator.set_password('testing')
                creator.save()
                print("User %s created with password: testing" % creator_email)
            else:
                raise e
        if options['logo']:
            try:
                f = open(os.path.expanduser(options['logo']), 'rb')
            except IOError as e:
                raise e
        else:
            f = None
        competition = Competition(title=title,
                                  creator=creator,
                                  modified_by=creator,
                                  description=description)
        if f:
            competition.image = File(f)
        competition.save()
        for n in range(0, numphases):
            CompetitionPhase.objects.create(competition=competition,
                                            phasenumber=n,
                                            label="Phase #%d" % n,
                                            start_date=phasedates[n])
        print("Created %d phases" % numphases)
        print(" ----- ")
        print("Competition, %s, created. ID: %d" % (competition.title, competition.pk))
        print(" ----- ")
