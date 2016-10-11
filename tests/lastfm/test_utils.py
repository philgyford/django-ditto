from django.test import TestCase

from ditto.lastfm.utils import slugify_name


class UtilsTestCase(TestCase):
    """
    These conversions have been tested by playing a track with the characters
    in the title, having Last.fm scrobble it, then clicking through to
    the track's page to get the encoded URL.
    """

    def test_unchanged_characters(self):
        "Some characters should remain unchanged."
        self.assertEqual(
            slugify_name(', . & ! ( ) ; :'),
                         ',+.+&+!+(+)+;+:'

        )

    def test_changed_characters_1(self):
        self.assertEqual(
            slugify_name("/ # ? [ ] ' + %"),
                        '%2F+%23+%3F+%5B+%5D+%27+%252B+%25'
        )

    def test_changed_characters_2(self):
        self.assertEqual(
            slugify_name('" < > \ ^ ` { | }'),
                        '%22+%3C+%3E+%5C%5C+%5E+%60+%7B+%7C+%7D'
        )

