#!/usr/bin/env python

import argparse
import fnmatch

from textwrap import dedent
from .utils import run_shell_script


def pattern_match(patterns, email):
    for pattern in patterns:
        if pattern and fnmatch.filter([email], pattern):
            return True
    return False


if __name__ == "__main__":
    # Get arguments
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--valid_email_list",
        default="approve_emails.txt",
        help="File containing a list of newline separated emails/patterns to approve"
    )
    parser.add_argument("-c", "--competition", default=1, help="Competition ID, defaults to 1")
    args = parser.parse_args()

    valid_emails = open(args.valid_email_list, "r").readlines()
    valid_emails = [email.strip() for email in valid_emails]  # strip whitespace

    # Get pending approvals
    pending_emails = dedent("""
        from apps.web.models import Competition, CompetitionParticipant, ParticipantStatus
                
        competition = Competition.objects.get(pk={competition_id})
        
        pending_participants = competition.participants.filter(
            status__codename=ParticipantStatus.PENDING
        ).values_list('user__email', flat=True)
        
        emails = ','.join(pending_participants)
        
        # wrap emails so we can easily parse it from the output
        print('***{{}}***'.format(emails))
    """.format(
        competition_id=args.competition
    ))

    print("Checking competition={} for PENDING approvals...".format(args.competition))

    pending_emails_result = run_shell_script(pending_emails)

    pending_emails = pending_emails_result.split('***')[1]  # unwrap emails
    pending_emails = pending_emails.split(',')

    # Pattern match each email
    to_approve = []
    to_deny = []

    for email in pending_emails:
        # Wrap each email in quotes so we can pass it to python later like...
        # 'email@test.com','email2@test.com'
        if email:
            if pattern_match(valid_emails, email):
                to_approve.append("'{}'".format(email))
            else:
                to_deny.append("'{}'".format(email))

    print("Approving:")
    for email in to_approve:
        print(email)
    print('')

    print("Denying:")
    for email in to_deny:
        print(email)
    print('')

    # Execute approvals/denials
    process_participants_script = dedent("""
        from apps.web.models import CompetitionParticipant, ParticipantStatus
        
        to_approve = [{to_approve}]
        to_deny = [{to_deny}]
        
        if to_approve:
            qs = CompetitionParticipant.objects.filter(competition__pk={competition_id}, user__email__in=to_approve)
            qs.update(status=ParticipantStatus.objects.get(codename=ParticipantStatus.APPROVED))
        
        if to_deny:
            qs = CompetitionParticipant.objects.filter(competition__pk={competition_id}, user__email__in=to_deny)
            qs.update(status=ParticipantStatus.objects.get(codename=ParticipantStatus.DENIED))
    """).format(
        competition_id=args.competition,
        to_approve=",".join(to_approve),
        to_deny=",".join(to_deny)
    )

    run_shell_script(process_participants_script)

    print("Executed approval/denial!")
