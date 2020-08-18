#!/usr/bin/env python

import argparse
import requests
from textwrap import dedent
from uuid import uuid4
from os.path import exists, basename
from .utils import run_shell_script


def put_blob(url, file_path):
    return requests.put(
        url,
        data=open(file_path, 'rb'),
        headers={
            # Only for Azure but AWS ignores this fine
            'x-ms-blob-type': 'BlockBlob',
        }
    )


if __name__ == "__main__":
    # Get arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("submission_zip", help="Submission zip file to use for stressing")
    parser.add_argument("participant_email", help="Participant, identified by email address")
    parser.add_argument("-c", "--competition", default=1, help="Competition ID, defaults to 1")
    args = parser.parse_args()

    # Validate arguments
    if not args.submission_zip.endswith(".zip"):
        raise Exception("Received non zip file: {}".format(args.submission_zip))

    if not exists(args.submission_zip):
        raise Exception("Zip file not found: {}".format(args.submission_zip))

    print("Uploading submission '{}' for user '{}' in competition={}".format(
        args.submission_zip,
        args.participant_email,
        args.competition,
    ))

    # Get SAS URL by running a script inside docker and printing out the URL between asterisks, like:
    # >>> ***http://url-we-want.com/***
    base_url_path = 'stresser/{}/{}'.format(str(uuid4())[:10], basename(args.submission_zip))
    get_sas_url_script = dedent("""
        from apps.web.tasks import _make_url_sassy
        
        url = _make_url_sassy('{}', permission='w')
        
        # wrap the URL so we can easily parse it from the output
        print('***{{}}***'.format(url))
    """).format(base_url_path)

    sas_script_result = run_shell_script(get_sas_url_script)

    submission_url = sas_script_result.split('***')[1]

    # Put submission to that URL
    resp = put_blob(submission_url, args.submission_zip)

    # Strip extra query params from URL since we don't need it any more
    submission_url = submission_url.split('?')[0]

    # Tie it together and submit
    submission_script = dedent("""
        from django.conf import settings
        from apps.web.models import Competition, CompetitionSubmission, CompetitionParticipant
        from apps.web.tasks import evaluate_submission
        
        if settings.USE_AWS:
            file_kwarg = {{'s3_file': '{submission_url}'}}
        else:
            file_kwarg = {{'file': '{submission_url}'}}
                
        competition = Competition.objects.get(pk={competition_id})
        phase = None
        for phase in competition.phases.all():
            if phase.is_active:
                phase = phase
                break
        
        new_submission = CompetitionSubmission(
            participant=CompetitionParticipant.objects.get(user__email='{email}', competition=competition),
            phase=phase,
            **file_kwarg
        )
        new_submission.save(ignore_submission_limits=True)
    
        evaluate_submission.apply_async((new_submission.pk, phase.is_scoring_only))
        
        # wrap the submission ID so we can easily parse it from the output
        print('***{{}}***'.format(new_submission.pk))
    """).format(
        submission_url=base_url_path,
        email=args.participant_email,
        competition_id=args.competition
    )

    submission_script_result = run_shell_script(submission_script)

    pk = submission_script_result.split('***')[1]

    print("Submission (id={}) started".format(pk))

    with open("submission_ids.txt", "a+") as submission_ids:
        submission_ids.write("{}\n".format(pk))
