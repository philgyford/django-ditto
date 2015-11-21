from unittest.mock import patch, Mock

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase
from django.utils.six import StringIO

from ..factories import AccountFactory


class FetchFlickrArgs(TestCase):
    "Testing the handling of arguments passed to the commands."

    # Child classes should set this:
    fetcher_class_path = ''

    def setUp(self):
        self.patcher = patch(self.fetcher_class_path)
        self.fetcher_class = self.patcher.start()

    def tearDown(self):
        self.patcher.stop()


class FetchFlickrUserArgs(FetchFlickrArgs):

    fetcher_class_path = 'ditto.flickr.management.commands.fetch_flickr_user.UserFetcher'

    def test_fail_with_no_args(self):
        with self.assertRaises(CommandError):
            call_command('fetch_flickr_user')

    def test_fail_with_invalid_url(self):
        with self.assertRaises(CommandError):
            call_command('fetch_flickr_user', url='Not a URL')

    def test_with_url(self):
        "Calls the correct method when a valid URL is supplied"
        call_command('fetch_flickr_user', url='https://www.flickr.com/philgyford')
        self.fetcher_class.assert_called_once_with()
        self.fetcher_class().fetch.assert_called_once_with(url='https://www.flickr.com/philgyford')


class FetchFlickrOutput(TestCase):
    "Testing the commands output what they should on success/failure."

    # Child classes should set this:
    fetch_method_path = ''

    def setUp(self):
        self.patcher = patch(self.fetch_method_path)
        self.fetch_method = self.patcher.start()
        self.account = AccountFactory(is_active=True)
        self.out = StringIO()
        self.out_err = StringIO()

    def tearDown(self):
        self.patcher.stop()


class FetchFlickrUserOutput(FetchFlickrOutput):

    fetch_method_path = 'ditto.flickr.management.commands.fetch_flickr_user.UserFetcher.fetch'

    def test_success_output(self):
        self.fetch_method.side_effect = [
            [{'success': True, 'user': {'name': 'Phil Gyford'}},]
        ]
        call_command('fetch_flickr_user',
                    url='https://www.flickr.com/philgyford', stdout=self.out)
        self.assertIn("Fetched user 'Phil Gyford'", self.out.getvalue())

    def test_error_output(self):
        self.fetch_method.side_effect = [
            [{'success': False, 'message': 'It broke'},]
        ]
        call_command('fetch_flickr_user',
                                        url='https://www.flickr.com/fakeuser',
                                        stdout=self.out, stderr=self.out_err)
        self.assertIn("Failed to fetch a user using URL 'https://www.flickr.com/fakeuser': It broke", self.out_err.getvalue())

