import re

import logging
import requests
from django.conf import settings
from django.core.files.storage import get_storage_class

logger = logging.getLogger(__name__)

StorageClass = get_storage_class(settings.DEFAULT_FILE_STORAGE)

if hasattr(settings, 'USE_AWS') and settings.USE_AWS:
    BundleStorage = StorageClass(bucket=settings.AWS_STORAGE_PRIVATE_BUCKET_NAME)
    PublicStorage = StorageClass(bucket=settings.AWS_STORAGE_BUCKET_NAME)
elif hasattr(settings, 'BUNDLE_AZURE_ACCOUNT_NAME') and settings.BUNDLE_AZURE_ACCOUNT_NAME:
    BundleStorage = StorageClass(account_name=settings.BUNDLE_AZURE_ACCOUNT_NAME,
                                 account_key=settings.BUNDLE_AZURE_ACCOUNT_KEY,
                                 azure_container=settings.BUNDLE_AZURE_CONTAINER)

    PublicStorage = StorageClass(account_name=settings.AZURE_ACCOUNT_NAME,
                                 account_key=settings.AZURE_ACCOUNT_KEY,
                                 azure_container=settings.AZURE_CONTAINER)
else:
    # No storage provided, like in a test, let's just do something basic
    BundleStorage = StorageClass()
    PublicStorage = StorageClass()


def clean_html_script(html_content):
    # Finds <script and everything between /script>. No scripts for you.
    return re.sub('(<script)(\s*?\S*?)*?(/script>)', "", str(html_content))


def docker_image_clean(image_name):
    if not image_name:
        return ""
    # Remove all excess whitespaces on edges, split on spaces and grab the first word.
    # Wraps in double quotes so bash cannot interpret as an exec
    image_name = '"{}"'.format(image_name.strip().split(' ')[0])
    # Regex acts as a whitelist here. Only alphanumerics and the following symbols are allowed: / . : -.
    # If any not allowed are found, replaced with second argument to sub.
    image_name = re.sub('[^0-9a-zA-Z/.:\-_]+', '', image_name)
    return image_name


def check_bad_scores(score_dict):
    bad_score_count = 0
    bad_scores = list()
    for score in score_dict:
        for subm in score['scores']:
            for i in range(len(subm)):
                if type(subm[i]) is dict:
                    for k, v in subm[i].items():
                        if k == 'values':
                            for result in v:
                                for result_key, result_value in result.items():
                                    if result_value == 'NaN' or result_value == '-':
                                        bad_score_count += 1
                                        bad_scores.append(result)
    return bad_score_count, bad_scores


def _put_blob(url, file_path):
    requests.put(
        url,
        data=open(file_path, 'rb'),
        headers={
            # For Azure but doesn't hurt AWS
            'x-ms-blob-type': 'BlockBlob',
        }
    )


def push_submission_to_leaderboard_if_best(submission):
    from apps.web.models import PhaseLeaderBoard, PhaseLeaderBoardEntry, add_submission_to_leaderboard
    # In this phase get the submission score from the column with the lowest ordering
    score_def = submission.get_default_score_def()
    lb = PhaseLeaderBoard.objects.get(phase=submission.phase)

    # Get our leaderboard entries: Related Submissions should be in our participant's submissions,
    # and the leaderboard should be the one attached to our phase
    entries = PhaseLeaderBoardEntry.objects.filter(result__in=submission.participant.submissions.all(), board=lb)
    submissions = [(entry.result, entry.result.get_default_score()) for entry in entries]
    sorted_list = sorted(submissions, key=lambda x: x[1])
    if sorted_list:
        top_sub, top_score = sorted_list[0]
        score_value = submission.get_default_score()
        if score_def.sorting == 'asc':
            # The last value in ascending is the top score, 1 beats 3
            if score_value <= top_score:
                add_submission_to_leaderboard(submission)
                logger.info("Force best submission added submission to leaderboard in ascending order "
                            "(submission_id=%s, top_score=%s, score=%s)", submission.id, top_score,
                            score_value)
        elif score_def.sorting == 'desc':
            # The first value in descending is the top score, 3 beats 1
            if score_value >= top_score:
                add_submission_to_leaderboard(submission)
                logger.info(
                    "Force best submission added submission to leaderboard in descending order "
                    "(submission_id=%s, top_score=%s, score=%s)", submission.id, top_score, score_value)
    else:
        add_submission_to_leaderboard(submission)
        logger.info(
            "Force best submission added submission: {0} with score: {1} to leaderboard: {2}"
            " because no submission was present".format(
                submission, submission.get_default_score(), lb)
        )


def inheritors(klass):
    subclasses = set()
    work = [klass]
    while work:
        parent = work.pop()
        for child in parent.__subclasses__():
            if child not in subclasses:
                subclasses.add(child)
                work.append(child)
    return subclasses

def get_object_base_url(object, attr):
    if settings.USE_AWS:
        # Boto3 does not like receiving an empty path.
        return getattr(object, attr).storage.url(' ').replace("%20", "")
    else:
        return getattr(object, attr).storage.url('')
