from django.core.management.base import BaseCommand
from apps.web.models import Competition, CompetitionParticipant, ParticipantStatus
from django.contrib.auth import get_user_model
User = get_user_model()


class Command(BaseCommand):
    help = "Adds a particpant to a competition. If the user does not exist, it will create one."

    def add_arguments(self, parser):
        parser.add_argument('--email',
                    dest='email',
                    help="Email of the user"),
        parser.add_argument('--competition',
                    dest='competition',
                    default=None,
                    help="ID of the competition"),
        parser.add_argument('--status',
                    choices=(
                        ParticipantStatus.UNKNOWN, ParticipantStatus.PENDING,
                        ParticipantStatus.APPROVED, ParticipantStatus.DENIED),
                    dest='status',
                    default=ParticipantStatus.PENDING,
                    help="The initial status of the created participant"
                    )

    def handle(self, *args, **options):
        competition_id = options['competition']
        competition = None
        if not options['email']:
            print(" ... Email Required ... ")
            exit(1)

        user, cr = User.objects.get_or_create(
            email=options['email'], defaults={'username': options['email']})
        if cr:
            user.set_password('testing')
            user.save()
            print("\nNew User Created. Password: testing\n")
        while not competition:
            if competition_id:
                try:
                    competition = Competition.objects.get(pk=competition_id)
                    competition_id = competition.pk
                    break
                except Competition.DoesNotExist:
                    pass
            else:
                print("Competition not specified or not valid:\n")
            clist = Competition.objects.order_by('pk').all()
            if not clist:
                print(" ... There are no competitions ...")
                exit(1)
            for c in clist:
                print("  %d) %s" % (c.pk, c.title))
            try:
                competition_id = int(input("\n Enter number --> "))
            except ValueError:
                print(" ... Bad Input ... ")
                competition_id = None
                continue
        pstatus = ParticipantStatus.objects.get(codename=options['status'])
        part, cr = CompetitionParticipant.objects.get_or_create(user=user,
                                                                competition=competition,
                                                                defaults={'status': pstatus})
        if not cr:
            print(" ... Participant already exists ... ")
