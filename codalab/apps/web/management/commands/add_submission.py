from django.core.management.base import BaseCommand
from apps.web.models import Competition, CompetitionPhase, CompetitionParticipant, CompetitionSubmission
from django.contrib.auth import get_user_model
User = get_user_model()

from django.core.files.base import File


class Command(BaseCommand):
    help = "Creates a submission for a participant"

    def add_arguments(self, parser):
        parser.add_argument('--email',
                    dest='email',
                    help="Email of the user"),
        parser.add_argument('--competition',
                    dest='competition',
                    default=None,
                    help="ID of the submission"),
        parser.add_argument('--phase',
                    dest='phase',
                    default=None,
                    help="ID of the competition phase"),
        parser.add_argument('--submission',
                    dest='submission',
                    default=None,
                    help="Path to the submission file"),

    def handle(self, *args, **options):
        competition_id = options['competition']
        phase_id = options['phase']
        submission = options['submission']
        competition = None
        phase = None
        if not options['email']:
            print(" ERROR ... Email Required ... ")
            exit(1)
        if not submission:
            print(" ERROR ... Submission File Required ... ")
            exit(1)

        user = User.objects.get(email=options['email'])
        while not competition and not phase:
            if competition_id and phase_id:
                try:
                    phase = CompetitionPhase.objects.get(
                        pk=phase_id, competition__pk=competition_id)
                    break
                except Competition.DoesNotExist:
                    pass
            else:
                print("Competition/Phase not specified or not valid:\n")

            clist = CompetitionPhase.objects.order_by('competition__pk').all()
            if not clist:
                print(" ... There are no competitions ...")
                exit(1)
            sel = []
            i = 0
            for c in clist:
                sel.append((c.competition, c))
                i = i + 1
                print("%d) %s %s" % (i, c.competition, c))
            try:
                inp = int(input("\n Enter number --> "))
                idx = inp - 1
                competition = sel[idx][0]
                phase = sel[idx][1]
            except ValueError:
                print(" ... Bad Input ... ")
                competition_id = None
                continue
            except Exception as e:
                print(e)

        part = CompetitionParticipant.objects.get(user=user,
                                                  competition=competition
                                                  )
        submission_file = File(open(options['submission'], 'rb'))
        s = CompetitionSubmission(
            participant=part, phase=phase, file=submission_file)
        s.save()
