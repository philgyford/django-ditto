#import datetime
#import pytz
from django.test import TestCase

#from freezegun import freeze_time

from ..templatetags.ditto import width_height


class WidthHeightTestCase(TestCase):

    def test_small(self):
        "Uses the same numbers if smaller than maximums"
        self.assertEqual(
            width_height(100, 100, 200, 200),
            'width="100" height="100"'
        )

    def test_large_width(self):
        "Scales to the maximum width"
        self.assertEqual(
            width_height(250, 100, 200, 200),
            'width="200" height="80"'
        )

    def test_large_height(self):
        "Scales to the maximum height"
        self.assertEqual(
            width_height(100, 250, 200, 200),
            'width="80" height="200"'
        )

    def test_both_large_width_largest(self):
        "Scales to the maximum width"
        self.assertEqual(
            width_height(300, 250, 200, 200),
            'width="200" height="167"'
        )

    def test_both_large_height_largest(self):
        "Scales to the maximum height"
        self.assertEqual(
            width_height(250, 300, 200, 200),
            'width="167" height="200"'
        )



