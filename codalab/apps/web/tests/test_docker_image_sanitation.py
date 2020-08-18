from django.test import TestCase
from apps.web.utils import docker_image_clean


class DockerImageSanitationTests(TestCase):

    def _sanitize(self, str, result):
        self.assertEqual(docker_image_clean(str), result)

    def test_docker_image_sanitation(self):
        # Baseline
        self._sanitize("continuumio/anaconda:4.3.0", "continuumio/anaconda:4.3.0")

        # Strips bad characters
        self._sanitize("      continuumio/anaconda:4.3.0           ", "continuumio/anaconda:4.3.0")
        self._sanitize("###continuumio###/###anaconda:4.3.0###", "continuumio/anaconda:4.3.0")
        self._sanitize("continuumio/anaconda:4.3.0 && sudo rm -rf /", "continuumio/anaconda:4.3.0")
        self._sanitize("continuumio/anaconda:4.3.0 && ls -all || ls.txt", "continuumio/anaconda:4.3.0")
        self._sanitize("continuumio/ anaconda:4.3.0", "continuumio/")
        self._sanitize("continuumio/anaconda:4.3.0", "continuumio/anaconda:4.3.0")
        self._sanitize("continuumio/anaconda-test:4.3.0", "continuumio/anaconda-test:4.3.0")
        self._sanitize("'sudo bash'", "sudo")

        # Handles empties
        self._sanitize(None, "")
        self._sanitize("", "")
        self._sanitize(" ", "")

        # Handles large strings
        self._sanitize(" " * 100, "")
        self._sanitize(" " * 1000, "")

        # Handles underscores
        self._sanitize("lisesun/codalab_automl2016", "lisesun/codalab_automl2016")
