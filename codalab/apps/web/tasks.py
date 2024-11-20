"""
Defines background tasks needed by the web site.
"""
import csv
import io
import json
import logging
import requests
import time
import traceback
import yaml
import zipfile
import datetime
from apps.authenz.models import ClUser
from apps.chahub.models import ChaHubSaveMixin
from apps.chahub.utils import send_to_chahub
from apps.coopetitions.models import DownloadRecord
from apps.health.models import (CompetitionStorageDataPoint,
                                UserStorageDataPoint,
                                StorageSnapshot,
                                StorageUsageHistory)
from apps.jobs.models import (Job,
                              run_job_task,
                              JobTaskResult,
                              update_job_status_task)
from apps.web import models
from apps.web.models import CompetitionDump
from apps.web.models import (add_submission_to_leaderboard,
                             Competition,
                             CompetitionSubmission,
                             CompetitionDefBundle,
                             CompetitionSubmissionStatus,
                             CompetitionPhase,
                             SubmissionScore,
                             SubmissionScoreDef,
                             CompetitionSubmissionMetadata, BundleStorage, SubmissionResultGroup,
                             SubmissionScoreDefGroup, OrganizerDataSet, CompetitionParticipant, ParticipantStatus)
from apps.web.utils import inheritors, push_submission_to_leaderboard_if_best, s3_key_from_url, \
    get_competition_size_data, delete_submissions_except_best_and_or_last, storage_recursive_find
from botocore.exceptions import ClientError
from celery import task
from celery.app import app_or_default
from celery.exceptions import SoftTimeLimitExceeded
from codalab.azure_storage import make_blob_sas_url
from collections import OrderedDict
from datetime import timedelta
from django.conf import settings
from django.contrib.sites.models import Site
from django.core.files.base import ContentFile
from django.core.mail import EmailMultiAlternatives, send_mail
from django.db import transaction
from django.db.models import Count
from django.template.loader import render_to_string
from django.utils import timezone
from zipfile import ZipFile

logger = logging.getLogger(__name__)

# Echo
def echo_task(job_id, args):
    """
    A simple task to echo a message provided as args['message']. The associated job will
    be marked as Finished if the message is echoes successfully. Otherwise the job will be
    marked as Failed.

    job_id: The ID of the job.
    args: A dictionary with the arguments for the task. Expected items are:
        args['message']: string to send as info to the module's logger.
    """
    def echo_it(job):
        """Echoes the message specified."""
        logger.info("Echoing (job id=%s): %s", job.id, args['message'])
        return JobTaskResult(status=Job.FINISHED)

    run_job_task(job_id, echo_it)


def echo(text):
    """
    Echoes the text specified. This is for testing.

    text: The text to echo.

    Returns a Job object which can be used to track the progress of the operation.
    """
    return Job.objects.create_and_dispatch_job('echo', {'message': text})


@task(queue='site-worker', soft_time_limit=60 * 60 * 24)
def create_competition(job_id, comp_def_id):
    """
    A task to create a competition from a bundle with the competition's definition.

    job_id: The ID of the job.
    args: A dictionary with the arguments for the task. Expected items are:
        args['comp_def_id']: The ID of the bundle holding the competition definition.
    Once the task succeeds, a new competition will be ready to use in CodaLab.
    """

    logger.info("Creating competition for competition bundle (bundle_id=%s)", comp_def_id)
    competition_def = CompetitionDefBundle.objects.get(pk=comp_def_id)
    try:
        competition = competition_def.unpack()
        result = JobTaskResult(status=Job.FINISHED, info={'competition_id': competition.pk})
        update_job_status_task(job_id, result.get_dict())
        logger.info("Created competition for competition bundle (bundle_id=%s, comp_id=%s)",
                    comp_def_id, competition.pk)

    except Exception as e:
        result = JobTaskResult(status=Job.FAILED, info={'error': str(e)})
        update_job_status_task(job_id, result.get_dict())
        logging.exception("Failed unpacking competition. Deleting uploaded bundle.")
        if competition_def.competition:
            competition_def.competition.delete()
        competition_def.delete()


# CompetitionSubmission states which are final.
_FINAL_STATES = {
    CompetitionSubmissionStatus.FINISHED,
    CompetitionSubmissionStatus.FAILED,
    CompetitionSubmissionStatus.CANCELLED
}

def _set_submission_status(submission_id, status_codename):
    """
    Update the status of a submission.

    submission_id: PK of CompetitionSubmission object.
    status_codename: New status codename.
    """
    status = CompetitionSubmissionStatus.objects.get(codename=status_codename)
    with transaction.atomic():
        submission = CompetitionSubmission.objects.select_for_update().get(pk=submission_id)
        old_status_codename = submission.status.codename
        if old_status_codename not in _FINAL_STATES:
            submission.status = status
            submission.save()
            logger.info("Changed submission status from %s to %s (id=%s).",
                        old_status_codename, status_codename, submission_id)
        else:
            logger.info("Skipping update of submission status: invalid transition %s -> %s  (id=%s).",
                        status_codename, old_status_codename, submission_id)


