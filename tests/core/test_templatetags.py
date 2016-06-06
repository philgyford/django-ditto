import datetime
import pytz
from unittest.mock import patch, Mock, MagicMock

from django.http import QueryDict
from django.test import TestCase

from freezegun import freeze_time

from ditto.core.templatetags.ditto_core import display_time, split_by,\
        query_string, width_height
from ditto.core.utils import datetime_now


class QueryStringTestCase(TestCase):

    def test_adds_arg(self):
        "It adds your key/value to the existing GET string."
        context = {'request': Mock( GET=QueryDict('a=1') ) }
        self.assertIn(
            query_string(context, 'foo', 'bar'),
            ['foo=bar&a=1', 'a=1&foo=bar']
        )

    def test_replaces_arg(self):
        "It replaces an existing GET arg with what you supply."
        context = {'request': Mock( GET=QueryDict('a=1') ) }
        self.assertEqual(
            query_string(context, 'a', 'bar'),
            'a=bar'
        )

    def test_handles_missing_request(self):
        "If there's no request object, it doesn't complain."
        context = {}
        self.assertEqual(
            query_string(context, 'foo', 'bar'),
            'foo=bar'
        )

    def test_urlencodes(self):
        "It URL-encodes the returned string."
        context = {'request': Mock( GET=QueryDict('a=1') ) }
        self.assertIn(
            query_string(context, 'foo', 'bar&bar'),
            ['foo=bar%26bar&a=1', 'a=1&foo=bar%26bar']
        )


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
        self.assertEqual(
            display_time(datetime_now()),
            '<time datetime="2015-08-14 13:34:56">13:34 on 14&nbsp;Aug&nbsp;2015</time>'
        )

    @freeze_time("2015-08-14 13:34:56")
    @patch('ditto.core.templatetags.ditto_core.reverse')
    def test_returns_time_with_link(self, reverse):
        reverse.return_value = '/2015/08/14/'
        self.assertEqual(
            display_time(datetime_now(), True),
            '<time datetime="2015-08-14 13:34:56">13:34 on <a href="/2015/08/14/" title="All items from this day">14&nbsp;Aug&nbsp;2015</a></time>'
        )

    @freeze_time("2015-08-14 13:34:56")
    def test_granularity_4_no_link(self):
        self.assertEqual(
            display_time(datetime_now(), granularity=4),
            '<time datetime="2015-08">sometime in Aug&nbsp;2015</time>'
        )

    @freeze_time("2015-08-14 13:34:56")
    def test_granularity_6_no_link(self):
        self.assertEqual(
            display_time(datetime_now(), granularity=6),
            '<time datetime="2015">sometime in 2015</time>'
        )

    @freeze_time("2015-08-14 13:34:56")
    def test_granularity_8_no_link(self):
        self.assertEqual(
            display_time(datetime_now(), granularity=8),
            '<time datetime="2015">circa 2015</time>'
        )

    @freeze_time("2015-08-14 13:34:56")
    def test_granularity_4_with_link(self):
        "Doesn't actually have a link as there's no exact day."
        self.assertEqual(
            display_time(datetime_now(), link_to_day=True, granularity=4),
            '<time datetime="2015-08">sometime in Aug&nbsp;2015</time>'
        )

    @freeze_time("2015-08-14 13:34:56")
    def test_granularity_6_with_link(self):
        "Doesn't actually have a link as there's no exact day."
        self.assertEqual(
            display_time(datetime_now(), link_to_day=True, granularity=6),
            '<time datetime="2015">sometime in 2015</time>'
        )

    @freeze_time("2015-08-14 13:34:56")
    def test_granularity_8_with_link(self):
        "Doesn't actually have a link as there's no exact day."
        self.assertEqual(
            display_time(datetime_now(), link_to_day=True, granularity=8),
            '<time datetime="2015">circa 2015</time>'
        )

    @freeze_time("2015-08-14 13:34:56")
    def test_case_lower(self):
        self.assertEqual(
            display_time(datetime_now(), granularity=4, case='lower'),
            '<time datetime="2015-08">sometime in aug&nbsp;2015</time>'
        )

    @freeze_time("2015-08-14 13:34:56")
    def test_case_capfirst(self):
        self.assertEqual(
            display_time(datetime_now(), granularity=4, case='capfirst'),
            '<time datetime="2015-08">Sometime in Aug&nbsp;2015</time>'
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

