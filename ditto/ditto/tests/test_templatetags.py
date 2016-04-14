import datetime
import pytz
from unittest.mock import patch

from django.test import TestCase

from freezegun import freeze_time

from ..templatetags.ditto import width_height, split_by, display_time 


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


class DisplayTimeTestCase(TestCase):

    @freeze_time("2015-08-14 13:34:56")
    def test_returns_time_with_no_link(self):
        dt = datetime.datetime.now().replace(tzinfo=pytz.utc)

        self.assertEqual(
            display_time(dt),
            '<time datetime="2015-08-14 13:34:56">13:34 on 14&nbsp;Aug&nbsp;2015</time>'
        )

    @freeze_time("2015-08-14 13:34:56")
    @patch('ditto.ditto.templatetags.ditto.reverse')
    def test_returns_time_with_link(self, reverse):
        reverse.return_value = '/2015/08/14/'
        dt = datetime.datetime.now().replace(tzinfo=pytz.utc)

        self.assertEqual(
            display_time(dt, True),
            '<time datetime="2015-08-14 13:34:56">13:34 on <a href="/2015/08/14/" title="All items from this day">14&nbsp;Aug&nbsp;2015</a></time>'
        )


class SplitByTestCase(TestCase):

    def test_returns_fewer_lists(self):
        "If there are fewer items than the split number"
        self.assertEqual(
            split_by([1,2,3,4], 6),
            [[1,2,3,4,],]
        )

    def test_returns_correct_number_of_lists(self):
        self.assertEqual(
            split_by(list(range(1,11)), 3),
            [
                [1, 2, 3,],
                [4, 5, 6,],
                [7, 8, 9,],
                [10,]
            ]
        )

