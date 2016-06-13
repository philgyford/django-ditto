# coding: utf-8
from unittest.mock import patch

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase
from django.utils.six import StringIO

from ditto.pinboard.fetch import AllBookmarksFetcher, DateBookmarksFetcher,\
        RecentBookmarksFetcher, UrlBookmarksFetcher

class FetchPinboardArgs(TestCase):

    def test_fail_with_no_args(self):
        """Fails when no arguments are provided"""
        with self.assertRaises(CommandError):
            call_command('fetch_pinboard_bookmarks')

    def test_fail_with_account_only(self):
        """Fails when only an account is provided"""
        with self.assertRaises(CommandError):
            call_command('fetch_pinboard_bookmarks', account='philgyford')

    @patch.object(AllBookmarksFetcher, 'fetch')
    def test_with_all(self, fetch_method):
        """Calls the correct method when fetching all bookmarks"""
        call_command('fetch_pinboard_bookmarks', all=True, stdout=StringIO())
        fetch_method.assert_called_once_with(username=None)

    @patch.object(AllBookmarksFetcher, 'fetch')
    def test_with_all_and_account(self, fetch_method):
        """Calls the correct method when fetching one account's bookmarks"""
        call_command('fetch_pinboard_bookmarks', all=True,
                                    account='philgyford', stdout=StringIO())
        fetch_method.assert_called_once_with(username='philgyford')

    @patch.object(DateBookmarksFetcher, 'fetch')
    def test_with_date(self, fetch_method):
        """Calls the correct method when fetching bookmarks for a date"""
        call_command('fetch_pinboard_bookmarks',
                                        date='2015-06-20', stdout=StringIO())
        fetch_method.assert_called_once_with(
                                        post_date='2015-06-20', username=None)

    @patch.object(DateBookmarksFetcher, 'fetch')
    def test_with_date_and_account(self, fetch_method):
        """Calls the correct method when fetching one account's bookmarks for
        a date"""
        call_command('fetch_pinboard_bookmarks', date='2015-06-20',
                                    account='philgyford', stdout=StringIO())
        fetch_method.assert_called_once_with(
                                post_date='2015-06-20', username='philgyford')

    @patch.object(RecentBookmarksFetcher, 'fetch')
    def test_with_recent(self, fetch_method):
        """Calls the correct method when fetching recent bookmarks"""
        call_command('fetch_pinboard_bookmarks', recent=20, stdout=StringIO())
        fetch_method.assert_called_once_with(num=20, username=None)

    @patch.object(RecentBookmarksFetcher, 'fetch')
    def test_with_recent_and_account(self, fetch_method):
        """Calls the correct method when fetching one account's recent
        bookmarks
        """
        call_command('fetch_pinboard_bookmarks', recent=20,
                                    account='philgyford', stdout=StringIO())
        fetch_method.assert_called_once_with(num=20, username='philgyford')

    @patch.object(UrlBookmarksFetcher, 'fetch')
    def test_with_url(self, fetch_method):
        """Calls the correct method when fetching bookmarks by URL"""
        url = 'http://new-aesthetic.tumblr.com/'
        call_command('fetch_pinboard_bookmarks', url=url, stdout=StringIO())
        fetch_method.assert_called_once_with(url=url, username=None)

    @patch.object(UrlBookmarksFetcher, 'fetch')
    def test_with_url_and_account(self, fetch_method):
        """Calls the correct method when fetching a bookmark by URL for one
        account
        """
        url = 'http://new-aesthetic.tumblr.com/'
        call_command('fetch_pinboard_bookmarks', url=url, account='philgyford',
                                                            stdout=StringIO())
        fetch_method.assert_called_once_with(url=url, username='philgyford')


class FetchPinboardOutput(TestCase):

    @patch.object(AllBookmarksFetcher, 'fetch')
    def test_success_output(self, fetch_method):
        """Responds correctly when all bookmarks were successfully fetched"""
        # What the mocked method will return:
        fetch_method.side_effect = [
            [{'account': 'philgyford', 'success': True, 'fetched': 23}]
        ]
        out = StringIO()
        call_command('fetch_pinboard_bookmarks', all=True, stdout=out)
        self.assertIn('philgyford: Fetched 23 Bookmarks', out.getvalue())

    @patch.object(AllBookmarksFetcher, 'fetch')
    def test_error_output(self, fetch_method):
        """Responds correctly when there was an error fetching all bookmarks"""
        # What the mocked method will return:
        fetch_method.side_effect = [
            [{'account': 'philgyford', 'success': False,
                                                    'messages': ['It broke',]}]
        ]
        out = StringIO()
        out_err = StringIO()
        call_command('fetch_pinboard_bookmarks', all=True, stdout=out,
                                                                stderr=out_err)
        self.assertIn('philgyford: Failed to fetch Bookmarks: It broke',
                                                            out_err.getvalue())

    @patch.object(AllBookmarksFetcher, 'fetch')
    def test_multiple_account_output(self, fetch_method):
        """Responds correctly when fetching bookmarks for multiple accounts"""
        # What the mocked method will return:
        fetch_method.side_effect = [
            [
                {'account': 'philgyford', 'success': True, 'fetched': 23},
                {'account': 'wrongaccount', 'success': False,
                                                    'messages': ['It broke',]}
            ]
        ]
        out = StringIO()
        out_err = StringIO()
        call_command('fetch_pinboard_bookmarks', all=True, stdout=out,
                                                                stderr=out_err)
        self.assertIn('philgyford: Fetched 23 Bookmarks', out.getvalue())
        self.assertIn('wrongaccount: Failed to fetch Bookmarks: It broke',
                                                            out_err.getvalue())

    @patch.object(AllBookmarksFetcher, 'fetch')
    def test_success_output_verbosity_0(self, fetch_method):
        """Outputs nothing when all bookmarks were successfully fetched"""
        # What the mocked method will return:
        fetch_method.side_effect = [
            [{'account': 'philgyford', 'success': True, 'fetched': 23}]
        ]
        out = StringIO()
        call_command('fetch_pinboard_bookmarks', all=True, verbosity=0, stdout=out)
        self.assertEqual('', out.getvalue())


