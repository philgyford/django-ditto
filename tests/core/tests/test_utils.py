# coding: utf-8
import datetime
import pytz
from django.test import TestCase

from freezegun import freeze_time

from ditto.core.utils import datetime_now, truncate_string


class DatetimeNowTestCase(TestCase):

    @freeze_time("2015-08-14 12:00:00", tz_offset=-8)
    def test_datetime_now(self):
        self.assertEqual(datetime_now(),
                        datetime.datetime.utcnow().replace(tzinfo=pytz.utc))


class TruncateStringTestCase(TestCase):

    def test_truncate_string_strip_html(self):
        "By default, strips HTML"
        self.assertEqual(
            truncate_string('<p>Some text. <a href="http://www.example.com/"><b>A link</b></a>. And more.'),
            u'Some text. A link. And more.'
        )

    def test_truncate_string_strip_html_false(self):
        "Can be told not to strip HTML"
        self.assertEqual(
            truncate_string('<p>Some text. <a href="http://www.example.com/"><b>A link</b></a>. And more.', strip_html=False),
            u'<p>Some text. <a href="http://www.example.com/"><b>A link</b></a>. And more.'
        )

    def test_truncate_string_default_chars(self):
        "By default, trims to 255 characters"
        self.assertEqual(
            truncate_string('Lorem ipsum dolor sit amet, consectetur adipiscing elit. Donec eget odio eget odio porttitor accumsan in eget elit. Integer gravida egestas nunc. Mauris at tortor ornare, blandit eros quis, auctor lacus. Fusce ullamcorper nunc vitae tincidunt sodales. Vestibulum sit amet lacus at sem porta porta.'),
            u'Lorem ipsum dolor sit amet, consectetur adipiscing elit. Donec eget odio eget odio porttitor accumsan in eget elit. Integer gravida egestas nunc. Mauris at tortor ornare, blandit eros quis, auctor lacus. Fusce ullamcorper nunc vitae tincidunt sodales. Ve…'
        )

    def test_truncate_string_custom_chars(self):
        "Can be told to truncate to other lengths"
        self.assertEqual(
            truncate_string('Lorem ipsum dolor sit amet, consectetur adipiscing elit. Donec eget odio eget odio porttitor accumsan in eget elit. Integer gravida egestas nunc. Mauris at tortor ornare, blandit eros quis, auctor lacus. Fusce ullamcorper nunc vitae tincidunt sodales. Vestibulum sit amet lacus at sem porta porta.', chars=100),
            u'Lorem ipsum dolor sit amet, consectetur adipiscing elit. Donec eget odio eget odio porttitor accums…'
        )

    def test_truncate_string_truncate(self):
        "Can be given a custom 'truncate' string"
        self.assertEqual(
            truncate_string('Lorem ipsum dolor sit amet, consectetur adipiscing elit. Donec eget odio eget odio porttitor accumsan in eget elit. Integer gravida egestas nunc. Mauris at tortor ornare, blandit eros quis, auctor lacus. Fusce ullamcorper nunc vitae tincidunt sodales. Vestibulum sit amet lacus at sem porta porta.', truncate=' (cont.)'),
            u'Lorem ipsum dolor sit amet, consectetur adipiscing elit. Donec eget odio eget odio porttitor accumsan in eget elit. Integer gravida egestas nunc. Mauris at tortor ornare, blandit eros quis, auctor lacus. Fusce ullamcorper nunc vitae tincidunt soda (cont.)'
        )

    def test_at_word_boundary(self):
        "Will break at word boundaries."
        self.assertEqual(
            truncate_string(u'Lorem ipsum dolor sit amet, consectetur adipiscing elit. Donec eget odio eget odio porttitor accumsan in eget elit. Integer gravida egestas nunc. Mauris at tortor ornare, blandit eros quis, auctor lacus. Fusce ullamcorper nunc vitae tincidunt sodales. Vestibulum sit amet lacus at sem porta porta.', at_word_boundary=True),
            u'Lorem ipsum dolor sit amet, consectetur adipiscing elit. Donec eget odio eget odio porttitor accumsan in eget elit. Integer gravida egestas nunc. Mauris at tortor ornare, blandit eros quis, auctor lacus. Fusce ullamcorper nunc vitae tincidunt sodales.…'
        )

    def test_no_truncation(self):
        """Too short to be truncated."""
        self.assertEqual(
            truncate_string(u'This is my string.'),
            u'This is my string.'
        )

    def test_no_truncation_at_word_boundary(self):
        """Too short to be truncated."""
        self.assertEqual(
            truncate_string(u'This is my string.', at_word_boundary=True),
            u'This is my string.'
        )

    def test_truncate_string_all(self):
        """Will strip HTML, truncate to specified length, at a word boundary,
        and add custom string.
        """
        self.assertEqual(
            truncate_string("""<p>Lorem ipsum dolor sit amet, consectetur adipiscing elit. Donec eget odio eget odio porttitor accumsan in eget elit. Integer gravida egestas nunc. Mauris at tortor ornare, blandit eros quis, auctorlacus.</p>

        <p>Fusce ullamcorper nunc vitae tincidunt sodales. Vestibulum sit amet lacus at sem porta porta. Donec fringilla laoreet orci eu porta. Aenean non lacus hendrerit, semper odio a, feugiat orci. Suspendisse potenti.</p>""", strip_html=True, chars=200, truncate='...', at_word_boundary=True),
            u'Lorem ipsum dolor sit amet, consectetur adipiscing elit. Donec eget odio eget odio porttitor accumsan in eget elit. Integer gravida egestas nunc. Mauris at tortor ornare, blandit eros quis,...'
        )

