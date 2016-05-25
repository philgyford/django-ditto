# coding: utf-8
import datetime
import os
import pytz
from unittest.mock import patch

from django.test import TestCase

from freezegun import freeze_time
import responses
from requests.exceptions import HTTPError

from ditto.core.utils import datetime_now, truncate_string
from ditto.core.utils.downloader import DownloadException, filedownloader


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


class FileDownloaderTestCase(TestCase):

    def setUp(self):
        self.url = \
            'https://c2.staticflickr.com/8/7019/27006033235_caa438b3b8_o.jpg'

    def do_download(self, status=200, content_type='image/jpg'):
        "Mocks requests and calls filedownloader.download()"
        # Open the image we're going to pretend we're fetching from the URL:
        with open('tests/core/fixtures/images/marmite.jpg', 'rb') as img1:

            responses.add(responses.GET, self.url,
                            body=img1.read(),
                            status=status,
                            content_type=content_type,
                            adding_headers={'Transfer-Encoding': 'chunked'})

            return filedownloader.download(self.url, ['image/jpg'])

    @responses.activate
    @patch.object(filedownloader, 'make_filename')
    def test_downloads_file(self, make_filename):
        "Streams a jpg, saves it to /tmp/, returns the path, calls _make_filename_for_download()."
        make_filename.return_value = 'marmite.jpg'

        filepath = self.do_download()

        self.assertTrue(os.path.isfile(filepath))
        self.assertEqual(len(responses.calls), 1)
        self.assertEqual(filepath, '/tmp/marmite.jpg')
        make_filename.assert_called_once_with(self.url,
                {'Content-Type': 'image/jpg', 'Transfer-Encoding': 'chunked'})

    @responses.activate
    def test_raises_error_on_get_failure(self):
        "If the requests.get() call raises an error."
        responses.add(responses.GET, self.url,
                        body=HTTPError('Something went wrong'))
        with self.assertRaises(DownloadException):
            filepath = filedownloader.download(self.url, ['image/jpg'])

    @responses.activate
    def test_raises_error_on_bad_status_code(self):
        with self.assertRaises(DownloadException):
            filepath = self.do_download(status=500)

    @responses.activate
    def test_raises_error_with_invalid_content_type(self):
        "If downloaded file has content type different to what we ask for."
        with self.assertRaises(DownloadException):
            filepath = self.do_download(content_type='text/html')

    def test_make_filename_from_url(self):
        "Should use the URL's filename."
        filename = filedownloader.make_filename(
            'https://c2.staticflickr.com/8/7019/27006033235_caa438b3b8_o.jpg',
            {}
        )
        self.assertEqual(filename, '27006033235_caa438b3b8_o.jpg')

    def test_make_filename_from_content_disposition(self):
        "If URL has no filename, should use the Content-Disposition filename."
        filename = filedownloader.make_filename(
            'https://www.flickr.com/photos/philgyford/26348530105/play/orig/2b5f3e0919/',
            {'Content-Disposition': 'attachment; filename=26348530105.mov'}
        )
        self.assertEqual(filename, '26348530105.mov')

