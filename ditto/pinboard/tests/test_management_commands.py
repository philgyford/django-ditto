# coding: utf-8
from mock import patch

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase
from django.utils.six import StringIO


class FetchPinboardTestCase(TestCase):

    def test_fail_with_no_args(self):
        with self.assertRaises(CommandError):
            call_command('fetch_pinboard_bookmarks')

    def test_fail_with_account_only(self):
        with self.assertRaises(CommandError):
            call_command('fetch_pinboard_bookmarks', account='philgyford')

    @patch('ditto.pinboard.fetch.FetchBookmarks.fetch_all')
    def test_with_all(self, fetch_method):
        call_command('fetch_pinboard_bookmarks', all=True, stdout=StringIO())
        fetch_method.assert_called_once_with(username=None)

    @patch('ditto.pinboard.fetch.FetchBookmarks.fetch_all')
    def test_with_all_and_account(self, fetch_method):
        call_command('fetch_pinboard_bookmarks', all=True,
                                    account='philgyford', stdout=StringIO())
        fetch_method.assert_called_once_with(username='philgyford')

    @patch('ditto.pinboard.fetch.FetchBookmarks.fetch_date')
    def test_with_date(self, fetch_method):
        call_command('fetch_pinboard_bookmarks',
                                        date='2015-06-20', stdout=StringIO())
        fetch_method.assert_called_once_with(
                                        post_date='2015-06-20', username=None)

    @patch('ditto.pinboard.fetch.FetchBookmarks.fetch_date')
    def test_with_date_and_account(self, fetch_method):
        call_command('fetch_pinboard_bookmarks', date='2015-06-20',
                                    account='philgyford', stdout=StringIO())
        fetch_method.assert_called_once_with(
                                post_date='2015-06-20', username='philgyford')

    @patch('ditto.pinboard.fetch.FetchBookmarks.fetch_recent')
    def test_with_recent(self, fetch_method):
        call_command('fetch_pinboard_bookmarks', recent=20, stdout=StringIO())
        fetch_method.assert_called_once_with(num=20, username=None)

    @patch('ditto.pinboard.fetch.FetchBookmarks.fetch_recent')
    def test_with_recent_and_account(self, fetch_method):
        call_command('fetch_pinboard_bookmarks', recent=20,
                                    account='philgyford', stdout=StringIO())
        fetch_method.assert_called_once_with(num=20, username='philgyford')

    @patch('ditto.pinboard.fetch.FetchBookmarks.fetch_url')
    def test_with_url(self, fetch_method):
        url = 'http://new-aesthetic.tumblr.com/'
        call_command('fetch_pinboard_bookmarks', url=url, stdout=StringIO())
        fetch_method.assert_called_once_with(url=url, username=None)

    @patch('ditto.pinboard.fetch.FetchBookmarks.fetch_url')
    def test_with_url_and_account(self, fetch_method):
        url = 'http://new-aesthetic.tumblr.com/'
        call_command('fetch_pinboard_bookmarks', url=url, account='philgyford',
                                                            stdout=StringIO())
        fetch_method.assert_called_once_with(url=url, username='philgyford')


    @patch('ditto.pinboard.fetch.FetchBookmarks.fetch_all')
    def test_success_output(self, fetch_method):
        # What the mocked method will return:
        fetch_method.side_effect = [
            [{'account': 'philgyford', 'success': True, 'fetched': 23}]
        ]
        out = StringIO()
        call_command('fetch_pinboard_bookmarks', all=True, stdout=out)
        self.assertIn('philgyford: Fetched 23 bookmarks', out.getvalue())

    @patch('ditto.pinboard.fetch.FetchBookmarks.fetch_all')
    def test_error_output(self, fetch_method):
        # What the mocked method will return:
        fetch_method.side_effect = [
            [{'success': False, 'message': 'It broke'}]
        ]
        out = StringIO()
        out_err = StringIO()
        call_command('fetch_pinboard_bookmarks', all=True, stdout=out,
                                                                stderr=out_err)
        self.assertIn('all: Failed to fetch bookmarks: It broke',
                                                            out_err.getvalue())

    @patch('ditto.pinboard.fetch.FetchBookmarks.fetch_all')
    def test_multiple_account_output(self, fetch_method):
        # What the mocked method will return:
        fetch_method.side_effect = [
            [
                {'account': 'philgyford', 'success': True, 'fetched': 23},
                {'account': 'wrongaccount', 'success': False, 'message': 'It broke'}
            ]
        ]
        out = StringIO()
        out_err = StringIO()
        call_command('fetch_pinboard_bookmarks', all=True, stdout=out,
                                                                stderr=out_err)
        self.assertIn('philgyford: Fetched 23 bookmarks', out.getvalue())
        self.assertIn('wrongaccount: Failed to fetch bookmarks: It broke',
                                                            out_err.getvalue())

