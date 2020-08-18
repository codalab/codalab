#!/usr/bin/env python

import csv
import json
import http.server
import socketserver
import threading
import time

from textwrap import dedent

from os.path import exists

from .utils import run_shell_script


CSV_HEADERS = [
    'id',
    'Submitter name',
    'Zip name',
    'Size of zip',
    'Compute worker used',
    'Queue used',
    'Score',
    'Total time taken',
    'Status',
]


def server_listener(port=8000):
    Handler = http.server.SimpleHTTPRequestHandler
    httpd = socketserver.TCPServer(("", port), Handler)
    print("Serving at port", port)
    httpd.serve_forever()


def get_submission_report(submission_id):
    separator = '!@#!~~'
    get_submission_report_script = dedent("""
        import json
        from django.conf import settings
        from os.path import basename
        from apps.web.models import CompetitionSubmission, CompetitionSubmissionStatus
        
        submission = CompetitionSubmission.objects.get(pk={submission_id})
        
        # Get file attribute whether we're on S3 or Azure
        if settings.USE_AWS:
            from apps.web.utils import BundleStorage
            size = BundleStorage.bucket.get_key(submission.s3_file).size
        else:
            size = submission.file.size
            
        # Get submission metadata
        metadata = CompetitionSubmissionMetadata.objects.get(submission=submission)
            
        # Make it easier to parse out the json with this separator
        separator = '{separator}'
        
        if submission.status.codename == CompetitionSubmissionStatus.FINISHED:
            total_time_taken = str(submission.completed_at - submission.started_at)
        else:
            total_time_taken = 'N/A'
        
        submission_report = {{
            'id': submission.pk,
            'Submitter name': submission.participant.user.get_full_name(),
            'Zip name': submission.readable_filename,
            'Size of zip': size,
            'Compute worker used': metadata.hostname,
            'Queue used': submission.queue_name,
            'Score': str(submission.get_default_score()),
            'Total time taken': total_time_taken,
            'Status': submission.status.codename,
        }}
        
        print '{{}}{{}}{{}}'.format(separator, json.dumps(submission_report), separator)
    """).format(
        submission_id=submission_id,
        separator=separator
    )

    submission_report_results = run_shell_script(get_submission_report_script)
    submission_report_json = submission_report_results.split(separator)[1]
    return json.loads(submission_report_json)


def add_report(report_dict):
    with open('report.csv', 'a+') as report_file:
        writer = csv.DictWriter(report_file, fieldnames=CSV_HEADERS)
        writer.writerow(report_dict)
    print("Added report for submission={}".format(report_dict['id']))


if __name__ == "__main__":
    processed_submission_ids = []

    # Start server listening thread
    print("Starting server")
    thread = threading.Thread(target=server_listener, kwargs={'port': 8000})
    thread.daemon = True
    thread.start()

    # Load CSV to see what IDs we've already processed
    if exists('report.csv'):
        with open('report.csv', 'rb') as report_file:
            reader = csv.DictReader(report_file)
            for row in reader:
                processed_submission_ids.append(row['id'])
    else:
        # report csv doesn't exist yet, write in headers
        with open('report.csv', 'w') as report_file:
            report_file.write(",".join(CSV_HEADERS))
            report_file.write("\n")

    print("{} submissions already processed, ready for more".format(
        len(processed_submission_ids),
    ))

    # Start loop waiting for more submissions to process
    while True:
        with open('submission_ids.txt', 'r') as submission_ids:
            for submission_id in submission_ids:
                # Sometimes whitespace messes up id
                submission_id = submission_id.strip()

                if submission_id not in processed_submission_ids:
                    add_report(get_submission_report(submission_id))
                    processed_submission_ids.append(submission_id)
        time.sleep(1)
