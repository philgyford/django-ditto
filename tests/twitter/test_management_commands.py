# coding: utf-8
from unittest.mock import patch, Mock

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase
from django.utils.six import StringIO

from ditto.twitter import factories
from ditto.twitter.models import Tweet


class FetchTwitterArgs(TestCase):
    "Testing the handling of arguments passed to the commands."

    # Child classes should set this:
    fetcher_class_path = ''

    def setUp(self):
        self.patcher = patch(self.fetcher_class_path)
        self.fetcher_class = self.patcher.start()

    def tearDown(self):
        self.patcher.stop()


class FetchTwitterTweetsArgs(FetchTwitterArgs):

    fetcher_class_path = 'ditto.twitter.management.commands.fetch_twitter_tweets.RecentTweetsFetcher'

    def test_fail_with_no_args(self):
        "Fails when no arguments are provided"
        with self.assertRaises(CommandError):
            call_command('fetch_twitter_tweets')

    def test_fail_with_account_only(self):
        "Fails when only an account is provided"
        with self.assertRaises(CommandError):
            call_command('fetch_twitter_tweets', account='terry')

    def test_with_recent(self):
        "Calls the correct method when fetching recent tweets"
        call_command('fetch_twitter_tweets', recent='new')
        self.fetcher_class.assert_called_once_with(screen_name=None)
        self.fetcher_class().fetch.assert_called_once_with(count='new')

    def test_with_recent_and_account(self):
        "Calls the correct method when fetching one account's recent tweets"
        call_command('fetch_twitter_tweets', recent='new', account='barbara')
        self.fetcher_class.assert_called_once_with(screen_name='barbara')
        self.fetcher_class().fetch.assert_called_once_with(count='new')

    def test_with_number(self):
        "Should send an int to fetch()."
        call_command('fetch_twitter_tweets', recent='25')
        self.fetcher_class.assert_called_once_with(screen_name=None)
        self.fetcher_class().fetch.assert_called_once_with(count=25)


class FetchTwitterFavoritesArgs(FetchTwitterArgs):

    fetcher_class_path = 'ditto.twitter.management.commands.fetch_twitter_favorites.FavoriteTweetsFetcher'

    def test_fail_with_no_args(self):
        "Fails when no arguments are provided"
        with self.assertRaises(CommandError):
            call_command('fetch_twitter_favorites')

    def test_fail_with_account_only(self):
        "Fails when only an account is provided"
        with self.assertRaises(CommandError):
            call_command('fetch_twitter_favorites', account='terry')

    def test_with_favorites(self):
        "Calls the correct method when fetching favorite tweets"
        call_command('fetch_twitter_favorites', recent='new', stdout=StringIO())
        self.fetcher_class.assert_called_once_with(screen_name=None)
        self.fetcher_class().fetch.assert_called_once_with(count='new')

    def test_with_favorites_and_account(self):
        "Calls the correct method when fetching one account's favorite tweets"
        call_command('fetch_twitter_favorites', recent='new',
                                    account='barbara', stdout=StringIO())
        self.fetcher_class.assert_called_once_with(screen_name='barbara')
        self.fetcher_class().fetch.assert_called_once_with(count='new')

    def test_with_favorites(self):
        "Should send an int to fetch()"
        call_command('fetch_twitter_favorites', recent='25', stdout=StringIO())
        self.fetcher_class.assert_called_once_with(screen_name=None)
        self.fetcher_class().fetch.assert_called_once_with(count=25)


class FetchTwitterOutput(TestCase):
    "Testing the commands output what they should on success/failure."

    # Child classes should set this:
    fetch_method_path = ''

    def setUp(self):
        self.patcher = patch(self.fetch_method_path)
        self.fetch_method = self.patcher.start()

        user = factories.UserFactory(screen_name='philgyford')
        self.account = factories.AccountFactory(user=user, is_active=True)
        self.out = StringIO()
        self.out_err = StringIO()

    def tearDown(self):
        self.patcher.stop()


