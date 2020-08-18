"""
Package containing the CodaLab client tools.
"""

import json
import multiprocessing
import os
import yaml
import time

from queue import Empty

class BaseConfig(object):
    """
    Defines a base class for loading configuration values from a YAML-formatted file.
    """
    def __init__(self, filename='.codalabconfig'):
        self._filename = filename
        paths_searched = [self._filename]
        if not os.path.exists(self._filename):
            self._filename = os.path.join(os.getcwd(), filename)
            paths_searched.append(self._filename)
            if not os.path.exists(self._filename):
                self._filename = os.path.join(os.path.expanduser("~"), filename)
                paths_searched.append(self._filename)
            env_config_path = os.environ.get('CONFIG_PATH', '/home/azureuser')
            if env_config_path and not os.path.exists(self._filename):
                self._filename = os.path.join(env_config_path, filename)
                paths_searched.append(self._filename)
            if not os.path.exists(self._filename):
                msg = "Config file not found. Searched for:\n" + "\n".join(paths_searched)
                raise EnvironmentError(msg)

        with open(self._filename, "r") as f:
            self.info = yaml.load(f)

    def getFilename(self):
        """Returns the full name of the configuration file."""
        return self._filename

    def getLoggerDictConfig(self):
        """Gets Dict config for logging configuration."""
        return self.info['logging'] if 'logging' in self.info else None


class Queue(object):
    """
    Provides an abstract definition for a queue providing one-way asynchronous messaging
    between a publisher and a remote subscriber.
    """
    def receive_message(self):
        """
        Gets the next message from the queue.

        Returns a valid QueueMessage instance or None if no message was received.
        """
        raise NotImplementedError()

    def send_message(self, body):
        """
        Sends a message to the queue.

        body: A string representing the body of the message.
        """
        raise NotImplementedError()

class QueueMessage(object):
    """
    Provides an abstract definition for a message exchanged through a queue.
    """
    def get_body(self):
        """Gets a string representing the body of the message."""
        raise NotImplementedError()
    def get_queue(self):
        """Gets the Queue instance from which the message was retrieved."""
        raise NotImplementedError()

class QueueMessageError(Exception):
    """Indicates that the body of a queue message cannot be decoded or is invalid."""
    def __init__(self, message):
        Exception.__init__(self, message)

def decode_message_body(message):
    """
    Returns a dictionary instance contructed by decoding the JSON-encoded body
    of the given message. The message is expected to decode to a dict containing
    the following required key-value pairs:
        key='id' -> tracking identifier
        key='task_type' -> string defining the type of task expected from the consumer
    Input arguments are usually passed with a third optional key-value pair:
        key='task_args' -> object defining input arguments for the task

    message: A QueueMessage instance.
    """
    try:
        body = message.get_body()
        data = json.loads(body)
    except:
        raise QueueMessageError("JSON object could not be decoded.")
    if not 'id' in data:
        raise QueueMessageError("Missing key: id.")
    if not 'task_type' in data:
        raise QueueMessageError("Missing key: task_type.")
    return data

class BaseWorker(object):
    """
    Defines the base implementation for a worker process which listens to a queue for
    messages. Each message defines a task. When the worker receives a message, it performs
    the task then goes back to listening mode.
    """

    def __init__(self, queue, vtable, logger):
        """
        queue: The Queue object to listen to.
        vtable: A map from a task type to a function which contructs a runnable task. Given a
            message with an identifier I, a task type T and task arguments A, the function
            constructed to run the task is: F = vtable[T](I, A). And F() runs the task.
        logger: The logging.Logger object to use.
        """
        self.queue = queue
        self.logger = logger
        self.vtable = vtable

    def _message_receive_listen(self, queue):
        while True:
            try:
                self.logger.debug("Waiting for message.")
                queue.put('waiting for message')
                msg = self.queue.receive_message()
                if msg is not None:
                    queue.put('received message')
                    self.logger.debug("Received message: %s", msg.get_body())
                    data = decode_message_body(msg)
                    task_id = data['id']
                    task_type = data['task_type']
                    task_args = data['task_args'] if 'task_args' in data else None
                    if task_type in self.vtable:
                        self.logger.info("Running task: id=%s task_type=%s", task_id, task_type)
                        self.vtable[task_type](task_id, task_args)
                        self.logger.info("Task complete: id=%s task_type=%s", task_id, task_type)
                    else:
                        self.logger.warning("Unknown task_type=%s for task with id=%s", task_type, task_id)
            # catch all non-"system exiting" exceptions
            except Exception:
                self.logger.exception("An error has occurred.")
                time.sleep(3)

    def start(self):
        """
        Starts the worker loop on the current thread.
        """
        self.logger.debug("BaseWorker entering worker loop.")

        last_message = None
        queue = multiprocessing.Queue(8)
        worker = multiprocessing.Process(target=self._message_receive_listen, args=(queue,))
        worker.start()

        while True:
            try:
                result = queue.get(True, 120)
            except Empty:
                result = None

            self.logger.debug("Process thread status result: %s" % result)

            # We don't want to shut off submissions in process, so only terminate if we're waiting for a message
            if last_message == 'waiting for message' and result is None:
                self.logger.debug("Restarting worker thread")
                worker.terminate()
                worker = multiprocessing.Process(target=self._message_receive_listen, args=(queue,))
                worker.start()

            last_message = result
