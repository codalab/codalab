"""
Defines models for this Django app.
"""
import json
import logging
import threading
import traceback

from codalabtools.azure_extensions import AzureServiceBusQueue
from django.conf import settings
from django.db import (models,
                       transaction)

logger = logging.getLogger(__name__)

# Queues

_lock = threading.Lock()
_queues = {}

def getQueue(name=None):
    """
    Returns a Queue given its name.

    :rtype queue: Azure Service Bus Queue
    """
    if name is None:
        name = settings.SBS_RESPONSE_QUEUE
    if name in _queues:
        return _queues[name]

    queue = None
    with _lock:
        queue = AzureServiceBusQueue(settings.SBS_NAMESPACE,
                                     settings.SBS_ACCOUNT_KEY,
                                     settings.SBS_ISSUER,
                                     settings.SBS_SHARED_ACCESS_KEY_NAME,
                                     settings.SBS_SHARED_ACCESS_KEY_VALUE,
                                     name)
        _queues[name] = queue

    return queue


# Jobs

class JobManager(models.Manager):
    """
    Adds job-specific convenience methods to the default Django Manager.
    """

    def create_job(self, task_type, task_args):
        """
        Creates a job.

        :param task_type: A string identifying the type of task to carry out.
        :param task_args: An object defining the task's input arguments. The object must allow
            serialization to a JSON string using `json.dumps(obj)`. A None value is acceptable
            if the task requires no input arguments.
        """
        task_args_json = "" if task_args is None else json.dumps(task_args)
        job = self.create(task_type=task_type, task_args_json=task_args_json)
        return job

    def create_and_dispatch_job(self, task_type, task_args, queue_name=None):
        """
        Creates a job and dispatches it to the specified queue.

        :param task_type: A string identifying the type of task to carry out.
        :param task_args: An object defining the task's input arguments. The object must allow
            serialization to a JSON string using `json.dumps(obj)`. A None value is acceptable
            if the task requires no input arguments.
        :param queue_name: The name of the target Queue. If name is None, the queue connected to
            the site workers is used.
        """
        job = self.create_job(task_type, task_args)
        getQueue(queue_name).send_message(job.create_json_message())
        return job


class Job(models.Model):
    """
    Defines a job which will carry out a long running task.
    """

    # Possible status codes
    PENDING = 0
    RUNNING = 1
    FINISHED = 2
    FAILED = 3
    # Status friendly code and display text
    STATUS_BY_CODE = {
        PENDING: { 'code_name': 'pending', 'display_text': 'Pending' },
        RUNNING: { 'code_name': 'running', 'display_text': 'Running' },
        FINISHED: { 'code_name': 'finished', 'display_text': 'Finished' },
        FAILED: { 'code_name': 'failed', 'display_text': 'Failed' }
    }
    # Reverse map to get integer code from friendly code name
    STATUS_BY_CODE_NAME = { v['code_name']: k  for (k, v) in STATUS_BY_CODE.items() }

    created = models.DateTimeField('Date of creation', auto_now_add=True)
    updated = models.DateTimeField('Date of last update', auto_now=True)
    status = models.PositiveIntegerField('Status', default=PENDING, db_index=True)
    task_type = models.CharField('Task type', max_length=256)
    task_args_json = models.TextField('JSON-encoded task arguments', blank=True)
    task_info_json = models.TextField('JSON-encoded task information', blank=True)

    objects = JobManager()

    def __unicode__(self):
        return "Job(pk={0})".format(self.pk)

    def get_status_code_name(self):
        """
        :return: The code name of this job's status.

        """
        return Job.STATUS_BY_CODE[self.status]['code_name']

    def get_task_args(self):
        """
        :return: Dictionary containing the task's arguments.
        """
        return json.loads(self.task_args_json) if len(self.task_args_json) > 0 else {}

    def get_task_info(self):
        """
        Gets the dictionary containing information about the task's progress or its outcome.
        """
        return json.loads(self.task_info_json) if len(self.task_info_json) > 0 else {}

    def can_transition_to(self, new_status):
        """
        Validates that the transition from the job's current status to the given new status is valid.

        :param new_status: Any valid job status.
        """
        if new_status in Job.STATUS_BY_CODE:
            if self.status == Job.FINISHED:
                return False
            if self.status == Job.FAILED:
                return False
            if self.status == Job.PENDING:
                return new_status != Job.PENDING
            if self.status == Job.RUNNING:
                return (new_status == Job.FINISHED) or (new_status == Job.FAILED)
        else:
            return False

    def create_json_message(self):
        """
        Gets the JSON-encoded message to describe the given job to a worker.
        """
        data = {"id": self.pk, "task_type": self.task_type}
        if len(self.task_args_json) > 0:
            data['task_args'] = json.loads(self.task_args_json)
        return json.dumps(data)