class FetchTwitterTweetsOutput(FetchTwitterOutput):

    fetch_method_path = 'ditto.twitter.management.commands.fetch_twitter_tweets.RecentTweetsFetcher.fetch'

    def test_success_output(self):
        "Responds correctly when recent tweets were successfully fetched"
        # What the mocked method will return:
        self.fetch_method.side_effect = [
            [{'account': 'philgyford', 'success': True, 'fetched': 23}]
        ]
        call_command('fetch_twitter_tweets', recent='new', stdout=self.out)
        self.assertIn('philgyford: Fetched 23 Tweets', self.out.getvalue())

    def test_success_output_verbosity_0(self):
        "Outputs nothing when recent tweets were successfully fetched"
        # What the mocked method will return:
        self.fetch_method.side_effect = [
            [{'account': 'philgyford', 'success': True, 'fetched': 23}]
        ]
        call_command(
            'fetch_twitter_tweets', recent='new', verbosity=0, stdout=self.out)
        self.assertEqual('', self.out.getvalue())

    def test_error_output(self):
        "Responds correctly when there was an error fetching recent tweets"
        self.fetch_method.side_effect = [
            [{'account': 'philgyford', 'success': False,
                                                    'messages': ['It broke']}]
        ]
        call_command('fetch_twitter_tweets', recent='new', stdout=self.out,
                                                        stderr=self.out_err)
        self.assertIn('philgyford: Failed to fetch Tweets: It broke',
                                                    self.out_err.getvalue())


class FetchTwitterFavoritesOutput(FetchTwitterOutput):

    fetch_method_path = 'ditto.twitter.management.commands.fetch_twitter_favorites.FavoriteTweetsFetcher.fetch'

    def test_success_output(self):
        "Responds correctly when recent tweets were successfully fetched"
        self.fetch_method.side_effect = [
            [{'account': 'philgyford', 'success': True, 'fetched': 23}]
        ]
        call_command('fetch_twitter_favorites', recent='new', stdout=self.out)
        self.assertIn('philgyford: Fetched 23 Tweets', self.out.getvalue())

    def test_success_output_verbosity_0(self):
        "Outputs nothing when recent tweets were successfully fetched"
        self.fetch_method.side_effect = [
            [{'account': 'philgyford', 'success': True, 'fetched': 23}]
        ]
        call_command('fetch_twitter_favorites',
                                    recent='new', verbosity=0, stdout=self.out)
        self.assertEqual('', self.out.getvalue())

    def test_error_output(self):
        "Responds correctly when there was an error fetching recent tweets"
        self.fetch_method.side_effect = [
            [{'account': 'philgyford', 'success': False,
                                                    'messages': ['It broke']}]
        ]
        call_command('fetch_twitter_favorites', recent='new', stdout=self.out,
                                                        stderr=self.out_err)
        self.assertIn('philgyford: Failed to fetch Tweets: It broke',
                                                    self.out_err.getvalue())


class FetchTwitterAccountsOutput(FetchTwitterOutput):

    fetch_method_path = 'ditto.twitter.management.commands.fetch_twitter_accounts.VerifyFetcher.fetch'

    def test_success_output(self):
        "Responds correctly when users were successfully fetched"
        self.fetch_method.side_effect = [
            [{'account': 'philgyford', 'success': True}]
        ]
        call_command('fetch_twitter_accounts', stdout=self.out)
        self.assertIn('Fetched @philgyford', self.out.getvalue())

    def test_success_output_verbosity_0(self):
        "Outputs nothing when users were successfully fetched"
        self.fetch_method.side_effect = [
            [{'account': 'philgyford', 'success': True}]
        ]
        call_command('fetch_twitter_accounts', verbosity=0, stdout=self.out)
        self.assertEqual('', self.out.getvalue())

    def test_error_output(self):
        "Responds correctly when there was an error fetching users"
        self.fetch_method.side_effect = [
                [{'account': 'philgyford', 'success': False,
                                                    'messages': ['It broke']}]
        ]
        call_command('fetch_twitter_accounts', stdout=self.out, stderr=self.out_err)
        self.assertIn('Could not fetch @philgyford: It broke',
                                                        self.out_err.getvalue())