def predict(submission, job_id):
    """
    Dispatches the prediction taks for the given submission to an appropriate compute worker.

    submission: The CompetitionSubmission object.
    job_id: The job ID used to track the progress of the evaluation.
    """
    # Generate metadata-only bundle describing the computation
    lines = []
    if settings.USE_AWS:
        program_value = submission.s3_file
    else:
        program_value = submission.file.name

    if len(program_value) > 0:
        lines.append("program: %s" % _make_url_sassy(program_value))
    else:
        raise ValueError("Program is missing.")

    if submission.phase.ingestion_program:
        # Keep stdout/stder for ingestion
        submission.ingestion_program_stdout_file.save('ingestion_program_stdout_file.txt', ContentFile(''.encode('utf-8')))
        submission.ingestion_program_stderr_file.save('ingestion_program_stderr_file.txt', ContentFile(''.encode('utf-8')))

        # For the ingestion program we have to include the actual ingestion program...
        lines.append("ingestion_program: %s" % _make_url_sassy(submission.phase.ingestion_program.name))

        # ..as well as the reference data for this phase.
        ref_value = submission.phase.reference_data.name
        if len(ref_value) > 0:
            lines.append("hidden_ref: %s" % _make_url_sassy(ref_value))

    # Create stdout.txt & stderr.txt, set the file names
    username = submission.participant.user.username
    stdout_filler = ["Standard output for submission #{0} by {1}.".format(submission.submission_number, username), ""]
    submission.stdout_file.save('stdout.txt', ContentFile('\n'.join(stdout_filler).encode('utf-8')))
    submission.prediction_stdout_file.save('prediction_stdout_file.txt', ContentFile('\n'.join(stdout_filler).encode('utf-8')))
    stderr_filler = ["Standard error for submission #{0} by {1}.".format(submission.submission_number, username), ""]
    submission.stderr_file.save('stderr.txt', ContentFile('\n'.join(stderr_filler).encode('utf-8')))
    submission.prediction_stderr_file.save('prediction_stderr_file.txt', ContentFile('\n'.join(stderr_filler).encode('utf-8')))

    submission.prediction_output_file.save('output.zip', ContentFile(''.encode('utf-8')))

    input_value = submission.phase.input_data.name

    logger.info("Running prediction")

    if len(input_value) > 0:
        lines.append("input: %s" % _make_url_sassy(input_value))
    lines.append("stdout: %s" % _make_url_sassy(submission.prediction_stdout_file.name, permission='w'))
    lines.append("stderr: %s" % _make_url_sassy(submission.prediction_stderr_file.name, permission='w'))
    submission.prediction_runfile.save('run.txt', ContentFile('\n'.join(lines).encode('utf-8')))

    # Store workflow state
    submission.execution_key = json.dumps({'predict': job_id})
    submission.save()

    # Submit the request to the computation service
    _prepare_compute_worker_run(job_id, submission, is_prediction=True)

    # Update the submission object
    _set_submission_status(submission.id, CompetitionSubmissionStatus.SUBMITTED)


def _prepare_compute_worker_run(job_id, submission, is_prediction):
    """Kicks off the compute_worker_run task passing job id, submission container details, and "is prediction
    or scoring" flag to compute worker"""
    if is_prediction:
        bundle_url = submission.prediction_runfile.name
        stdout = submission.prediction_stdout_file.name
        stderr = submission.prediction_stderr_file.name
        output = submission.prediction_output_file.name

    else:
        # Scoring, if we're not predicting
        bundle_url = submission.runfile.name
        stdout = submission.stdout_file.name
        stderr = submission.stderr_file.name
        output = submission.output_file.name

    if submission.docker_image and submission.docker_image != "":
        docker_image = submission.docker_image
    else:
        docker_image = submission.phase.competition.competition_docker_image or settings.DOCKER_DEFAULT_WORKER_IMAGE
        submission.docker_image = docker_image
        submission.save()

    logger.info("@@@ Docker image set to: {} @@@".format(docker_image))

    data = {
        "id": job_id,
        "task_type": "run",
        "task_args": {
            "submission_id": submission.pk,
            "docker_image": docker_image,
            "ingestion_program_docker_image": docker_image,
            "bundle_url": _make_url_sassy(bundle_url),
            "stdout_url": _make_url_sassy(stdout, permission='w'),
            "stderr_url": _make_url_sassy(stderr, permission='w'),
            "output_url": _make_url_sassy(output, permission='w'),
            "ingestion_program_output_url": _make_url_sassy(submission.ingestion_program_stdout_file.name, permission='w'),
            "ingestion_program_stderr_url": _make_url_sassy(submission.ingestion_program_stderr_file.name, permission='w'),
            "detailed_results_url": _make_url_sassy(submission.detailed_results_file.name, permission='w'),
            "private_output_url": _make_url_sassy(submission.private_output_file.name, permission='w'),
            "secret": submission.secret,
            "execution_time_limit": submission.phase.execution_time_limit,
            "predict": is_prediction,
        }
    }

    logger.info("Passing task args to compute worker: %s", data["task_args"])

    time_limit = submission.phase.execution_time_limit
    if time_limit <= 0:
        time_limit = 60 * 10  # 10 minutes timeout by default

    # Let's make our soft time limit (for the task) a bit longer than it needs to be, so the worker has time to
    # clean up
    time_limit += 60 * 60  # 1 hour cleanup time

    if submission.phase.competition.queue:
        submission.queue_name = submission.phase.competition.queue.name or ''
        submission.save()

        # Send to special queue?
        app = app_or_default()
        with app.connection() as new_connection:
            new_connection.virtual_host = submission.phase.competition.queue.vhost
            compute_worker_run(data, soft_time_limit=time_limit, connection=new_connection)
    else:
        compute_worker_run(data, soft_time_limit=time_limit, priority=2)


def compute_worker_run(data, priority=None, **kwargs):
    if priority:
        kwargs['queue_arguments'] = {'x-max-priority': priority}
    task_args = data['task_args'] if 'task_args' in data else None
    app = app_or_default()
    app.send_task('compute_worker_run', args=(data["id"], task_args), queue='compute-worker', **kwargs)


def _make_url_sassy(path, permission='r', duration=60 * 60 * 24, content_type=None):
    if not path:
        logger.info("Make URL sassy received an empty path!")
        return ''

    if settings.USE_AWS:
        if permission == 'r':
            # GET instead of r (read) for AWS
            method = 'GET'
        elif permission == 'w':
            # GET instead of w (write) for AWS
            method = 'PUT'
        else:
            # Default to get if we don't know
            method = 'GET'

        key = s3_key_from_url(path)

        logger.info("Path is: {}".format(key))
        # This was necessary because otherwise the url generated would have double slashes
        if key[0] == '/':
            key = key[1:]

        try:
            params = {
                'Bucket': settings.AWS_STORAGE_PRIVATE_BUCKET_NAME,
                'Key': key,
            }
            if content_type and permission != 'w':
                params['ResponseContentType'] = content_type
            # Look into if there's a host param so we don't need to replace it ourselves...
            url =  BundleStorage.bucket.meta.client.generate_presigned_url(
                ClientMethod='put_object' if permission == 'w' else 'get_object',
                Params=params,
                ExpiresIn=duration,
                HttpMethod=method
            )
        except ClientError as e:
            logger.error(e)
            return ''
        # Replace the default URL with the proper AWS_S3_HOST if we have one
        if settings.AWS_S3_HOST:
            return url.replace("s3.amazonaws.com", settings.AWS_S3_HOST)
        else:
            return url
    else:
        sassy_url = make_blob_sas_url(
            settings.BUNDLE_AZURE_ACCOUNT_NAME,
            settings.BUNDLE_AZURE_ACCOUNT_KEY,
            settings.BUNDLE_AZURE_CONTAINER,
            path,
            permission=permission,
            duration=duration
        )

        # Ugly way to check if we didn't get the path, should work...
        if '<Code>InvalidUri</Code>' not in sassy_url:
            return sassy_url
        else:
            return ''


