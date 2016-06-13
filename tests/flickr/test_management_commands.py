from unittest.mock import patch, Mock

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase
from django.utils.six import StringIO

from ditto.flickr.factories import AccountFactory, UserFactory


class FetchFlickrAccountUserTestCase(TestCase):

    def setUp(self):
        # What we'll use as return values from UserIdFetcher().fetch()...
        self.id_fetcher_success =\
                    {'success': True, 'id': '35034346050@N01', 'fetched': 1}
        # ...and UserFetcher().fetch():
        self.user_fetcher_success =\
            {'success': True, 'user': {'name': 'Phil Gyford'}, 'fetched': 1}

        self.account = AccountFactory(id=32, user=None)
        self.out = StringIO()
        self.out_err = StringIO()

    def test_fail_with_no_args(self):
        with self.assertRaises(CommandError):
            call_command('fetch_flickr_account_user')

    def test_fail_with_invalid_id(self):
        call_command('fetch_flickr_account_user', id='3', stderr=self.out_err)
        self.assertIn("No Account found with an id of '3'",
                                                    self.out_err.getvalue())

    @patch('ditto.flickr.management.commands.fetch_flickr_account_user.UserFetcher')
    @patch('ditto.flickr.management.commands.fetch_flickr_account_user.UserIdFetcher')
    def test_with_id(self, id_fetcher, user_fetcher):
        user = UserFactory(nsid='35034346050@N01')
        id_fetcher.return_value.fetch.return_value = self.id_fetcher_success
        user_fetcher.return_value.fetch.return_value = self.user_fetcher_success
        call_command('fetch_flickr_account_user', id='32', stdout=self.out)
        self.assertIn("Fetched and saved user 'Phil Gyford'",
                                                        self.out.getvalue())

    @patch('ditto.flickr.management.commands.fetch_flickr_account_user.UserFetcher')
    @patch('ditto.flickr.management.commands.fetch_flickr_account_user.UserIdFetcher')
    def test_invalid_nsid(self, id_fetcher, user_fetcher):
        """
        Correct error message if we fail to find a user for the fetched
        Flickr ID (unlikely).
        """
        id_fetcher.return_value.fetch.return_value =  self.id_fetcher_success
        user_fetcher.return_value.fetch.return_value =\
                                    {'success': False, 'messages': ['Oops']}
        call_command('fetch_flickr_account_user', id='32', stderr=self.out_err)
        self.assertIn(
            "Failed to fetch a user using Flickr ID '35034346050@N01': Oops",
            self.out_err.getvalue())

    @patch('ditto.flickr.management.commands.fetch_flickr_account_user.UserIdFetcher')
    def test_no_matching_nsid(self, id_fetcher):
        "Correct error message if we can't find a Flickr ID for this Account."
        id_fetcher.return_value.fetch.return_value =\
                                    {'success': False, 'messages': ['Oops']}
        call_command('fetch_flickr_account_user', id='32', stderr=self.out_err)
        self.assertIn(
            "Failed to fetch a Flickr ID for this Account: Oops",
            self.out_err.getvalue())

    @patch('ditto.flickr.management.commands.fetch_flickr_account_user.UserFetcher')
    @patch('ditto.flickr.management.commands.fetch_flickr_account_user.UserIdFetcher')
    def test_associates_account_with_user(self, id_fetcher, user_fetcher):
        "After fetching and saving the user, associate it with the Account."
        user = UserFactory(nsid='35034346050@N01')
        id_fetcher.return_value.fetch.return_value = self.id_fetcher_success
        user_fetcher.return_value.fetch.return_value = self.user_fetcher_success
        call_command('fetch_flickr_account_user', id='32', stdout=self.out)
        self.account.refresh_from_db()
        self.assertEqual(self.account.user.nsid, '35034346050@N01')