class ImportTweets(TestCase):

    def setUp(self):
        self.patcher = patch('ditto.twitter.management.commands.import_twitter_tweets.TweetIngester.ingest')
        self.ingest_mock = self.patcher.start()
        self.out = StringIO()
        self.out_err = StringIO()

    def tearDown(self):
        self.patcher.stop()

    def test_fails_with_no_args(self):
        "Fails when no arguments are provided"
        with self.assertRaises(CommandError):
            call_command('import_twitter_tweets')

    def test_fails_with_invalid_directory(self):
        with patch('os.path.isdir', return_value=False):
            with self.assertRaises(CommandError):
                call_command('import_twitter_tweets', path='/wrong/path')

    def test_calls_ingest_method(self):
        with patch('os.path.isdir', return_value=True):
            call_command('import_twitter_tweets', path='/right/path',
                                                            stdout=self.out)
            self.ingest_mock.assert_called_once_with(
                                        directory='/right/path/data/js/tweets')

    def test_success_output(self):
        """Outputs the correct response if ingesting succeeds."""
        self.ingest_mock.return_value = {
            'success': True, 'tweets': 12345, 'files': 21
        }
        with patch('os.path.isdir', return_value=True):
            call_command('import_twitter_tweets', path='/right/path',
                                                            stdout=self.out)
            self.assertIn('Imported 12345 tweets from 21 files',
                                                            self.out.getvalue())

    def test_success_output_verbosity_0(self):
        """Outputs nothing if ingesting succeeds."""
        self.ingest_mock.return_value = {
            'success': True, 'tweets': 12345, 'files': 21
        }
        with patch('os.path.isdir', return_value=True):
            call_command('import_twitter_tweets',
                            path='/right/path', verbosity=0, stdout=self.out)
            self.assertEqual('', self.out.getvalue())

    def test_error_output(self):
        """Outputs the correct error if ingesting fails."""
        self.ingest_mock.return_value = {
            'success': False, 'messages': ['Something went wrong'],
        }
        with patch('os.path.isdir', return_value=True):
            call_command('import_twitter_tweets', path='/right/path',
                                        stdout=self.out, stderr=self.out_err)
            self.assertIn('Something went wrong', self.out_err.getvalue())


class GenerateTweetHtml(TestCase):

    def setUp(self):
        user_1 = factories.UserFactory(screen_name='terry')
        user_2 = factories.UserFactory(screen_name='bob')
        tweets_1 = factories.TweetFactory.create_batch(2, user=user_1)
        tweets_2 = factories.TweetFactory.create_batch(3, user=user_2)
        account_1 = factories.AccountFactory(user=user_1)
        account_2 = factories.AccountFactory(user=user_2)
        self.out = StringIO()

    @patch.object(Tweet, 'save')
    def test_with_all_accounts(self, save_method):
        call_command('generate_twitter_tweet_html', stdout=self.out)
        self.assertEqual(save_method.call_count, 5)
        self.assertIn('Generated HTML for 5 Tweets', self.out.getvalue())

    @patch.object(Tweet, 'save')
    def test_with_one_account(self, save_method):
        call_command('generate_twitter_tweet_html', account='terry',
                                                            stdout=self.out)
        self.assertEqual(save_method.call_count, 2)
        self.assertIn('Generated HTML for 2 Tweets', self.out.getvalue())

    def test_with_invalid_account(self):
        with self.assertRaises(CommandError):
            call_command('generate_twitter_tweet_html', account='thelma')


class UpdateUsers(TestCase):

    def setUp(self):
        user_1 = factories.UserFactory(screen_name='terry')
        user_2 = factories.UserFactory(screen_name='bob')
        account_1 = factories.AccountFactory(user=user_1)
        account_2 = factories.AccountWithCredentialsFactory(user=user_2)

        self.patcher = patch('ditto.twitter.management.commands.update_twitter_users.UsersFetcher')
        self.fetcher_class = self.patcher.start()
        self.out = StringIO()
        self.out_err = StringIO()

    def tearDown(self):
        self.patcher.stop()

    def test_with_account(self):
        call_command('update_twitter_users', account='bob')
        self.fetcher_class.assert_called_once_with(screen_name='bob')
        self.fetcher_class().fetch.assert_called_once_with()

    def test_without_account(self):
        with self.assertRaises(CommandError):
            call_command('update_twitter_users')

    def test_success_output(self):
        self.fetcher_class().fetch.side_effect = [
            [{'account': 'philgyford', 'success': True, 'fetched': 612}]
        ]
        call_command('update_twitter_users', account='bob', stdout=self.out)
        self.assertIn('philgyford: Fetched 612 Users', self.out.getvalue())

    def test_success_output_verbosity_0(self):
        self.fetcher_class().fetch.side_effect = [
            [{'account': 'philgyford', 'success': True, 'fetched': 612}]
        ]
        call_command('update_twitter_users',
                                account='bob', verbosity=0, stdout=self.out)
        self.assertEqual('', self.out.getvalue())

    def test_error_output(self):
        self.fetcher_class().fetch.side_effect = [
            [{'account': 'philgyford', 'success': False,
                                                    'messages': ['It broke']}]
        ]
        call_command('update_twitter_users', account='bob', stdout=self.out,
                                                        stderr=self.out_err)
        self.assertIn('philgyford: Failed to fetch Users: It broke',
                                                    self.out_err.getvalue())