def score(submission, job_id):
    """
    Dispatches the scoring task for the given submission to an appropriate compute worker.

    submission: The CompetitionSubmission object.
    job_id: The job ID used to track the progress of the evaluation.
    """
    # profile = cProfile.Profile()
    start = time.time()
    # profile.enable()
    # Loads the computation state.
    state = {}
    if len(submission.execution_key) > 0:
        state = json.loads(submission.execution_key)
    has_generated_predictions = 'predict' in state

    #generate metadata-only bundle describing the history of submissions and phases
    last_submissions = CompetitionSubmission.objects.filter(
        participant=submission.participant,
        status__codename=CompetitionSubmissionStatus.FINISHED
    ).order_by('-submitted_at')


    lines = []
    # lines.append("description: history of all previous successful runs output files")
    #
    # if last_submissions:
    #     for past_submission in last_submissions:
    #         if past_submission.pk != submission.pk:
    #             #pad folder numbers for sorting os side, 001, 002, 003,... 010, etc...
    #             past_submission_phasenumber = '%03d' % past_submission.phase.phasenumber
    #             past_submission_number = '%03d' % past_submission.submission_number
    #             lines.append('%s/%s/output/: %s' % (
    #                     past_submission_phasenumber,
    #                     past_submission_number,
    #                     submission_private_output_filename(past_submission),
    #                 )
    #             )


    submission.history_file.save('history.txt', ContentFile('\n'.join(lines).encode('utf-8')))

    score_csv = submission.phase.competition.get_results_csv(submission.phase.pk)
    submission.scores_file.save('scores.txt', ContentFile(score_csv.encode('utf-8')))

    # Extra submission info
    coopetition_zip_buffer = io.BytesIO()
    coopetition_zip_file = zipfile.ZipFile(coopetition_zip_buffer, "w")

    phases_list = submission.phase.competition.phases.all()

    for phase in phases_list:
        coopetition_field_names = (
            "participant__user__username",
            "pk",
            "when_made_public",
            "when_unmade_public",
            "started_at",
            "completed_at",
            "download_count",
            "submission_number",
        )
        annotated_submissions = phase.submissions.filter(status__codename=CompetitionSubmissionStatus.FINISHED).values(
            *coopetition_field_names
        ).annotate(like_count=Count("likes"), dislike_count=Count("dislikes"))

        # Add this after fetching annotated count from db
        coopetition_field_names += ("like_count", "dislike_count")

        coopetition_csv = io.StringIO()
        writer = csv.DictWriter(coopetition_csv, coopetition_field_names)
        writer.writeheader()
        for row in annotated_submissions:
            writer.writerow(row)

        coopetition_zip_file.writestr('coopetition_phase_%s.txt' % phase.phasenumber, coopetition_csv.getvalue().encode('utf-8'))

    # Scores metadata
    for phase in phases_list:
        coopetition_zip_file.writestr(
            'coopetition_scores_phase_%s.txt' % phase.phasenumber,
            phase.competition.get_results_csv(phase.pk, include_scores_not_on_leaderboard=True)
        )

    # Download metadata
    coopetition_downloads_csv = io.StringIO()
    writer = csv.writer(coopetition_downloads_csv)
    writer.writerow((
        "submission_pk",
        "submission_owner",
        "downloaded_by",
        "time_of_download",
    ))
    for download in DownloadRecord.objects.filter(submission__phase__competition=submission.phase.competition):
        writer.writerow((
            download.submission.pk,
            download.submission.participant.user.username,
            download.user.username,
            str(download.timestamp),
        ))

    coopetition_zip_file.writestr('coopetition_downloads.txt', coopetition_downloads_csv.getvalue().encode('utf-8'))

    # Current user
    coopetition_zip_file.writestr('current_user.txt', submission.participant.user.username.encode('utf-8'))
    coopetition_zip_file.close()

    # Save them all
    submission.coopetition_file.save('coopetition.zip', ContentFile(coopetition_zip_buffer.getvalue()))

    # Generate metadata-only bundle describing the inputs. Reference data is an optional
    # dataset provided by the competition organizer. Results are provided by the participant
    # either indirectly (has_generated_predictions is True i.e. participant provides a program
    # which is run to generate results) ordirectly (participant uploads results directly).
    lines = []
    ref_value = submission.phase.reference_data.name
    if len(ref_value) > 0:
        lines.append("ref: %s" % _make_url_sassy(ref_value))
    if settings.USE_AWS:
        res_value = submission.prediction_output_file.name if has_generated_predictions else submission.s3_file
    else:
        res_value = submission.prediction_output_file.name if has_generated_predictions else submission.file.name
    if len(res_value) > 0:
        lines.append("res: %s" % _make_url_sassy(res_value))
    else:
        raise ValueError("Results are missing.")

    lines.append("history: %s" % _make_url_sassy(submission.history_file.name))
    lines.append("scores: %s" % _make_url_sassy(submission.scores_file.name))
    lines.append("coopetition: %s" % _make_url_sassy(submission.coopetition_file.name))
    lines.append("submitted-by: %s" % submission.participant.user.username)
    lines.append("submitted-at: %s" % submission.submitted_at.replace(microsecond=0).isoformat())
    lines.append("competition-submission: %s" % submission.submission_number)
    lines.append("competition-phase: %s" % submission.phase.phasenumber)
    is_automatic_submission = False
    if submission.phase.auto_migration:
        # If this phase has auto_migration and this submission is the first in the phase, it is an automatic submission!
        submissions_this_phase = CompetitionSubmission.objects.filter(
            phase=submission.phase,
            participant=submission.participant
        ).count()
        is_automatic_submission = submissions_this_phase == 1

    lines.append("automatic-submission: %s" % is_automatic_submission)
    submission.inputfile.save('input.txt', ContentFile('\n'.join(lines).encode('utf-8')))


    # Generate metadata-only bundle describing the computation.
    lines = []
    program_value = submission.phase.scoring_program.name
    if len(program_value) > 0:
        lines.append("program: %s" % _make_url_sassy(program_value))
    else:
        raise ValueError("Program is missing.")
    lines.append("input: %s" % _make_url_sassy(submission.inputfile.name))
    lines.append("stdout: %s" % _make_url_sassy(submission.stdout_file.name, permission='w'))
    lines.append("stderr: %s" % _make_url_sassy(submission.stderr_file.name, permission='w'))
    lines.append("private_output: %s" % _make_url_sassy(submission.private_output_file.name, permission='w'))
    lines.append("output: %s" % _make_url_sassy(submission.output_file.name, permission='w'))
    submission.runfile.save('run.txt', ContentFile('\n'.join(lines).encode('utf-8')))

    # Create stdout.txt & stderr.txt
    if has_generated_predictions == False:
        username = submission.participant.user.username
        lines = ["Standard output for submission #{0} by {1}.".format(submission.submission_number, username), ""]
        submission.stdout_file.save('stdout.txt', ContentFile('\n'.join(lines).encode('utf-8')))
        lines = ["Standard error for submission #{0} by {1}.".format(submission.submission_number, username), ""]
        submission.stderr_file.save('stderr.txt', ContentFile('\n'.join(lines).encode('utf-8')))
    # Update workflow state
    state['score'] = job_id
    submission.execution_key = json.dumps(state)

    # Pre-save files so we can overwrite their names later
    submission.output_file.save('output_file.zip', ContentFile(''.encode('utf-8')))
    submission.private_output_file.save('private_output_file.zip', ContentFile(''.encode('utf-8')))
    submission.detailed_results_file.save('detailed_results_file.html', ContentFile(''.encode('utf-8')))
    submission.save()
    # Submit the request to the computation service
    _prepare_compute_worker_run(job_id, submission, is_prediction=False)

    if has_generated_predictions == False:
        _set_submission_status(submission.id, CompetitionSubmissionStatus.SUBMITTED)

    time_elapsed = time.time() - start
    logger.info("It took: %f seconds to run" % time_elapsed)