class FetchFlickrOriginalsTestCase(TestCase):

    def setUp(self):
        self.out = StringIO()
        self.out_err = StringIO()

    @patch('ditto.flickr.management.commands.fetch_flickr_originals.OriginalFilesMultiAccountFetcher')
    def test_sends_all_true_to_fetcher_with_account(self, fetcher):
        call_command(
                'fetch_flickr_originals', '--all', account='35034346050@N01')
        fetcher.assert_called_with(nsid='35034346050@N01')
        fetcher.return_value.fetch.assert_called_with(fetch_all=True)

    @patch('ditto.flickr.management.commands.fetch_flickr_originals.OriginalFilesMultiAccountFetcher')
    def test_sends_all_true_to_fetcher_no_account(self, fetcher):
        call_command('fetch_flickr_originals', '--all')
        fetcher.assert_called_with(nsid=None)
        fetcher.return_value.fetch.assert_called_with(fetch_all=True)

    @patch('ditto.flickr.management.commands.fetch_flickr_originals.OriginalFilesMultiAccountFetcher')
    def test_sends_all_false_to_fetcher(self, fetcher):
        call_command('fetch_flickr_originals')
        fetcher.assert_called_with(nsid=None)
        fetcher.return_value.fetch.assert_called_with(fetch_all=False)

    @patch('ditto.flickr.management.commands.fetch_flickr_originals.OriginalFilesMultiAccountFetcher')
    def test_success_output(self, fetcher):
        fetcher.return_value.fetch.return_value =\
            [{'account': 'Phil Gyford', 'success': True, 'fetched': 33}]
        call_command('fetch_flickr_originals', stdout=self.out)
        self.assertIn('Phil Gyford: Fetched 33 Files', self.out.getvalue())

    @patch('ditto.flickr.management.commands.fetch_flickr_originals.OriginalFilesMultiAccountFetcher')
    def test_success_output_verbosity_0(self, fetcher):
        fetcher.return_value.fetch.return_value =\
            [{'account': 'Phil Gyford', 'success': True, 'fetched': 33}]
        call_command('fetch_flickr_originals', verbosity=0, stdout=self.out)
        self.assertEqual('', self.out.getvalue())

    @patch('ditto.flickr.management.commands.fetch_flickr_originals.OriginalFilesMultiAccountFetcher')
    def test_error_output(self, fetcher):
        fetcher.return_value.fetch.return_value =\
            [{'account': 'Phil Gyford', 'success': False, 'messages': ['Oops']}]
        call_command('fetch_flickr_originals', stdout=self.out,
                                                        stderr=self.out_err)
        self.assertIn('Phil Gyford: Failed to fetch Files: Oops',
                                                    self.out_err.getvalue())