class UpdateTweets(TestCase):

    def setUp(self):
        user_1 = factories.UserFactory(screen_name='terry')
        user_2 = factories.UserFactory(screen_name='bob')
        account_1 = factories.AccountFactory(user=user_1)
        account_2 = factories.AccountWithCredentialsFactory(user=user_2)

        self.patcher = patch('ditto.twitter.management.commands.update_twitter_tweets.TweetsFetcher')
        self.fetcher_class = self.patcher.start()
        self.out = StringIO()
        self.out_err = StringIO()

    def tearDown(self):
        self.patcher.stop()

    def test_with_account(self):
        call_command('update_twitter_tweets', account='bob')
        self.fetcher_class.assert_called_once_with(screen_name='bob')
        self.fetcher_class().fetch.assert_called_once_with()

    def test_without_account(self):
        with self.assertRaises(CommandError):
            call_command('update_twitter_tweets')

    def test_success_output(self):
        self.fetcher_class().fetch.side_effect = [
            [{'account': 'philgyford', 'success': True, 'fetched': 612}]
        ]
        call_command('update_twitter_tweets', account='bob', stdout=self.out)
        self.assertIn('philgyford: Fetched 612 Tweets', self.out.getvalue())

    def test_success_output_verbosity_0(self):
        self.fetcher_class().fetch.side_effect = [
            [{'account': 'philgyford', 'success': True, 'fetched': 612}]
        ]
        call_command('update_twitter_tweets',
                                account='bob', verbosity=0, stdout=self.out)
        self.assertEqual('', self.out.getvalue())

    def test_error_output(self):
        self.fetcher_class().fetch.side_effect = [
            [{'account': 'philgyford', 'success': False,
                                                    'messages': ['It broke']}]
        ]
        call_command('update_twitter_tweets', account='bob', stdout=self.out,
                                                        stderr=self.out_err)
        self.assertIn('philgyford: Failed to fetch Tweets: It broke',
                                                    self.out_err.getvalue())


class FetchFiles(TestCase):

    def setUp(self):
        self.out = StringIO()
        self.out_err = StringIO()

    @patch('ditto.twitter.management.commands.fetch_twitter_files.FilesFetcher')
    def test_sends_all_true_to_fetcher(self, fetcher):
        call_command('fetch_twitter_files', '--all')
        fetcher.assert_called_with()
        fetcher.return_value.fetch.assert_called_with(fetch_all=True)

    @patch('ditto.twitter.management.commands.fetch_twitter_files.FilesFetcher')
    def test_sends_all_false_to_fetcher(self, fetcher):
        call_command('fetch_twitter_files')
        fetcher.assert_called_with()
        fetcher.return_value.fetch.assert_called_with(fetch_all=False)

    @patch('ditto.twitter.management.commands.fetch_twitter_files.FilesFetcher')
    def test_success_output(self, fetcher):
        fetcher.return_value.fetch.return_value =\
                                            [{'success': True, 'fetched': 33}]
        call_command('fetch_twitter_files', stdout=self.out)
        self.assertIn('Fetched 33 Files', self.out.getvalue())

    @patch('ditto.twitter.management.commands.fetch_twitter_files.FilesFetcher')
    def test_success_output_verbosity_0(self, fetcher):
        fetcher.return_value.fetch.return_value =\
                                            [{'success': True, 'fetched': 33}]
        call_command('fetch_twitter_files', verbosity=0, stdout=self.out)
        self.assertEqual('', self.out.getvalue())

    @patch('ditto.twitter.management.commands.fetch_twitter_files.FilesFetcher')
    def test_error_output(self, fetcher):
        fetcher.return_value.fetch.return_value =\
                                    [{'success': False, 'messages': ['Oops']}]
        call_command('fetch_twitter_files', stdout=self.out,
                                                        stderr=self.out_err)
        self.assertIn('Failed to fetch Files: Oops', self.out_err.getvalue())

