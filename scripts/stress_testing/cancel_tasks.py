#!/usr/bin/env python

import re
from textwrap import dedent

from .utils import run_shell_script


if __name__ == "__main__":
    cancel_tasks_script = dedent("""
        from celery.task.control import inspect, revoke
        
        
        def get_task_ids(task_query):
            for worker, tasks in task_query.items():
                for task in tasks:
                    print '***Found task: {}***'.format(task['name'])
                    yield task['id']
        
        
        def cancel_tasks(task_ids):
            for task_id in task_ids:
                revoke(task_id, terminate=True)
        
        
        i = inspect()
        
        task_ids = []
        task_ids += list(get_task_ids(i.scheduled()))
        task_ids += list(get_task_ids(i.active()))
        task_ids += list(get_task_ids(i.reserved()))
        
        cancel_tasks(task_ids)
    """)

    cancel_tasks_result = run_shell_script(cancel_tasks_script)

    # Get all messages between '***'
    tasks = re.findall("\*\*\*.*?\*\*\*", cancel_tasks_result)

    for task in tasks:
        print(task.replace('***', ''))

    if not tasks:
        print("No tasks to cancel!")