class FetchFlickrPhotosTestCase(TestCase):

    def setUp(self):
        self.out = StringIO()
        self.out_err = StringIO()

    def test_fail_with_no_args(self):
        with self.assertRaises(CommandError):
            call_command('fetch_flickr_photos')

    def test_fail_with_account_only(self):
        with self.assertRaises(CommandError):
            call_command('fetch_flickr_photos', account='35034346050@N01')

    def test_fail_with_non_numeric_days(self):
        with self.assertRaises(CommandError):
            call_command('fetch_flickr_photos', days='foo')

    @patch('ditto.flickr.management.commands.fetch_flickr_photos.RecentPhotosMultiAccountFetcher')
    def test_sends_days_to_fetcher_with_account(self, fetcher):
        call_command('fetch_flickr_photos', account='35034346050@N01', days='4')
        fetcher.assert_called_with(nsid='35034346050@N01')
        fetcher.return_value.fetch.assert_called_with(days=4)

    @patch('ditto.flickr.management.commands.fetch_flickr_photos.RecentPhotosMultiAccountFetcher')
    def test_sends_days_to_fetcher_no_account(self, fetcher):
        call_command('fetch_flickr_photos', days='4')
        fetcher.assert_called_with(nsid=None)
        fetcher.return_value.fetch.assert_called_with(days=4)

    @patch('ditto.flickr.management.commands.fetch_flickr_photos.RecentPhotosMultiAccountFetcher')
    def test_sends_all_to_fetcher_with_account(self, fetcher):
        call_command(
                'fetch_flickr_photos', account='35034346050@N01', days='all')
        fetcher.assert_called_with(nsid='35034346050@N01')
        fetcher.return_value.fetch.assert_called_with(days='all')

    @patch('ditto.flickr.management.commands.fetch_flickr_photos.RecentPhotosMultiAccountFetcher')
    def test_success_output(self, fetcher):
        fetcher.return_value.fetch.return_value =\
            [{'account': 'Phil Gyford', 'success': True, 'fetched': '40'}]
        call_command('fetch_flickr_photos', days='4', stdout=self.out)
        self.assertIn('Phil Gyford: Fetched 40 Photos', self.out.getvalue())

    @patch('ditto.flickr.management.commands.fetch_flickr_photos.RecentPhotosMultiAccountFetcher')
    def test_success_output_verbosity_0(self, fetcher):
        fetcher.return_value.fetch.return_value =\
            [{'account': 'Phil Gyford', 'success': True, 'fetched': '40'}]
        call_command('fetch_flickr_photos',
                                        days='4', verbosity=0, stdout=self.out)
        self.assertEqual('', self.out.getvalue())

    @patch('ditto.flickr.management.commands.fetch_flickr_photos.RecentPhotosMultiAccountFetcher')
    def test_error_output(self, fetcher):
        fetcher.return_value.fetch.return_value =\
            [{'account': 'Phil Gyford', 'success': False, 'messages': ['Oops']}]
        call_command('fetch_flickr_photos', days='4', stdout=self.out,
                                                        stderr=self.out_err)
        self.assertIn('Phil Gyford: Failed to fetch Photos: Oops',
                                                    self.out_err.getvalue())


class FetchFlickrPhotosetsTestCase(TestCase):

    def setUp(self):
        self.out = StringIO()
        self.out_err = StringIO()

    @patch('ditto.flickr.management.commands.fetch_flickr_photosets.PhotosetsMultiAccountFetcher')
    def test_calls_fetcher_with_account(self, fetcher):
        call_command('fetch_flickr_photosets', account='35034346050@N01')
        fetcher.assert_called_with(nsid='35034346050@N01')
        fetcher.return_value.fetch.assert_called_with()

    @patch('ditto.flickr.management.commands.fetch_flickr_photosets.PhotosetsMultiAccountFetcher')
    def test_calls_fetcher_with_no_account(self, fetcher):
        call_command('fetch_flickr_photosets')
        fetcher.assert_called_with(nsid=None)
        fetcher.return_value.fetch.assert_called_with()

    @patch('ditto.flickr.management.commands.fetch_flickr_photosets.PhotosetsMultiAccountFetcher')
    def test_success_output(self, fetcher):
        fetcher.return_value.fetch.return_value =\
            [{'account': 'Phil Gyford', 'success': True, 'fetched': '40'}]
        call_command('fetch_flickr_photosets', stdout=self.out)
        self.assertIn('Phil Gyford: Fetched 40 Photosets', self.out.getvalue())

    @patch('ditto.flickr.management.commands.fetch_flickr_photosets.PhotosetsMultiAccountFetcher')
    def test_success_output_verbosity_0(self, fetcher):
        fetcher.return_value.fetch.return_value =\
            [{'account': 'Phil Gyford', 'success': True, 'fetched': '40'}]
        call_command('fetch_flickr_photosets', verbosity=0, stdout=self.out)
        self.assertEqual('', self.out.getvalue())

    @patch('ditto.flickr.management.commands.fetch_flickr_photosets.PhotosetsMultiAccountFetcher')
    def test_error_output(self, fetcher):
        fetcher.return_value.fetch.return_value =\
            [{'account': 'Phil Gyford', 'success': False, 'messages': ['Oops']}]
        call_command('fetch_flickr_photosets', stdout=self.out,
                                                        stderr=self.out_err)
        self.assertIn('Phil Gyford: Failed to fetch Photosets: Oops',
                                                    self.out_err.getvalue())

