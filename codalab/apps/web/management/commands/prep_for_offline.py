import requests
import shutil
import sys
import zipfile
import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

User = get_user_model()

class Command(BaseCommand):
    help = """Sets up Codalab for offline usage."""

    def add_arguments(self, parser):
        parser.add_argument('--delete', '-d',
                    dest='delete',
                    action="store_true",
                    default=False,
                    help="remove prep for offline"
                    ),

    def handle(self, *args, **options):
        # list containing |(package_name, destination, download_url, file_name, dir_name, success_message )| tuples for packages
        packages = [
            ('MathJax', 'apps/web/static/js/vendor/mathjax', 'https://github.com/mathjax/MathJax/archive/master.zip', 'mathjax.zip', 'MathJax-master', 'LOCAL_MATHJAX = True'),
            ('Ace-editor', 'apps/web/static/js/vendor/ace-editor', 'https://github.com/ajaxorg/ace-builds/archive/master.zip', 'ace-builds-master.zip', 'ace-builds-master', 'LOCAL_ACE_EDITOR = True'),
        ]
        print(" ----- ")
        if options['delete']:
            for package_name, destination, _, _, _, _ in packages:
                print("cleaning up %s" % package_name)
                shutil.rmtree(destination)
            return

        # all packages that are successfully installed will be appended to this list
        success_message_list = []

        for package_name, destination, download_url, file_name, dir_name, success_message in packages:
            if not os.path.exists(file_name):
                with open(file_name, "wb") as f:
                        print("Downloading %s to %s..." % (download_url, file_name))
                        response = requests.get(download_url, stream=True)
                        total_length = response.headers.get('content-length')
                        if total_length is None: # no content length header
                            f.write(response.content)
                        else:
                            dl = 0
                            total_length = int(total_length)
                            for data in response.iter_content(1024*1024):
                                dl += len(data)
                                f.write(data)
                                done = int(50 * dl / total_length)
                                sys.stdout.write("\r[%s%s]" % ('=' * done, ' ' * (50-done)) )
                                sys.stdout.flush()

            if not os.path.exists(dir_name):
                print('Unzipping %s to %s...' % (file_name, dir_name))
                zip_file = zipfile.ZipFile(file_name)
                zip_file.extractall()

            print("Moving over files to correct directories...")
            try:
                shutil.move(dir_name, destination)
            except Exception as e:
                print("************")
                print("ERROR: %s files not found. Please rerun to download and unpack the files again" % (package_name))
                print(e)
                print("************")
                continue

            success_message_list.append(success_message)

        print('\n')
        print('Please put the following in your `codalab/settings/local.py` file to enable offline usage:')
        for success_message in success_message_list:
            print(success_message)