class SubmissionUpdateException(Exception):
    """Defines an exception that occurs during the update of a CompetitionSubmission object."""
    def __init__(self, submission, inner_exception):
        super(SubmissionUpdateException, self).__init__(inner_exception.message)
        self.submission = submission
        self.inner_exception = inner_exception


@task(queue='submission-updates')
def update_submission(job_id, args, secret):
    """
    A task to update the status of a submission in a competition.

    job_id: The ID of the job.
    args: A dictionary with the arguments for the task. Expected items are:
        args['status']: The evaluation status, which is one of 'running', 'finished' or 'failed'.
    """

    def _update_submission(submission, status, job_id, traceback=None, metadata=None):
        """
        Updates the status of a submission.

        submission: The CompetitionSubmission object to update.
        status: The new status string: 'running', 'finished' or 'failed'.
        job_id: The job ID used to track the progress of the evaluation.
        """

        state = {}
        if len(submission.execution_key) > 0:
            logger.debug("update_submission_task loading state: %s", submission.execution_key)
            state = json.loads(submission.execution_key)
            logger.debug("update_submission_task state = %s" % submission.execution_key)

        if metadata:
            is_predict = 'score' not in state
            sub_metadata, created = CompetitionSubmissionMetadata.objects.get_or_create(
                is_predict=is_predict,
                is_scoring=not is_predict,
                submission=submission,
            )
            sub_metadata.__dict__.update(metadata)
            sub_metadata.save()
            logger.debug("saving extra metadata, was a new object created? %s" % created)

        if status == 'running':
            _set_submission_status(submission.id, CompetitionSubmissionStatus.RUNNING)
            return Job.RUNNING

        if status == 'finished':
            result = Job.FAILED
            if 'score' in state:
                logger.info("update_submission_task loading final scores (pk=%s)", submission.pk)
                logger.info("Retrieving output.zip and 'scores.txt' file (submission_id=%s)", submission.id)
                logger.info("Output.zip location=%s" % submission.output_file.file.name)

                ozip = ZipFile(io.BytesIO(submission.output_file.read()))

                scores = None
                try:
                    scores = open(ozip.extract('scores.txt'), 'r').read()
                except Exception:
                    logger.info("Scores.txt not found, unable to process submission: %s (submission_id=%s)", status, submission.id)
                    _set_submission_status(submission.id, CompetitionSubmissionStatus.FAILED)
                    return Job.FAILED

                logger.info("Processing scores... (submission_id=%s)", submission.id)
                for line in scores.split("\n"):
                    if len(line) > 0:
                        label, value = line.split(":")
                        logger.info("Attempting to submit score %s:%s" % (label, value))
                        try:
                            scoredef = SubmissionScoreDef.objects.get(competition=submission.phase.competition,
                                                                      key=label.strip())
                            SubmissionScore.objects.create(result=submission, scoredef=scoredef, value=float(value))
                        except SubmissionScoreDef.DoesNotExist:
                            logger.info("Score %s does not exist (submission_id=%s)", label, submission.id)
                logger.info("Done processing scores... (submission_id=%s)", submission.id)
                _set_submission_status(submission.id, CompetitionSubmissionStatus.FINISHED)

                if submission.phase.delete_submissions_except_best_and_last:
                    delete_submissions_except_best_and_or_last(submission)

                # Automatically submit to the leaderboard?
                if submission.phase.is_blind and not submission.phase.force_best_submission_to_leaderboard:
                    logger.info("Adding to leaderboard... (submission_id=%s)", submission.id)
                    add_submission_to_leaderboard(submission)
                    logger.info("Leaderboard updated with latest submission (submission_id=%s)", submission.id)

                if submission.phase.competition.force_submission_to_leaderboard and not submission.phase.force_best_submission_to_leaderboard:
                    add_submission_to_leaderboard(submission)
                    logger.info("Force submission added submission to leaderboard (submission_id=%s)", submission.id)

                if submission.phase.force_best_submission_to_leaderboard:
                    push_submission_to_leaderboard_if_best(submission)
                result = Job.FINISHED

                if submission.participant.user.email_on_submission_finished_successfully:
                    email = submission.participant.user.email
                    site_url = "https://%s%s" % (Site.objects.get_current().domain, submission.phase.competition.get_absolute_url())
                    send_mail(
                        'Submission has finished successfully!',
                        'Your submission to the competition "%s" has finished successfully! View it here: %s' %
                        (submission.phase.competition.title, site_url),
                        settings.DEFAULT_FROM_EMAIL,
                        [email],
                        fail_silently=False
                    )
            else:
                logger.debug("update_submission_task entering scoring phase (pk=%s)", submission.pk)
                # url_name = pathname2url(submission_prediction_output_filename(submission))
                # submission.prediction_output_file.name = url_name
                # submission.prediction_stderr_file.name = pathname2url(predict_submission_stdout_filename(submission))
                # submission.prediction_stdout_file.name = pathname2url(predict_submission_stderr_filename(submission))
                # submission.save()
                try:
                    score(submission, job_id)
                    result = Job.RUNNING
                    logger.debug("update_submission_task scoring phase entered (pk=%s)", submission.pk)
                except Exception:
                    logger.exception("update_submission_task failed to enter scoring phase (pk=%s)", submission.pk)
            return result

        if status != 'failed':
            logger.error("Invalid status: %s (submission_id=%s)", status, submission.id)

        if traceback:
            submission.exception_details = traceback
            submission.save()

        _set_submission_status(submission.id, CompetitionSubmissionStatus.FAILED)

    def handle_update_exception(job, ex):
        """
        Handles exception that occur while attempting to update the status of a submission.

        job: The running Job instance.
        ex: The exception. The handler tries to acquire the CompetitionSubmission instance
            from a submission attribute on the exception.
        """
        try:
            submission = ex.submission
            _set_submission_status(submission.id, CompetitionSubmissionStatus.FAILED)
        except Exception:
            logger.exception("Unable to set the submission status to Failed (job_id=%s)", job.id)
        return JobTaskResult(status=Job.FAILED)

    def update_it(job):
        """Updates the database to reflect the state of the evaluation of the given competition submission."""
        logger.debug("Entering update_submission_task::update_it (job_id=%s)", job.id)
        if job.task_type != 'evaluate_submission':
            raise ValueError("Job has incorrect task_type (job.task_type=%s)", job.task_type)
        task_args = job.get_task_args()
        submission_id = task_args['submission_id']
        logger.debug("Looking for submission (job_id=%s, submission_id=%s)", job.id, submission_id)

        try:
            submission = CompetitionSubmission.objects.get(pk=submission_id)
        except CompetitionSubmission.DoesNotExist:
            return

        if secret != submission.secret:
            raise SubmissionUpdateException(submission, "Password does not match")

        status = args['status']
        logger.debug("Ready to update submission status (job_id=%s, submission_id=%s, status=%s)",
                     job.id, submission_id, status)
        result = None
        try:
            traceback = None
            metadata = None
            if 'extra' in args:
                if 'traceback' in args['extra']:
                    traceback = args['extra']['traceback']

                if 'metadata' in args['extra']:
                    metadata = args['extra']['metadata']

            result = _update_submission(submission, status, job.id, traceback, metadata)
        except Exception as e:
            logger.exception("Failed to update submission (job_id=%s, submission_id=%s, status=%s)",
                             job.id, submission_id, status)
            raise SubmissionUpdateException(submission, e)
        return JobTaskResult(status=result)

    run_job_task(job_id, update_it, handle_update_exception)


