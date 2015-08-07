# coding: utf-8
from mock import patch

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase
from django.utils.six import StringIO


class FetchTwitterTweetsArgs(TestCase):

    def test_fail_with_no_args(self):
        "Fails when no arguments are provided"
        with self.assertRaises(CommandError):
            call_command('fetch_twitter_tweets')

    def test_fail_with_account_only(self):
        "Fails when only an account is provided"
        with self.assertRaises(CommandError):
            call_command('fetch_twitter_tweets', account='philgyford')

    @patch('ditto.twitter.fetch.FetchTweets.fetch_recent')
    def test_with_recent(self, fetch_method):
        "Calls the correct method when fetching recent tweets"
        call_command('fetch_twitter_tweets', '--recent', stdout=StringIO())
        fetch_method.assert_called_once_with(num=None, screen_name=None)

    @patch('ditto.twitter.fetch.FetchTweets.fetch_recent')
    def test_with_recent_and_account(self, fetch_method):
        "Calls the correct method when fetching one account's recent tweets"
        call_command('fetch_twitter_tweets', '--recent', account='philgyford',
                                                            stdout=StringIO())
        fetch_method.assert_called_once_with(num=None, screen_name='philgyford')

    @patch('ditto.twitter.fetch.FetchTweets.fetch_recent')
    def test_with_recent_value(self, fetch_method):
        "Calls the correct method when fetching a number of recent tweets"
        call_command('fetch_twitter_tweets', recent=20, stdout=StringIO())
        fetch_method.assert_called_once_with(num=20, screen_name=None)

    @patch('ditto.twitter.fetch.FetchTweets.fetch_recent')
    def test_with_recent_value_and_account(self, fetch_method):
        """Calls the correct method when fetching a number of one account's
        recent tweets
        """
        call_command('fetch_twitter_tweets', recent=20, account='philgyford',
                                                            stdout=StringIO())
        fetch_method.assert_called_once_with(num=20, screen_name='philgyford')

    @patch('ditto.twitter.fetch.FetchTweets.fetch_favorites')
    def test_with_favorites(self, fetch_method):
        "Calls the correct method when fetching favorite tweets"
        call_command('fetch_twitter_tweets', favorites=20, stdout=StringIO())
        fetch_method.assert_called_once_with(num=20, screen_name=None)

    @patch('ditto.twitter.fetch.FetchTweets.fetch_favorites')
    def test_with_favorites_and_account(self, fetch_method):
        "Calls the correct method when fetching one account's favorite tweets"
        call_command('fetch_twitter_tweets', favorites=20, account='philgyford',
                                                            stdout=StringIO())
        fetch_method.assert_called_once_with(num=20, screen_name='philgyford')


class FetchTwitterTweetsOutput(TestCase):

    @patch('ditto.twitter.fetch.FetchTweets.fetch_recent')
    def test_success_output(self, fetch_method):
        "Responds correctly when recent tweets were successfully fetched"
        # What the mocked method will return:
        fetch_method.side_effect = [
            [{'account': 'philgyford', 'success': True, 'fetched': 23}]
        ]
        out = StringIO()
        call_command('fetch_twitter_tweets', '--recent', stdout=out)
        self.assertIn('philgyford: Fetched 23 tweets', out.getvalue())

    @patch('ditto.twitter.fetch.FetchTweets.fetch_recent')
    def test_error_output(self, fetch_method):
        "Responds correctly when there was an error fetching recent tweets"
        # What the mocked method will return:
        fetch_method.side_effect = [
            [{'success': False, 'message': 'It broke'}]
        ]
        out = StringIO()
        out_err = StringIO()
        call_command('fetch_twitter_tweets', '--recent', stdout=out,
                                                                stderr=out_err)
        self.assertIn('all: Failed to fetch tweets: It broke',
                                                            out_err.getvalue())

