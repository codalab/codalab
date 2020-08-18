# -*- encoding: utf-8 -*-
from django.test import TestCase

from apps.authenz.models import ClUser
from apps.web.utils import clean_html_script


class HTMLCleanTestCase(TestCase):
    def test_script_tags_get_removed_from_html_content(self):
        self.assertEqual(clean_html_script("<script></script>"), "")
        self.assertEqual(clean_html_script("<script src=\"https://www.googleorsomething\"></script>"), "")
        self.assertEqual(clean_html_script(
            "<script src=\"https://www.googleorsomething\">There's some stuff in between here too </script>"), "")
        self.assertEqual(clean_html_script(
            "<script src=\"https://www.googleorsomething\">There's some stuff in between here too </script>There should be some stuff here."),
                          "There should be some stuff here.")
        self.assertEqual(clean_html_script("<b>A strong word</b>"), "<b>A strong word</b>")
        self.assertEqual(clean_html_script('<h1 class="char Zinh U030C" data-text="̌">̌</h1>'),
                          '<h1 class="char Zinh U030C" data-text="̌">̌</h1>')
        self.assertEqual(clean_html_script({
            'my_key': 1,
            'my_value': "twenty_seven",
        }), "{'my_key': 1, 'my_value': 'twenty_seven'}")
        self.assertEqual(clean_html_script(1), "1")