@task(queue='site-worker', soft_time_limit=60 * 60 * 1)
def re_run_all_submissions_in_phase(phase_pk):
    phase = CompetitionPhase.objects.get(id=phase_pk)

    # Remove duplicate submissions this ugly way because MySQL distinct doesn't work...
    submissions_with_duplicates = CompetitionSubmission.objects.filter(phase=phase)
    submissions_without_duplicates = []
    file_names_seen = []

    for submission in submissions_with_duplicates:
        if submission.file.name not in file_names_seen:
            if settings.USE_AWS:
                file_names_seen.append(submission.s3_file)
            else:
                file_names_seen.append(submission.file.name)
            submissions_without_duplicates.append(submission)

    for submission in submissions_without_duplicates:
        if settings.USE_AWS:
            file_kwarg = {'s3_file': submission.s3_file}
        else:
            file_kwarg = {'file': submission.file}

        new_submission = CompetitionSubmission(
            participant=submission.participant,
            phase=submission.phase,
            docker_image=submission.docker_image,
            **file_kwarg
        )
        new_submission.save(ignore_submission_limits=True)

        evaluate_submission.apply_async((new_submission.pk, submission.phase.is_scoring_only))


@task(queue='site-worker')
def evaluate_submission(submission_id, is_scoring_only):
    """
    Starts the process of evaluating a user's submission to a competition.

    submission_id: The ID of the CompetitionSubmission object.
    is_scoring_only: True to skip the prediction step.

    Returns a Job object which can be used to track the progress of the operation.
    """
    task_args = {'submission_id': submission_id, 'predict': (not is_scoring_only)}
    job = Job.objects.create_job('evaluate_submission', task_args)
    job_id = job.pk

    logger.debug("evaluate_submission begins (job_id=%s)", job_id)
    submission_id = task_args['submission_id']
    logger.debug("evaluate_submission submission_id=%s (job_id=%s)", submission_id, job_id)
    predict_and_score = task_args['predict'] == True
    logger.debug("evaluate_submission predict_and_score=%s (job_id=%s)", predict_and_score, job_id)

    try:
        submission = CompetitionSubmission.objects.get(pk=submission_id)
    except CompetitionSubmission.DoesNotExist:
        return

    task_name, task_func = ('prediction', predict) if predict_and_score else ('scoring', score)
    try:
        logger.debug("evaluate_submission dispatching %s task (submission_id=%s, job_id=%s)",
                    task_name, submission_id, job_id)
        task_func(submission, job_id)
        logger.debug("evaluate_submission dispatched %s task (submission_id=%s, job_id=%s)",
                    task_name, submission_id, job_id)
    except Exception:
        logger.exception("evaluate_submission dispatch failed (job_id=%s, submission_id=%s)",
                         job_id, submission_id)
        update_submission.apply_async((job_id, {'status': 'failed'}, submission.secret))
    logger.debug("evaluate_submission ends (job_id=%s)", job_id)


