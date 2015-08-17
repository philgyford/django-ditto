# coding: utf-8
from mock import patch

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase
from django.utils.six import StringIO

from .. import factories


class FetchTwitterTweetsArgs(TestCase):

    def test_fail_with_no_args(self):
        "Fails when no arguments are provided"
        with self.assertRaises(CommandError):
            call_command('fetch_twitter_tweets')

    def test_fail_with_account_only(self):
        "Fails when only an account is provided"
        with self.assertRaises(CommandError):
            call_command('fetch_twitter_tweets', account='terry')

    @patch('ditto.twitter.management.commands.fetch_twitter_tweets.RecentTweetsFetcher')
    def test_with_recent(self, fetch_class):
        "Calls the correct method when fetching recent tweets"
        call_command('fetch_twitter_tweets', '--recent', stdout=StringIO())
        fetch_class.assert_called_once_with(screen_name=None)

    @patch('ditto.twitter.management.commands.fetch_twitter_tweets.RecentTweetsFetcher')
    def test_with_recent_and_account(self, fetch_class):
        "Calls the correct method when fetching one account's recent tweets"
        call_command('fetch_twitter_tweets', '--recent', account='barbara',
                                                            stdout=StringIO())
        fetch_class.assert_called_once_with(screen_name='barbara')

    @patch('ditto.twitter.management.commands.fetch_twitter_tweets.FavoriteTweetsFetcher')
    def test_with_favorites(self, fetch_class):
        "Calls the correct method when fetching favorite tweets"
        call_command('fetch_twitter_tweets', '--favorites', stdout=StringIO())
        fetch_class.assert_called_once_with(screen_name=None)

    @patch('ditto.twitter.management.commands.fetch_twitter_tweets.FavoriteTweetsFetcher')
    def test_with_favorites_and_account(self, fetch_class):
        "Calls the correct method when fetching one account's favorite tweets"
        call_command('fetch_twitter_tweets', '--favorites',
                                    account='barbara', stdout=StringIO())
        fetch_class.assert_called_once_with(screen_name='barbara')


class FetchTwitterTweetsOutput(TestCase):

    @patch('ditto.twitter.management.commands.fetch_twitter_tweets.RecentTweetsFetcher.fetch')
    def test_success_output(self, fetch_method):
        "Responds correctly when recent tweets were successfully fetched"
        # What the mocked method will return:
        fetch_method.side_effect = [
            [{'account': 'philgyford', 'success': True, 'fetched': 23}]
        ]
        out = StringIO()
        call_command('fetch_twitter_tweets', '--recent', stdout=out)
        self.assertIn('philgyford: Fetched 23 tweets', out.getvalue())

    @patch('ditto.twitter.management.commands.fetch_twitter_tweets.RecentTweetsFetcher.fetch')
    def test_error_output(self, fetch_method):
        "Responds correctly when there was an error fetching recent tweets"
        # What the mocked method will return:
        fetch_method.side_effect = [
                [{'account': 'philgyford', 'success': False,
                    'message': 'It broke'}]
        ]
        out = StringIO()
        out_err = StringIO()
        call_command('fetch_twitter_tweets', '--recent', stdout=out,
                                                                stderr=out_err)
        self.assertIn('philgyford: Failed to fetch tweets: It broke',
                                                            out_err.getvalue())


#class UpdateAccounts(TestCase):

    #@patch('ditto.twitter.fetch.UpdateAccounts.update_all')
    #def test_calls_correct_method(self, update_method):
        #call_command('update_twitter_accounts', stdout=StringIO())
        #update_method.assert_called_once_with()

    #@patch('ditto.twitter.fetch.UpdateAccounts.update_all')
    #def test_success_output(self, update_method):
        #"Responds correctly when accounts were successfully updated"
        ## What the mocked method will return:
        #update_method.side_effect = [
            #[{'account': 'philgyford', 'success': True}]
        #]
        #out = StringIO()
        #call_command('update_twitter_accounts', stdout=out)
        #self.assertIn('Updated Account "philgyford"', out.getvalue())

    #@patch('ditto.twitter.fetch.UpdateAccounts.update_all')
    #def test_error_output(self, update_method):
        #"Responds correctly when accounts were successfully updated"
        ## What the mocked method will return:
        #update_method.side_effect = [
            #[{'account': 'ID: 7', 'success': False, 'message': 'It broke'}]
        #]
        #out = StringIO()
        #out_err = StringIO()
        #call_command('update_twitter_accounts', stdout=out, stderr=out_err)
        #self.assertIn('Failed to update Account "ID: 7": It broke',
                                                            #out_err.getvalue())

