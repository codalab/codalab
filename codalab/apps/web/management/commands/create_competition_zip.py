import datetime
import os
import random
import requests
import shutil
import string
import tempfile
import yaml

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

User = get_user_model()

class Command(BaseCommand):
    help = """Creates a fake competition zip file for easy uploading and testing. \n Please see create_competition_zip.py for more options"""

    def add_arguments(self, parser):
        parser.add_argument('--numphases', '-p',
                    dest='numphases',
                    default=5,
                    type=int,
                    help="Number of phases to create"
                    ),
        parser.add_argument('--phaselength', '-l',
                    dest='phaselength',
                    type=int,
                    default=10,
                    help="How many minutes would you like phase to last"
                    ),
        parser.add_argument('--delete', '-d',
                    dest='delete',
                    action="store_false",
                    default=True,
                    help="Don't delete the temp files"
                    ),
        parser.add_argument('--automigrate', '-a',
                    dest='auto_migrate',
                    action="store_true",
                    default=False,
                    help="Enable auto migration between phases"
                    )

    def handle(self, *args, **options):
        print(" ----- ")
        print("Creating a competition zip in project root. The competition is based on the hello world example")
        print("https://github.com/Tivix/competition-examples/tree/master/hello_world/competition")
        print("this command is mainly used quick dev test of full upload competition flow and phases")
        print(" ----- ")

        #please set these to whatever defaults you would like to load
        yaml_file_url = "https://raw.githubusercontent.com/Tivix/competition-examples/master/hello_world/competition/competition.yaml"
        logo_url = "https://raw.githubusercontent.com/Tivix/competition-examples/master/hello_world/competition/logo.jpg"

        scoring_program_eval_url = "https://raw.githubusercontent.com/Tivix/competition-examples/master/hello_world/competition/scoring_program/evaluate.py"
        scoring_program_metdata_url = "https://raw.githubusercontent.com/Tivix/competition-examples/master/hello_world/competition/scoring_program/metadata"

        reference_data_truth_url = "https://raw.githubusercontent.com/Tivix/competition-examples/master/hello_world/competition/reference_data/truth.txt"

        #dummy flat data
        data_html = "<p> This is the data for the competition. It is to be used responsibly.</p>"
        evaluation_html = "<H3>Evaluation Criteria</H3><p>This is the page that tells you how competition submissions will be evaluated and scored.</p>"
        overview_html = "<H3>Welcome!</H3> <p> This is an example competition. </p>"
        terms_and_conditions_html = "<H3>Terms and Conditions</H3> <p> This page enumerated the terms and conditions of the competition. </p>"

        numphases = options['numphases']
        phaselength = options['phaselength']
        delete = options['delete']
        auto_migrate = options['auto_migrate']

        if numphases < 1:
            print("you must have at least one phase ")
            return

        phasedates = []
        now = datetime.datetime.utcnow()
        delta = datetime.timedelta(minutes=phaselength)
        next = now
        for i in range(0, numphases):
            phasedates.append(next)
            next = next + delta

        #get files and make edits
        yaml_file = requests.get(yaml_file_url)
        comp_yaml_obj = yaml.full_load(yaml_file.content)

        #put our date changed phases and with random name
        tz_now = datetime.datetime.now()
        comp_yaml_obj['title'] = "%s %s" %(comp_yaml_obj['title'], tz_now.strftime("%m-%d %d:%M"))
        comp_yaml_obj['force_submission_to_leaderboard'] = True

        comp_yaml_obj['phases'] = {}
        for i in range(0, numphases):
            random_name = ''.join(random.choice(string.ascii_uppercase + string.ascii_lowercase) for _ in range(6))
            phase_name = "Phase %s %s" % (i, random_name)
            phase = {
                   i: {
                      'scoring_program': 'scoring_program.zip',
                      'phasenumber': i,
                      'max_submissions': 100,
                      'reference_data': 'reference_data.zip',
                      'start_date': phasedates[i],
                      'label': phase_name,
                      'auto_migration': auto_migrate
                   }
                }
            comp_yaml_obj['phases'].update(phase)


        PROJECT_ROOT = os.path.abspath(os.path.split(os.path.split(__file__)[1])[0])

        # let's further isolate this by creating a temp dir with a name we control
        temp_dir = os.path.join(PROJECT_ROOT, 'tmp_comp')
        if os.path.exists(temp_dir) == False:
            os.mkdir(temp_dir)
        #now lets create a real temp dir.
        root_dir = tempfile.mkdtemp(dir=temp_dir)

        #setup up some sub folders
        scoring_program_dir = os.path.join(root_dir, 'scoring_program')
        if os.path.exists(scoring_program_dir) == False:
            os.mkdir(scoring_program_dir)

        reference_data_dir = os.path.join(root_dir, 'reference_data')
        if os.path.exists(reference_data_dir) == False:
            os.mkdir(reference_data_dir)

        #write the files we need
        # yaml for the competition
        with open(os.path.join(root_dir, 'competition.yaml'), 'w') as f:
            f.write(yaml.dump(comp_yaml_obj, default_flow_style=False))

        #misc files
        with open(os.path.join(root_dir, 'data.html'), 'w') as f:
            f.write(data_html)
        with open(os.path.join(root_dir, 'evaluation.html'), 'w') as f:
            f.write(evaluation_html)
        with open(os.path.join(root_dir, 'overview.html'), 'w') as f:
            f.write(overview_html)
        with open(os.path.join(root_dir, 'terms_and_conditions.html'), 'w') as f:
            f.write(terms_and_conditions_html)
        # logo
        r = requests.get(logo_url, stream=True)
        if r.status_code == 200:
            with open(os.path.join(root_dir, 'logo.jpg'), 'wb') as f:
                for chunk in r.iter_content():
                    f.write(chunk)


        #scoring program files
        evaluate_py = requests.get(scoring_program_eval_url)
        evaluate_py = evaluate_py.content

        scoring_program_metdata = requests.get(scoring_program_metdata_url)
        scoring_program_metdata = scoring_program_metdata.content

        with open(os.path.join(scoring_program_dir, 'evaluate.py'), 'w') as f:
            f.write(evaluate_py)
        with open(os.path.join(scoring_program_dir, 'metadata'), 'w') as f:
            f.write(scoring_program_metdata)


        #reference data files
        truth_txt = requests.get(reference_data_truth_url)
        truth_txt = truth_txt.content

        with open(os.path.join(reference_data_dir, 'truth.txt'), 'w') as f:
            f.write(truth_txt)


        #zip everything up
        shutil.make_archive(
            base_name=scoring_program_dir,  #folder and file name are the same
            format='zip',
            root_dir=scoring_program_dir,
        )
        shutil.make_archive(
            base_name=reference_data_dir,  #folder and file name are the same
            format='zip',
            root_dir=reference_data_dir,
        )

        output_file = os.path.join(PROJECT_ROOT, 'sample_competition.zip')
        shutil.make_archive(
            base_name=os.path.splitext(output_file)[0],
            format='zip',
            root_dir=root_dir,
        )

        print("sample competition complete")
        print(output_file)

        if temp_dir is not None and delete:
            # Try cleaning-up temporary directory
            try:
                os.chdir(PROJECT_ROOT)
                shutil.rmtree(temp_dir)
            except:
                print("there was a problem cleaning up the temp folder.")
                print(temp_dir)