@task(queue='site-worker')
def send_mass_email(competition_pk, body=None, subject=None, from_email=None, to_emails=None):
    logger.info("Sending emails to: {}".format(to_emails))
    competition = Competition.objects.get(pk=competition_pk)
    from_email = from_email or settings.DEFAULT_FROM_EMAIL

    site = Site.objects.get_current()

    context = {"competition": competition, "body": body, "site": site, "mass_email": True}
    text = render_to_string("emails/notifications/participation_organizer_direct_email.txt", context)
    html = render_to_string("emails/notifications/participation_organizer_direct_email.html", context)

    message = EmailMultiAlternatives(subject, text, from_email, to=None, bcc=to_emails)
    message.attach_alternative(html, 'text/html')
    message.send()

    logger.info("Finished sending emails.")


@task(queue='site-worker')
def do_chahub_retries(limit=None):
    if not settings.CHAHUB_API_URL:
        return

    logger.info("Checking whether ChaHub is online before sending retries")
    try:
        response = requests.get(settings.CHAHUB_API_URL)
        if response.status_code != 200:
            return
    except requests.exceptions.RequestException:
        # This base exception works for HTTP errors, Connection errors, etc.
        return

    logger.info("ChaHub is online, checking for objects needing to be re-sent to ChaHub")
    chahub_models = inheritors(ChaHubSaveMixin)
    for model in chahub_models:
        # Special case for competition model manager, with deleted competitions
        if hasattr(model.objects, 'get_all_objects'):
            needs_retry = model.objects.get_all_objects().filter(chahub_needs_retry=True)
        else:
            needs_retry = model.objects.filter(chahub_needs_retry=True)

        if limit:
            needs_retry = needs_retry[:limit]
        for instance in needs_retry:
            # Saving forces chahub update
            instance.save(force_to_chahub=True)


@task(queue='site-worker')
def send_chahub_general_stats():
    if settings.DATABASES.get('default').get('ENGINE') == 'django.db.backends.postgresql_psycopg2':
        # Only Postgres supports 'distinct', so if we can use the database, if not use some Python Set magic
        # Order by creator because "SELECT DISTINCT ON expressions must match initial ORDER BY expressions"
        organizer_count = Competition.objects.order_by('creator').distinct('creator').count()
    else:
        users_with_competitions = list(ClUser.objects.filter(competitioninfo_creator__isnull=False))
        user_set = set(users_with_competitions)
        # Only unique users that have competitions
        organizer_count = len(user_set)
    approved_status = ParticipantStatus.objects.get(codename=ParticipantStatus.APPROVED)
    data = {
        'competition_count': Competition.objects.filter(published=True).count(),
        'dataset_count': OrganizerDataSet.objects.count(),
        'participant_count': CompetitionParticipant.objects.filter(status=approved_status).count(),
        'submission_count': CompetitionSubmission.objects.count(),
        'user_count': ClUser.objects.count(),
        'organizer_count': organizer_count
    }

    try:
        send_to_chahub('producers/{}/'.format(settings.CHAHUB_PRODUCER_ID), data, update=True)
    except requests.ConnectionError:
        logger.info("There was a problem reaching Chahub, it is currently offline. Re-trying in 5 minutes.")
        send_chahub_general_stats.apply_async(eta=timezone.now() + timedelta(minutes=5))


@task(queue='site-worker')
def send_chahub_updates():
    competitions = Competition.objects.filter(published=True).annotate(participant_count=Count('participants'))
    for comp in competitions:
        # saving generates new participant_count -- will be sent if it is different from
        # what was sent last time.
        comp.save()


@task(queue='site-worker', soft_time_limit=60*60*12) # 12 hours
def create_storage_analytics_snapshot():
    logger.info("Task create_storage_analytics_snapshot started")
    starting_time = time.process_time()

    # Retrieve the last storage usage history point
    bucket = BundleStorage.bucket
    last_storage_usage_history_point = StorageUsageHistory.objects.filter(bucket_name=bucket.name).order_by('-at_date').first()

    current_datetime = datetime.datetime.now(datetime.timezone.utc)
    last_storage_usage_history_date = last_storage_usage_history_point.at_date if last_storage_usage_history_point else current_datetime - datetime.timedelta(days=1000)

    # Prepare the storage usage history points and total usage
    days_count = int((current_datetime - last_storage_usage_history_date).days)
    days = range(1, days_count + 1)
    usage_at_date = {last_storage_usage_history_date + datetime.timedelta(day): 0 for day in days}
    total_usage = 0

    if settings.USE_AWS:
        for obj in bucket.objects.all():
            size = obj.size
            total_usage += size
            for date in usage_at_date:
                if obj.last_modified <= date:
                    usage_at_date[date] += size
    else:
        found_files = set(storage_recursive_find(BundleStorage))
        for file_path in found_files:
            total_usage += BundleStorage.size(file_path) or 0
            if BundleStorage.modified_time(file_path) <= date:
                usage_at_date[date] += BundleStorage.size(file_path) or 0
    
    # Competitions details
    competitions = Competition.objects.all().reverse()
    for competition in competitions:
        competition_size_data = get_competition_size_data(competition)
        competition_size_data['competition_id'] = competition_size_data['id']
        competition_size_data.pop('id')
        default = {
            'title': competition_size_data['title'],
            'creator': competition_size_data['creator'],
            'is_active': competition_size_data['is_active'],
            'submissions': competition_size_data['submissions'],
            'datasets': competition_size_data['datasets'],
            'dumps': competition_size_data['dumps'],
            'bundle': competition_size_data['bundle'],
            'total': competition_size_data['total']
        }
        CompetitionStorageDataPoint.objects.update_or_create(competition_id=competition_size_data['competition_id'], defaults=default)
    
    # Users details
    users = ClUser.objects.order_by('?').exclude(id=-1).exclude(username='AnonymousUser')
    for user in users:
        user_usage = user.get_storage_use_data()
        user_usage['user_id'] = user_usage['id']
        user_usage.pop('id')
        default = {
            'email': user_usage['email'],
            'username': user_usage['username'],
            'competitions_total': user_usage['competitions_total'],
            'datasets_total': user_usage['datasets_total'],
            'submissions_total': user_usage['submissions_total'],
            'total': user_usage['total']
        }
        UserStorageDataPoint.objects.update_or_create(user_id=user_usage['user_id'], defaults=default)

    # Save the storage usage history points
    for date, usage in usage_at_date.items():
        storage_usage_history_point = {
            'bucket_name': bucket.name,
            'at_date': date,
            'usage': usage
        }
        StorageUsageHistory.objects.create(**storage_usage_history_point)

    # Save the storage snapshot
    storage_snapshot = {
            'bucket_name': bucket.name,
            'total_use': total_usage
        }
    StorageSnapshot.objects.create(**storage_snapshot)

    elapsed_time = time.process_time() - starting_time
    logger.info("Task create_storage_analytics_snapshot stoped. Duration = {:.3f} seconds".format(elapsed_time))