#
# Tasks
#


def update_job_status_task(job_id, args):
    """
    A task to update the status of a Job instance.

    :param job_id: The ID of the job to update.
    :param args: A dictionary with the arguments for the task.

    - **Required items are**::
        args['status']: friendly code name of the new status
    - **Optional items are**::
        args['info']: a dictionary containing custom information about the
        task's progress or outcome. The dictionary must be serializable
        to JSON via the built-in 'json.dumps' function.
    """
    status_code_name = args['status']
    logger.debug("Starting request to update job (id=%s) with new status (status_code_name=%s)",
                 job_id, status_code_name)
    status = Job.STATUS_BY_CODE_NAME[status_code_name]
    info_json = None
    if 'info' in args:
        info_json = json.dumps(args['info'])
    with transaction.atomic():
        job = Job.objects.select_for_update().get(pk=job_id)
        if job.can_transition_to(status):
            job.status = status
            if info_json is not None:
                job.task_info_json = info_json
            job.save()
            logger.info("Completed update for job id=%s. New status=%s.", job_id, job.status)
        else:
            logger.warning("Skipping update for job id=%s: invalid transition %s -> %s.", job_id, job.status, status)

class JobTaskResult(object):
    """
    Defines the result type expected from the computation method passed into the run_job_task function.

    :param status: A valid job status.
    :param info: Extra info about a task.
    """
    def __init__(self, status=None, info=None):
        self.status = status
        self.info = info
        self._result = None
        if status is not None:
            self._result = {'status': Job.STATUS_BY_CODE[status]['code_name']}
            if info is not None:
                self._result['info'] = info

    def get_dict(self):
        """
        Gets the result dictionary.
        """
        return self._result

def run_job_task(job_id, computation, handle_exception=None):
    """
    Runs the computation associated with a job. If the computation succeeds (runs to completion without
    raising an exception), then the job status is updated with the status code returned by the computation.
    But if the computation fails then handle_exception is invoked and the status code returned by
    handle_exception is used to update the job status. If an excpeption handler is not provided, the job
    status is automatically set to Failed.

    :param job_id: The ID of the job.
    :param computation: The function invoked to run the task: new_status_code = computation(job).
    :param handle_exception: An optional exception handler: new_status = handle_exception(job, ex), where job
        is the current job object and ex is the exception which was caught.
    """
    logger.debug("Entering run_job_task (job_id=%s).", job_id)
    try:
        job = Job.objects.get(pk=job_id)
        logger.debug("run_job_task got the Job object (job_id=%s).", job_id)
        result = computation(job)
        logger.debug("Task execution succeeded (job_id=%s, new_status=%s).",
                     job_id, "unchanged" if result.status is None else result.status)
        result_dict = result.get_dict()
        if result_dict is not None:
            update_job_status_task(job_id, result_dict)
    except Exception as ex:
        logger.exception("An error occurred during task execution (job_id=%s).", job_id)
        result = JobTaskResult(status=Job.FAILED)
        if handle_exception is not None:
            result = handle_exception(job, ex)
            logger.debug("Task exception has been handled (job_id=%s, new_status=%s).",
                         job_id, "unchanged" if result.status is None else result.status)
        result_dict = result.get_dict()

        if result_dict is not None:
            result_dict['info'] = {'error': traceback.format_exc()}
            update_job_status_task(job_id, result_dict)
