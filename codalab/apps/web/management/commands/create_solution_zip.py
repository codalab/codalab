import datetime
import os
import requests
import shutil
import tempfile

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

User = get_user_model()

class Command(BaseCommand):
    help = """Creates a fake solution zip file for easy uploading and testing. \n This is made to work in tandem with create_competition_zip"""

    def add_arguments(self, parser):
        parser.add_argument('--delete', '-d',
                    dest='delete',
                    action="store_true",
                    default=True,
                    help="Don't delete the temp files"
                    ),
        parser.add_argument('--wrong', '-w',
                    dest='wrong',
                    action="store_true",
                    default=False,
                    help="Create wrong submission"
                    )

    def handle(self, *args, **options):
        print(" ----- ")
        print("Creating a solution zip in project root. The solution is based on the hello world example")
        print("https://github.com/Tivix/competition-examples/tree/master/hello_world/submission")
        print("this command is mainly used quick dev test")
        print(" ----- ")

        #please set these to whatever defaults you would like to load
        answer_txt_url = "https://raw.githubusercontent.com/Tivix/competition-examples/master/hello_world/submission/answer.txt"
        delete = options['delete']
        wrong = options['wrong']

        PROJECT_ROOT = os.path.abspath(os.path.split(os.path.split(__file__)[1])[0])

        # let's further isolate this by creating a temp dir with a name we control
        temp_dir = os.path.join(PROJECT_ROOT, 'tmp_comp')
        if os.path.exists(temp_dir) == False:
            os.mkdir(temp_dir)
        #now lets create a real temp dir.
        root_dir = tempfile.mkdtemp(dir=temp_dir)


        #reference data files
        answer_txt = requests.get(answer_txt_url)
        answer_txt = answer_txt.content

        with open(os.path.join(root_dir, 'answer.txt'), 'w') as f:
            if wrong:
                f.write("This is wrong. Sorry :(")
            else:
                f.write(answer_txt)

        file_name = 'sample_solution'
        if wrong:
            file_name = 'sample_solution_wrong'

        tz_now = datetime.datetime.now()
        file_name = "%s-%s.zip" % (file_name, tz_now.strftime("%m-%d-%d-%M"))

        output_file = os.path.join(PROJECT_ROOT, file_name)
        shutil.make_archive(
            base_name=os.path.splitext(output_file)[0],
            format='zip',
            root_dir=root_dir,
        )

        print("sample solution complete")

        if temp_dir is not None and delete:
            # Try cleaning-up temporary directory
            try:
                os.chdir(PROJECT_ROOT)
                shutil.rmtree(temp_dir)
            except:
                print("there was a problem cleaning up the temp folder.")
                print(temp_dir)
