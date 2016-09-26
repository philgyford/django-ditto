from unittest.mock import patch, Mock

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase
from django.utils.six import StringIO

from ditto.lastfm.fetch import ScrobblesMultiAccountFetcher
from ditto.lastfm.factories import AccountFactory


class FetchLastfmScrobblesTestCase(TestCase):

    def setUp(self):
        self.out = StringIO()
        self.out_err = StringIO()
        self.account = AccountFactory(username='terry', api_key='1234')

    def test_fail_with_invalid_days(self):
        with self.assertRaises(CommandError):
            call_command('fetch_lastfm_scrobbles', days='foo')

    @patch.object(ScrobblesMultiAccountFetcher, 'fetch')
    def test_sends_recent_fetch_type(self, fetch):
        "Should call Fetcher with correct fetch_type"
        call_command('fetch_lastfm_scrobbles')
        fetch.assert_called_with(fetch_type='recent')

    @patch.object(ScrobblesMultiAccountFetcher, 'fetch')
    def test_sends_all_fetch_type(self, fetch):
        "Should call Fetcher with correct fetch_type"
        call_command('fetch_lastfm_scrobbles', days='all')
        fetch.assert_called_with(fetch_type='all')

    @patch.object(ScrobblesMultiAccountFetcher, 'fetch')
    def test_sends_days_fetch_type(self, fetch):
        "Should call Fetcher with correct fetch_type"
        call_command('fetch_lastfm_scrobbles', days='3')
        fetch.assert_called_with(fetch_type='days', days=3)

    @patch.object(ScrobblesMultiAccountFetcher, 'fetch')
    @patch.object(ScrobblesMultiAccountFetcher, '__init__')
    def test_sends_account(self, init, fetch):
        "Should send the username to the Fetcher"
        init.return_value = None
        call_command('fetch_lastfm_scrobbles', account='terry')
        init.assert_called_with(username='terry')

    @patch.object(ScrobblesMultiAccountFetcher, 'fetch')
    @patch.object(ScrobblesMultiAccountFetcher, '__init__')
    def test_sends_no_account(self, init, fetch):
        "Should send None to the Fetcher"
        init.return_value = None
        call_command('fetch_lastfm_scrobbles')
        init.assert_called_with(username=None)

    @patch.object(ScrobblesMultiAccountFetcher, 'fetch')
    def test_success_output(self, fetch):
        fetch.return_value = \
                    [{'account': 'terry', 'success': True, 'fetched': '30',},]
        call_command('fetch_lastfm_scrobbles', stdout=self.out)
        self.assertIn('terry: Fetched 30 Scrobbles', self.out.getvalue())

    @patch.object(ScrobblesMultiAccountFetcher, 'fetch')
    def test_success_output_verbosity_0(self, fetch):
        fetch.return_value = \
                    [{'account': 'terry', 'success': True, 'fetched': '30',},]
        call_command('fetch_lastfm_scrobbles', verbosity=0, stdout=self.out)
        self.assertEqual('', self.out.getvalue())

    @patch.object(ScrobblesMultiAccountFetcher, 'fetch')
    def test_error_output(self, fetch):
        fetch.return_value = \
            [{'account': 'terry', 'success': False, 'messages': ['Oops',],},]
        call_command('fetch_lastfm_scrobbles',
                                        stdout=self.out, stderr=self.out_err)
        self.assertIn('terry: Failed to fetch Scrobbles: Oops',
                                                    self.out_err.getvalue())