@task(queue='site-worker')
def reset_computed_storage_analytics():
    logger.info("Task reset_computed_storage_analytics started")
    starting_time = time.process_time()

    # Reset the value of all computed sizes so they will be re-computed again without any shifting on the next run of the storage analytics task
    CompetitionSubmission.objects.all().update(sub_size=0)

    elapsed_time = time.process_time() - starting_time
    logger.info("Task reset_computed_storage_analytics stoped. Duration = {:.3f} seconds".format(elapsed_time))


@task(queue='site-worker')
def do_phase_migrations():
    competitions = Competition.objects.filter(is_migrating=False)
    logger.info("Checking {} competitions for phase migrations.".format(len(competitions)))
    for c in competitions:
        c.check_future_phase_sumbmissions()


def _get_or_default(obj, field_name, default=None):
    if hasattr(obj, field_name):
        if getattr(obj, field_name) != None:
            return getattr(obj, field_name)
    if default != None:
        return default
    elif obj._meta.get_field(field_name).get_default() != None:
        return obj._meta.get_field(field_name).get_default()
    else:
        return None


@task(queue='site-worker', soft_time_limit=60 * 60 * 24)
def make_modified_bundle(competition_pk, exclude_datasets_flag):
    # The following lines help dump this in a nice format
    _mapping_tag = yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG

    def dict_representer(dumper, data):
        return dumper.represent_dict(iter(data.items()))

    def dict_constructor(loader, node):
        return OrderedDict(loader.construct_pairs(node))
    # Credit to miracle2k on Github for orderdict safe dump

    def represent_odict(dump, tag, mapping, flow_style=None):
        """Like BaseRepresenter.represent_mapping, but does not issue the sort().
        """
        value = []
        node = yaml.MappingNode(tag, value, flow_style=flow_style)
        if dump.alias_key is not None:
            dump.represented_objects[dump.alias_key] = node
        best_style = True
        if hasattr(mapping, 'items'):
            mapping = list(mapping.items())
        for item_key, item_value in mapping:
            node_key = dump.represent_data(item_key)
            node_value = dump.represent_data(item_value)
            if not (isinstance(node_key, yaml.ScalarNode) and not node_key.style):
                best_style = False
            if not (isinstance(node_value, yaml.ScalarNode) and not node_value.style):
                best_style = False
            value.append((node_key, node_value))
        if flow_style is None:
            if dump.default_flow_style is not None:
                node.flow_style = dump.default_flow_style
            else:
                node.flow_style = best_style
        return node
    yaml.SafeDumper.add_representer(OrderedDict,
                                    lambda dumper, value: represent_odict(dumper, 'tag:yaml.org,2002:map', value))
    # Following line supresses the broadexception warning. We catch and do a traceback for now from logs.
    # noinspection PyBroadException
    try:
        # SafeRepresenter does not have represent_unicode anymore. Competition dumps still seem to be working.
        # yaml.add_representer(str, SafeRepresenter.represent_unicode)
        yaml.add_representer(OrderedDict, dict_representer)
        yaml.add_constructor(_mapping_tag, dict_constructor)

        competition = models.Competition.objects.get(pk=competition_pk)
        logger.info("Creating Competion dump")
        temp_comp_dump = CompetitionDump.objects.create(competition=competition)
        yaml_data = OrderedDict()
        yaml_data['title'] = _get_or_default(competition, 'title')
        yaml_data['description'] = competition.description.replace("/n", "").replace("\"", "").strip() if competition.description else None
        temp_comp_dump.status = "Adding end-date"
        temp_comp_dump.save()
        logger.info("Adding end-date")
        yaml_data['start_date'] = _get_or_default(competition, 'start_date')
        yaml_data['end_date'] = _get_or_default(competition, 'end_date')
        yaml_data['competition_docker_image'] = _get_or_default(competition, 'competition_docker_image')
        if competition.image:
            yaml_data['image'] = 'logo.png'
        else:
            logger.info("No image for competition.")
        yaml_data['has_registration'] = _get_or_default(competition, 'has_registration')
        yaml_data['force_submission_to_leaderboard'] = _get_or_default(competition, 'force_submission_to_leaderboard')
        yaml_data['disallow_leaderboard_modifying'] = _get_or_default(competition, 'disallow_leaderboard_modifying')
        yaml_data['enable_detailed_results'] = _get_or_default(competition, 'enable_detailed_results')
        temp_comp_dump.status = "Adding admins"
        temp_comp_dump.save()
        yaml_data['admin_names'] = ','.join(list(competition.admins.all().values_list('username', flat=True))) if competition.admins.all() else None
        yaml_data['html'] = dict()
        yaml_data['phases'] = {}
        zip_buffer = io.BytesIO()
        zip_name = "{0}.zip".format(competition.title)
        zip_file = zipfile.ZipFile(zip_buffer, "w")
        for p in competition.pagecontent.pages.all():
            temp_comp_dump.status = "Adding {}.html".format(p.codename)
            temp_comp_dump.save()
            logger.info("Adding HTML")
            if p.codename in list(yaml_data["html"].keys()) or p.codename == 'terms_and_conditions' or p.codename == 'get_data' or p.codename == 'submit_results':
                if p.codename == 'terms_and_conditions':
                    # overwrite this for consistency
                    p.codename = 'terms'
                    yaml_data['html'][p.codename] = p.codename + '.html'
                    zip_file.writestr(yaml_data["html"][p.codename], p.html.encode("utf-8"))
                if p.codename == 'get_data':
                    # overwrite for consistency
                    p.codename = 'data'
                    yaml_data['html'][p.codename] = p.codename + '.html'
                    zip_file.writestr(yaml_data["html"][p.codename], p.html.encode("utf-8"))
                # Do not include submit_results.
                if p.codename == 'submit_results':
                    pass
            else:
                yaml_data['html'][p.codename] = p.codename + '.html'
                zip_file.writestr(yaml_data["html"][p.codename], p.html.encode("utf-8"))
        file_cache = {}
        for index, phase in enumerate(competition.phases.all()):
            temp_comp_dump.status = "Adding phase {0}".format(phase.phasenumber)
            temp_comp_dump.save()
            logger.info("Adding phase")
            phase_dict = dict()
            phase_dict['phasenumber'] = _get_or_default(phase, 'phasenumber', 999)
            phase_dict['label'] = _get_or_default(phase, 'label')
            phase_dict['description'] = _get_or_default(phase, 'description')
            phase_dict['start_date'] = _get_or_default(phase, 'start_date')
            phase_dict['max_submissions'] = _get_or_default(phase, 'max_submissions')
            phase_dict['color'] = _get_or_default(phase, 'color', 'white')
            phase_dict['max_submissions_per_day'] = _get_or_default(phase, 'max_submissions_per_day')
            phase_dict['is_scoring_only'] = _get_or_default(phase, 'is_scoring_only')
            phase_dict['auto_migration'] = _get_or_default(phase, 'auto_migration')
            # Write the programs/data to zip
            data_types = ['reference_data', 'scoring_program', 'input_data', 'starting_kit', 'public_data', 'ingestion_program']
            try:
                for data_type in data_types:
                    logger.info("Current data type is {}".format(data_type))
                    if hasattr(phase, data_type):
                        data_field = getattr(phase, data_type)
                        if data_field:
                            if data_field.file.name not in list(file_cache.keys()):
                                if exclude_datasets_flag:
                                    data_field = getattr(phase, data_type + '_organizer_dataset')
                                    phase_dict[data_type] = str(data_field.key)
                                    file_name = "{}_{}.zip".format(data_type, phase.phasenumber)
                                    file_cache[data_field.name] = {
                                        'name': file_name
                                    }
                                else:
                                    file_name = "{}_{}.zip".format(data_type, phase.phasenumber)
                                    phase_dict[data_type] = file_name
                                    file_cache[data_field.file.name] = {
                                        'name': file_name
                                    }
                                    zip_file.writestr(file_name, data_field.read())
                            else:
                                if exclude_datasets_flag:
                                    data_field = getattr(phase, data_type + '_organizer_dataset')
                                    phase_dict[data_type] = str(data_field.key)
                                else:
                                    file_name = file_cache[str(data_field.name)]['name']
                                    phase_dict[data_type] = file_name
            except ValueError:
                logger.info("Failed to retrieve the file.")
            datasets = phase.datasets.all()
            if datasets:
                phase_dict['datasets'] = dict()
                temp_comp_dump.status = "Adding datasets"
                temp_comp_dump.save()
                logger.info("Adding dataset")
                for data_set_index, data_set in enumerate(datasets):
                    phase_dict['datasets'][data_set_index] = {
                        'name': data_set.datafile.name,
                        'url': data_set.datafile.source_url,
                        'description': data_set.description
                    }
            yaml_data['phases'][index] = phase_dict
        yaml_data["leaderboard"] = dict()
        logger.info("Adding leaderboard.")
        leaderboards_dict = dict()
        columns_dictionary = dict()
        for index, submission_result_group in enumerate(SubmissionResultGroup.objects.filter(competition=competition)):
            logger.info("Adding a submission result group.")
            result_group = submission_result_group
            result_group_key = result_group.key
            leaderboards_dict[result_group_key] = {
                'label': submission_result_group.label,
                'rank': submission_result_group.ordering,
            }
            for index_score_def, submission_score_def_group in enumerate(SubmissionScoreDefGroup.objects.filter(group=submission_result_group)):
                logger.info("Adding a submission score def group.")
                score_def = submission_score_def_group.scoredef
                score_def_key = score_def.key
                columns_dictionary[score_def_key] = {
                    'leaderboard': leaderboards_dict[submission_result_group.label],
                    'label': score_def.label,
                    'rank': score_def.ordering,
                    'sort': score_def.sorting,
                }
        logger.info("YAML finalizing")
        yaml_data["leaderboard"]['leaderboards'] = leaderboards_dict
        yaml_data["leaderboard"]['columns'] = columns_dictionary
        logger.info("Done with leaderboard")
        temp_comp_dump.status = "Finalizing"
        temp_comp_dump.save()
        logger.info("Finalizing")
        comp_yaml_my_dump = yaml.safe_dump(yaml_data, default_flow_style=False, allow_unicode=True, encoding="utf-8")
        if competition.image:
            zip_file.writestr(yaml_data["image"], competition.image.file.read())
        else:
            logger.info("No image for competition.")
        zip_file.writestr("competition.yaml", comp_yaml_my_dump)
        zip_file.close()
        logger.info("Stored Zip buffer yaml dump, and image")
        logger.info("Attempting to save ZIP")
        temp_comp_data = ContentFile(zip_buffer.getvalue())
        save_success = False
        while not save_success:
            counter = 0
            logger.info("Attempting to save new object.")
            try:
                temp_comp_dump.data_file.save(zip_name, temp_comp_data)
                save_success = True
            except SoftTimeLimitExceeded:
                logger.info("Failed to save object, retrying.")
                counter += 1
                continue
            if counter == 5:
                temp_comp_dump.status = "Failed"
                temp_comp_dump.save()
                logger.info("Failed to save object after 5 tries. Stopping.")
                save_success = True
        logger.info("Saved zip file to Competition dump")
        temp_comp_dump.status = "Finished"
        temp_comp_dump.save()
        logger.info("Set status to finished")
    except:
        logger.info("There was an error making a Competition dump")
        logger.info(traceback.format_exc())
        temp_comp_dump.status = "Failed"
        temp_comp_dump.save()
