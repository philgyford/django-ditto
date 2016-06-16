import json
import os
import tempfile
from unittest.mock import call, patch

import responses

from django.http import QueryDict
from django.test import override_settings, TestCase

from .test_fetch import FetchTwitterTestCase
from ditto.core.utils.downloader import DownloadException, filedownloader
from ditto.twitter.factories import AccountFactory,\
        AccountWithCredentialsFactory, AnimatedGifFactory, PhotoFactory,\
        TweetFactory, UserFactory, VideoFactory
from ditto.twitter.fetch import FetchError
from ditto.twitter.fetch.savers import UserSaver, TweetSaver
from ditto.twitter.fetch.fetch import FetchFiles,\
        FetchVerify, FetchUsers,\
        FetchTweets, FetchTweetsRecent, FetchTweetsFavorite
from ditto.twitter.fetch.fetchers import FilesFetcher,\
        TwitterFetcher,\
        VerifyFetcher, UsersFetcher,\
        TweetsFetcher, RecentTweetsFetcher, FavoriteTweetsFetcher
from ditto.twitter.models import Account, Tweet, User


class TwitterFetcherSetAccountsTestCase(FetchTwitterTestCase):
    """Testing the private _set_accounts() method of the parent TwitterFetcher
    class.
    """

    def setUp(self):
        user_1 = UserFactory(screen_name='jill')
        user_2 = UserFactory(screen_name='debs')
        account_1 = AccountFactory(user=user_1)
        account_2 = AccountFactory(user=user_2)
        self.fetcher = TwitterFetcher()

    def test_set_accounts_gets_one(self):
        "It gets a single account when passed its screen_name"
        self.fetcher._set_accounts('debs')
        accounts = self.fetcher.accounts
        self.assertEqual(len(accounts), 1)
        self.assertIsInstance(accounts[0], Account)
        self.assertEqual(accounts[0].user.screen_name, 'debs')

    def test_set_accounts_gets_all(self):
        "It gets all accounts when passed no screen_names"
        self.fetcher._set_accounts()
        accounts = self.fetcher.accounts
        self.assertEqual(len(accounts), 2)
        self.assertIsInstance(accounts[0], Account)
        self.assertEqual(accounts[0].user.screen_name, 'debs')
        self.assertIsInstance(accounts[1], Account)
        self.assertEqual(accounts[1].user.screen_name, 'jill')

    def test_set_accounts_bad_screen_name(self):
        "It raises FetchError when passed a non-existent screen_name"
        with self.assertRaises(FetchError):
            self.fetcher._set_accounts('percy')


class TwitterFetcherInactiveAccountsTestCase(FetchTwitterTestCase):

    def setUp(self):
        user_1 = UserFactory(screen_name='jill')
        user_2 = UserFactory(screen_name='debs')
        account_1 = AccountFactory(user=user_1, is_active=False)
        account_2 = AccountFactory(user=user_2, is_active=False)

    def test_set_account_inactive_account(self):
        "It raises FetchError if we try one inactive account."
        with self.assertRaises(FetchError):
            fetcher = TwitterFetcher(screen_name='jill')

    def test_set_account_inactive_all_accounts(self):
        "It raises FetchError if we try accounts and all are inactive."
        with self.assertRaises(FetchError):
            fetcher = TwitterFetcher(screen_name=None)


class TwitterFetcherTestCase(FetchTwitterTestCase):
    """Testing the parent TwitterFetcher class."""

    api_fixture = 'tweets.json'

    def setUp(self):
        """We add the last_recent_id and last_favorite_id to prevent the
        fetcher fetching multiple pages of tweets. Keeps things simpler.
        """
        user_1 = UserFactory(screen_name='jill', twitter_id=1)
        user_2 = UserFactory(screen_name='debs', twitter_id=2)
        self.account_1 = AccountWithCredentialsFactory(
                        user=user_1, last_recent_id=100, last_favorite_id=100)
        self.account_2 = AccountWithCredentialsFactory(
                        user=user_2, last_recent_id=100, last_favorite_id=100)

    def test_raises_error_with_invalid_screen_name(self):
        user = UserFactory(screen_name='goodname')
        account = AccountFactory(user=user)
        with self.assertRaises(FetchError):
            result = RecentTweetsFetcher(screen_name='badname')


class RecentTweetsFetcherTestCase(TwitterFetcherTestCase):
    """Testing the RecentTweetsFetcher class."""

    api_call = 'statuses/user_timeline'

    @responses.activate
    @patch.object(filedownloader, 'download')
    def test_api_request_for_one_account(self, download):
        # Quietly prevents avatar files being fetched:
        download.side_effect = DownloadException('Oops')
        self.add_response(body=self.make_response_body())
        result = RecentTweetsFetcher(screen_name='jill').fetch()
        self.assertEqual(1, len(responses.calls))

    @responses.activate
    @patch.object(filedownloader, 'download')
    def test_api_requests_for_all_accounts(self, download):
        # Quietly prevents avatar files being fetched:
        download.side_effect = DownloadException('Oops')
        self.add_response(body=self.make_response_body())
        result = RecentTweetsFetcher().fetch()
        self.assertEqual(2, len(responses.calls))

    @responses.activate
    @patch.object(filedownloader, 'download')
    def test_ignores_account_with_no_creds(self, download):
        # Quietly prevents avatar files being fetched:
        download.side_effect = DownloadException('Oops')
        user_3 = UserFactory()
        account_3 = AccountFactory(user=user_3)
        self.add_response(body=self.make_response_body())
        result = RecentTweetsFetcher().fetch()
        self.assertEqual(2, len(responses.calls))

    @responses.activate
    def test_includes_last_recent_id_in_response(self):
        "If an account has a last_recent_id, use it in the request"
        self.add_response(body=self.make_response_body())
        result = RecentTweetsFetcher(screen_name='jill').fetch()
        self.assertIn('since_id=100', responses.calls[0][0].url)

    @responses.activate
    def test_omits_last_recent_id_from_response(self):
        "If an account has no last_recent_id, it is not used in the request"
        self.account_1.last_recent_id = None
        self.account_1.save()
        # Stop us fetching multiple pages of results:
        self.add_response(body='[]')
        result = RecentTweetsFetcher(screen_name='jill').fetch()
        self.assertNotIn('since_id=100', responses.calls[0][0].url)

    @responses.activate
    def test_includes_count(self):
        "If fetching a number of tweets, requests that number, not since_id"
        # We're patching the saving of results, so just need the correct
        # number of 'Tweets' in the results:
        body = json.dumps([{'id':1} for x in range(25)])
        self.add_response(body=body)
        with patch.object(FetchTweetsRecent, '_save_results'):
            result = RecentTweetsFetcher(screen_name='jill').fetch(count=25)
            self.assertIn('count=25', responses.calls[0][0].url)
            self.assertNotIn('since_id=100', responses.calls[0][0].url)

    @responses.activate
    def test_updates_last_recent_id_new(self):
        "The account's last_recent_id should be set to the most recent tweet's"
        self.account_1.last_recent_id = 9876543210
        self.account_1.save()
        self.add_response(body=self.make_response_body())
        result = RecentTweetsFetcher(screen_name='jill').fetch()
        self.account_1.refresh_from_db()
        self.assertEqual(self.account_1.last_recent_id, 300)

    @responses.activate
    def test_updates_last_recent_id_count(self):
        """The account's last_recent_id should also be changed if requesting
        count tweets
        """
        self.account_1.last_recent_id = 9876543210
        self.account_1.save()
        body = json.dumps([{'id':999} for x in range(25)])
        self.add_response(body=body)
        with patch.object(FetchTweetsRecent, '_save_results'):
            result = RecentTweetsFetcher(screen_name='jill').fetch(count=25)
            self.account_1.refresh_from_db()
            self.assertEqual(self.account_1.last_recent_id, 999)

    @responses.activate
    def test_returns_correct_success_response(self):
        "Data returned is correct"
        self.add_response(body=self.make_response_body())
        result = RecentTweetsFetcher().fetch()
        self.assertEqual(len(result), 2)
        self.assertTrue(result[1]['account'], 'jill')
        self.assertTrue(result[1]['success'])
        self.assertEqual(result[1]['fetched'], 3)

    @responses.activate
    def test_returns_error_if_api_call_fails(self):
        self.add_response(body='{"errors":[{"message":"Rate limit exceeded","code":88}]}', status=429)
        result = RecentTweetsFetcher(screen_name='jill').fetch()
        self.assertFalse(result[0]['success'])
        self.assertIn('Rate limit exceeded', result[0]['messages'][0])

    @responses.activate
    def test_returns_error_if_no_creds(self):
        "If an account has no API credentials, the result is correct"
        user = UserFactory(screen_name='bobby')
        account = AccountFactory(user=user)
        self.add_response(body=self.make_response_body())
        result = RecentTweetsFetcher(screen_name='bobby').fetch()
        self.assertFalse(result[0]['success'])
        self.assertIn('Account has no API credentials',
                                                    result[0]['messages'][0])

    @responses.activate
    def test_saves_tweets(self):
        self.add_response(body=self.make_response_body())
        result = RecentTweetsFetcher(screen_name='jill').fetch()
        self.assertEqual(Tweet.objects.count(), 3)
        # Our sample tweets are from a different user, so there'll now be 3:
        self.assertEqual(User.objects.count(), 3)

    @responses.activate
    @patch.object(TweetSaver, 'save_tweet')
    def test_saves_correct_tweet_data(self, save_tweet):
        """Assert save_tweet is called once per tweet.
        Not actually checking what's passed in."""
        save_tweet.side_effect = [TweetFactory(),TweetFactory(),TweetFactory()]
        self.add_response(body=self.make_response_body())
        result = RecentTweetsFetcher(screen_name='jill').fetch()
        self.assertEqual(save_tweet.call_count, 3)

    @responses.activate
    @patch.object(filedownloader, 'download')
    def test_fetches_multiple_pages_for_new(self, download):
        "Fetches subsequent pages until no more recent results are returned."
        # Quietly prevents avatar files being fetched:
        download.side_effect = DownloadException('Oops')
        self.account_1.last_recent_id = 10
        self.account_1.save()
        qs = {'user_id': self.account_1.user.twitter_id,
                'include_rts': 'true', 'count': 200, 'since_id': 10}
        self.add_response(body=self.make_response_body(),
                            querystring=qs, match_querystring=True)
        qs['max_id'] = 99
        self.add_response(body='[]', querystring=qs, match_querystring=True)
        with patch('time.sleep'):
            result = RecentTweetsFetcher(screen_name='jill').fetch()
            self.assertEqual(2, len(responses.calls))

    @responses.activate
    def test_fetches_multiple_pages_for_count(self):
        "Fetches subsequent pages until enough counted tweets are returned."
        qs = {'user_id': self.account_1.user.twitter_id,
                                        'include_rts': 'true', 'count': 200}
        # Return "[{id:1}, {id:1}, {id:1}...]" and patch _save_results() as
        # we're only interested in how many times we ask for more results.
        body = json.dumps([{'id':1} for x in range(200)])

        # We're going to request 3 x 200 Tweets and then...
        for n in range(3):
            self.add_response(body=body, querystring=qs, match_querystring=True)
        # ... 1 x 100 Tweets = 700 Tweets.
        qs['count'] = 100
        self.add_response(body=body, querystring=qs, match_querystring=True)

        with patch.object(FetchTweetsRecent, '_save_results'):
            with patch('time.sleep'):
                result = RecentTweetsFetcher(screen_name='jill').fetch(
                                                                    count=700)
                self.assertEqual(4, len(responses.calls))


class FavoriteTweetsFetcherTestCase(TwitterFetcherTestCase):
    """Testing the FavoriteTweetsFetcher class."""

    api_call = 'favorites/list'

    @responses.activate
    @patch.object(filedownloader, 'download')
    def test_api_request_for_one_account(self, download):
        # This will just stop us requesting avatars from Twitter:
        download.side_effect = DownloadException('Ooops')
        self.add_response(body=self.make_response_body())
        result = FavoriteTweetsFetcher(screen_name='jill').fetch()
        self.assertEqual(1, len(responses.calls))

    @responses.activate
    @patch.object(filedownloader, 'download')
    def test_api_requests_for_all_accounts(self, download):
        # This will just stop us requesting avatars from Twitter:
        download.side_effect = DownloadException('Ooops')
        self.add_response(body=self.make_response_body())
        result = FavoriteTweetsFetcher().fetch()
        self.assertEqual(2, len(responses.calls))

    @responses.activate
    @patch.object(filedownloader, 'download')
    def test_ignores_account_with_no_creds(self, download):
        # This will just stop us requesting avatars from Twitter:
        download.side_effect = DownloadException('Ooops')
        # Add a third Account that has no API credentials:
        account_3 = AccountFactory(user=UserFactory())
        self.add_response(body=self.make_response_body())
        result = FavoriteTweetsFetcher().fetch()
        # Should only have fetched faves for the two accounts with API creds:
        self.assertEqual(2, len(responses.calls))

    @responses.activate
    def test_includes_last_favorite_id_in_response(self):
        "If an account has a last_favorite_id, use it in the request"
        self.add_response(body=self.make_response_body())
        result = FavoriteTweetsFetcher(screen_name='jill').fetch()
        self.assertTrue('since_id=100' in responses.calls[0][0].url)

    @responses.activate
    def test_omits_last_favorite_id_from_response(self):
        "If an account has no last_favorite_id, it is not used in the request"
        # Stop us fetching multiple pages of results:
        self.add_response(body='[]')
        result = FavoriteTweetsFetcher(screen_name='jill').fetch()
        self.assertFalse('since_id=9876543210' in responses.calls[0][0].url)

    @responses.activate
    def test_includes_count(self):
        "If fetching a number of tweets, requests that number, not since_id"
        body = json.dumps([{'id':1} for x in range(25)])
        self.add_response(body=body)
        with patch.object(FetchTweetsFavorite, '_save_results'):
            result = FavoriteTweetsFetcher(screen_name='jill').fetch(count=25)
            self.assertIn('count=25', responses.calls[0][0].url)
            self.assertNotIn('since_id=100', responses.calls[0][0].url)

    @responses.activate
    def test_updates_last_favorite_id_new(self):
        "The account's last_favorite_id should be set to the most recent tweet's"
        self.account_1.last_favorite_id = 9876543210
        self.account_1.save()
        self.add_response(body=self.make_response_body())
        result = FavoriteTweetsFetcher(screen_name='jill').fetch()
        self.account_1.refresh_from_db()
        self.assertEqual(self.account_1.last_favorite_id, 300)

    @responses.activate
    def test_updates_last_favorite_id_count(self):
        """The account's last_favorite_id should be changed if requesting count
        tweets
        """
        self.account_1.last_favorite_id = 9876543210
        self.account_1.save()
        body = json.dumps([{'id':999} for x in range(25)])
        self.add_response(body=body)
        with patch.object(FetchTweetsFavorite, '_save_results'):
            result = FavoriteTweetsFetcher(screen_name='jill').fetch(count=25)
            self.account_1.refresh_from_db()
            self.assertEqual(self.account_1.last_favorite_id, 999)

    @responses.activate
    def test_returns_correct_success_response(self):
        "Data returned is correct"
        self.add_response(body=self.make_response_body())
        result = FavoriteTweetsFetcher().fetch()
        self.assertEqual(len(result), 2)
        self.assertEqual(result[1]['account'], 'jill')
        self.assertTrue(result[1]['success'])
        self.assertEqual(result[1]['fetched'], 3)

    @responses.activate
    def test_returns_error_if_api_call_fails(self):
        self.add_response(body='{"errors":[{"message":"Rate limit exceeded","code":88}]}', status=429)
        result = FavoriteTweetsFetcher(screen_name='jill').fetch()
        self.assertFalse(result[0]['success'])
        self.assertIn('Rate limit exceeded', result[0]['messages'][0])

    @responses.activate
    def test_returns_error_if_no_creds(self):
        "If an account has no API credentials, the result is correct"
        user = UserFactory(screen_name='bobby')
        account = AccountFactory(user=user)
        self.add_response(body=self.make_response_body())
        result = FavoriteTweetsFetcher(screen_name='bobby').fetch()
        self.assertFalse(result[0]['success'])
        self.assertIn('Account has no API credentials',
                                                    result[0]['messages'][0])

    @responses.activate
    def test_saves_tweets(self):
        self.add_response(body=self.make_response_body())
        result = FavoriteTweetsFetcher(screen_name='jill').fetch()
        self.assertEqual(Tweet.objects.count(), 3)
        # Our sample tweets are from a different user, so there'll now be 3:
        self.assertEqual(User.objects.count(), 3)

    @responses.activate
    @patch.object(TweetSaver, 'save_tweet')
    def test_saves_correct_tweet_data(self, save_tweet):
        """Assert save_tweet is called once per tweet.
        Not actually checking what's passed in."""
        save_tweet.side_effect = [TweetFactory(),TweetFactory(),TweetFactory()]
        self.add_response(body=self.make_response_body())
        result = FavoriteTweetsFetcher(screen_name='jill').fetch()
        self.assertEqual(save_tweet.call_count, 3)

    @responses.activate
    def test_associates_users_with_favorites(self):
        self.add_response(body=self.make_response_body())
        result = FavoriteTweetsFetcher(screen_name='jill').fetch()
        jill = User.objects.get(screen_name='jill')
        jills_faves = jill.favorites.all()
        self.assertEqual(len(jills_faves), 3)
        self.assertIsInstance(jills_faves[0], Tweet)
        self.assertEqual(jills_faves[0].twitter_id, 300)

    @responses.activate
    @patch.object(filedownloader, 'download')
    def test_fetches_multiple_pages_for_new(self, download):
        """Fetches subsequent pages until no results are returned."""
        # This will just stop us requesting avatars from Twitter:
        download.side_effect = DownloadException('Ooops')
        self.account_1.last_favorite_id = 10
        self.account_1.save()
        qs = {'user_id': self.account_1.user.twitter_id,
                                                'count': 200, 'since_id': 10}
        self.add_response(body=self.make_response_body(),
                            querystring=qs, match_querystring=True)
        qs['max_id'] = 99
        self.add_response(body='[]', querystring=qs, match_querystring=True)
        with patch('time.sleep'):
            result = FavoriteTweetsFetcher(screen_name='jill').fetch()
            self.assertEqual(2, len(responses.calls))

    @responses.activate
    def test_fetches_multiple_pages_for_count(self):
        "Fetches subsequent pages until enough counted tweets are returned."
        qs = {'user_id': self.account_1.user.twitter_id, 'count': 200}
        # Return "[{id:1}, {id:1}, {id:1}...]" and patch _save_results() as
        # we're only interested in how many times we ask for more results.
        body = json.dumps([{'id':1} for x in range(200)])

        # We're going to request 3 x 200 Tweets and then...
        for n in range(3):
            self.add_response(body=body, querystring=qs, match_querystring=True)
        # ... 1 x 100 Tweets = 700 Tweets.
        qs['count'] = 100
        self.add_response(body=body, querystring=qs, match_querystring=True)

        with patch.object(FetchTweetsFavorite, '_save_results'):
            with patch('time.sleep'):
                result = FavoriteTweetsFetcher(screen_name='jill').fetch(
                                                                    count=700)
                self.assertEqual(4, len(responses.calls))


class UsersFetcherTestCase(TwitterFetcherTestCase):

    api_fixture = 'users_lookup.json'

    api_call = 'users/lookup'

    @responses.activate
    @patch.object(UserSaver, '_fetch_and_save_avatar')
    def test_makes_one_api_call(self, fetch_avatar):
        self.add_response(body=self.make_response_body())
        result = UsersFetcher(screen_name='jill').fetch(
                                                [460060168, 26727655, 6795192])
        self.assertEqual(1, len(responses.calls))

    @responses.activate
    def test_makes_correct_api_call(self):
        self.add_response(body=self.make_response_body())
        result = UsersFetcher(screen_name='jill').fetch([460060168, 26727655, 6795192])
        self.assertIn('users/lookup.json?', responses.calls[0][0].url)
        self.assertIn('include_entities=true', responses.calls[0][0].url)
        self.assertIn('user_id=460060168%2C26727655%2C6795192',
                                                    responses.calls[0][0].url)

    @responses.activate
    def test_returns_correct_success_response(self):
        self.add_response(body=self.make_response_body())
        result = UsersFetcher(screen_name='jill').fetch([460060168, 26727655, 6795192])
        self.assertEqual(result[0]['account'], 'jill')
        self.assertTrue(result[0]['success'])
        self.assertEqual(result[0]['fetched'], 3)

    @responses.activate
    def test_returns_error_if_api_call_fails(self):
        self.add_response(body='{"errors":[{"message":"Rate limit exceeded","code":88}]}', status=429)
        result = UsersFetcher(screen_name='jill').fetch([460060168, 26727655, 6795192])
        self.assertFalse(result[0]['success'])
        self.assertIn('Rate limit exceeded', result[0]['messages'][0])

    @responses.activate
    def test_requests_all_users(self):
        "If no ids supplied, uses all users in the DB"
        users = UserFactory.create_batch(5)
        result = UsersFetcher(screen_name='jill').fetch()

        ids = User.objects.values_list('twitter_id', flat=True).order_by('fetch_time')
        ids = '%2C'.join(map(str, ids))
        self.assertIn(ids, responses.calls[0][0].url)

    @responses.activate
    def test_creates_users(self):
        self.add_response(body=self.make_response_body())
        result = UsersFetcher(screen_name='jill').fetch([460060168, 26727655, 6795192])
        self.assertEqual(1, User.objects.filter(twitter_id=460060168).count())
        self.assertEqual(1, User.objects.filter(twitter_id=26727655).count())
        self.assertEqual(1, User.objects.filter(twitter_id=6795192).count())

    @responses.activate
    def test_updates_users(self):
        user = UserFactory.create(
                                    twitter_id=26727655, screen_name='bill')
        self.add_response(body=self.make_response_body())
        result = UsersFetcher(screen_name='jill').fetch([460060168, 26727655, 6795192])
        self.assertEqual('Aiannucci',
                            User.objects.get(twitter_id=26727655).screen_name)

    @responses.activate
    def test_fetches_multiple_pages(self):
        # We're going to ask for 350 user IDs, which will be split over 4 pages.
        ids = [id for id in range(1,351)]
        body = json.dumps([{'id':id} for id in range(1,100)])

        for n in range(3):
            # First time, add ids 1-100. Then 101-200. Then 201-300.
            start = n * 100
            end = (n+1) * 100
            qs = {
                'user_id': '%2C'.join(map(str, ids[start:end])),
                'include_entities': 'true'}
            self.add_response(body=body, querystring=qs, match_querystring=True)
        # Then add the final 301-350 ids.
        qs['user_id'] = '%2C'.join(map(str, ids[-50:]))
        self.add_response(body=body, querystring=qs, match_querystring=True)

        with patch.object(FetchUsers, '_save_results'):
            with patch('time.sleep'):
                result = UsersFetcher(screen_name='jill').fetch(ids)
                self.assertEqual(4, len(responses.calls))


class TweetsFetcherTestCase(TwitterFetcherTestCase):

    api_fixture = 'tweets.json'

    api_call = 'statuses/lookup'

    @responses.activate
    @patch.object(filedownloader, 'download')
    def test_makes_one_api_call(self, download):
        # This will just stop us requesting avatars from Twitter:
        download.side_effect = DownloadException('Ooops')
        self.add_response(body=self.make_response_body(), method='POST')
        result = TweetsFetcher(screen_name='jill').fetch([300, 200, 100])
        self.assertEqual(1, len(responses.calls))

    @responses.activate
    def test_makes_correct_api_call(self):
        self.add_response(body=self.make_response_body(), method='POST')
        result = TweetsFetcher(screen_name='jill').fetch([300, 200, 100])
        self.assertIn('statuses/lookup.json', responses.calls[0][0].url)

        # To get the POST params:
        params = QueryDict(responses.calls[0][0].body)

        self.assertIn('include_entities', params)
        self.assertEqual(params['include_entities'], 'true')
        self.assertIn('trim_user', params)
        self.assertEqual(params['trim_user'], 'false')
        self.assertIn('map', params)
        self.assertEqual(params['map'], 'false')
        self.assertIn('id', params)
        self.assertEqual(params['id'], '300,200,100')

    @responses.activate
    def test_returns_correct_success_response(self):
        self.add_response(body=self.make_response_body(), method='POST')
        result = TweetsFetcher(screen_name='jill').fetch([300,200,100])
        self.assertEqual(result[0]['account'], 'jill')
        self.assertTrue(result[0]['success'])
        self.assertEqual(result[0]['fetched'], 3)

    @responses.activate
    def test_returns_error_if_api_call_fails(self):
        self.add_response(body='{"errors":[{"message":"Rate limit exceeded","code":88}]}', status=429, method='POST')
        result = TweetsFetcher(screen_name='jill').fetch([300,200,100])
        self.assertFalse(result[0]['success'])
        self.assertIn('Rate limit exceeded', result[0]['messages'][0])

    @responses.activate
    def test_requests_all_tweets(self):
        "If no ids supplied, uses all tweets in the DB"
        tweets = TweetFactory.create_batch(5)
        result = TweetsFetcher(screen_name='jill').fetch()

        ids = Tweet.objects.values_list('twitter_id', flat=True).order_by('fetch_time')

        params = QueryDict(responses.calls[0][0].body)
        self.assertIn('id', params)
        self.assertEqual(','.join(map(str, ids)), params['id'])

    @responses.activate
    def test_creates_tweets(self):
        self.add_response(body=self.make_response_body(), method='POST')
        result = TweetsFetcher(screen_name='jill').fetch([300,200,100])
        self.assertEqual(1, Tweet.objects.filter(twitter_id=300).count())
        self.assertEqual(1, Tweet.objects.filter(twitter_id=200).count())
        self.assertEqual(1, Tweet.objects.filter(twitter_id=100).count())

    @responses.activate
    def test_updates_tweets(self):
        tweets = TweetFactory.create(twitter_id=200, text='Will change')
        self.add_response(body=self.make_response_body(), method='POST')
        result = TweetsFetcher(screen_name='jill').fetch([300,200,100])
        self.assertEqual(Tweet.objects.get(twitter_id=200).text,
            "@rooreynolds I've read stories of people travelling abroad who were mistaken for military/security because of that kind of thing… careful :)")

    @responses.activate
    def test_fetches_multiple_pages(self):
        """
        The mocked requests work without specifying the data we're POSTing,
        so... not doing anything with it.
        """
        # We're going to ask for 350 tweet IDs which will be split over 4 pages.
        ids = [id for id in range(1,351)]
        body = json.dumps([{'id':id} for id in range(1,100)])

        for n in range(3):
            # First time, add ids 1-100. Then 101-200. Then 201-300.
            start = n * 100
            end = (n+1) * 100
            #qs = {
                #'id': ','.join(map(str, ids[start:end])),
                #'include_entities': 'true',
                #'trim_user': 'false',
                #'map': 'false'}
            self.add_response(body=body, method='POST')
        # Then add the final 301-350 ids.
        #qs['id'] = ','.join(map(str, ids[-50:]))
        self.add_response(body=body, method='POST')

        with patch.object(FetchTweets, '_save_results'):
            with patch('time.sleep'):
                result = TweetsFetcher(screen_name='jill').fetch(ids)
                self.assertEqual(4, len(responses.calls))


class VerifyFetcherTestCase(TwitterFetcherTestCase):

    api_fixture = 'verify_credentials.json'

    api_call = 'account/verify_credentials'

    @responses.activate
    @patch.object(UserSaver, '_fetch_and_save_avatar')
    def test_api_request_for_one_account(self, fetch_avatar):
        self.add_response(body=self.make_response_body())
        result = VerifyFetcher(screen_name='jill').fetch()
        self.assertEqual(1, len(responses.calls))

    @responses.activate
    @patch.object(UserSaver, '_fetch_and_save_avatar')
    def test_api_requests_for_all_accounts(self, fetch_avatar):
        self.add_response(body=self.make_response_body())
        result = VerifyFetcher().fetch()
        self.assertEqual(2, len(responses.calls))

    @responses.activate
    @patch.object(UserSaver, '_fetch_and_save_avatar')
    def test_ignores_account_with_no_creds(self, fetch_avatar):
        user_3 = UserFactory()
        account_3 = AccountFactory(user=user_3)
        self.add_response(body=self.make_response_body())
        result = VerifyFetcher().fetch()
        self.assertEqual(2, len(responses.calls))

    @responses.activate
    def test_returns_correct_success_response(self):
        "Data returned is correct"
        self.add_response(body=self.make_response_body())
        result = VerifyFetcher().fetch()
        self.assertEqual(len(result), 2)
        self.assertTrue(result[1]['account'], 'jill')
        self.assertTrue(result[1]['success'])

    @responses.activate
    def test_returns_error_if_api_call_fails(self):
        self.add_response(body='{"errors":[{"message":"Rate limit exceeded","code":88}]}',
                            status=429)
        result = VerifyFetcher(screen_name='jill').fetch()
        self.assertFalse(result[0]['success'])
        self.assertIn('Rate limit exceeded', result[0]['messages'][0])

    @responses.activate
    def test_returns_error_if_no_creds(self):
        "If an account has no API credentials, the result is correct"
        user = UserFactory(screen_name='bobby')
        account = AccountFactory(user=user)
        self.add_response(body=self.make_response_body())
        result = VerifyFetcher(screen_name='bobby').fetch()
        self.assertFalse(result[0]['success'])
        self.assertIn('Account has no API credentials',
                                                    result[0]['messages'][0])

    @responses.activate
    def test_saves_users(self):
        "Updates the Account's user data in the DB with fetched data."
        user = UserFactory(twitter_id=12552,
                        screen_name='philgyford', name='This should change')
        account = AccountWithCredentialsFactory(id=4, user=user)

        self.add_response(body=self.make_response_body())
        result = VerifyFetcher(screen_name='philgyford').fetch()

        user_reloaded = User.objects.get(screen_name='philgyford')
        self.assertEqual(user_reloaded.name, 'Phil Gyford')


class FetchVerifyTestCase(FetchTwitterTestCase):

    api_fixture = 'verify_credentials.json'

    api_call = 'account/verify_credentials'

    @responses.activate
    @patch.object(UserSaver, '_fetch_and_save_avatar')
    def test_fetch_for_account_creates(self, fetch_avatar):
        "Saves and returns new user after successful API call"
        # Just make the mocked method return the User that's passed in:
        fetch_avatar.side_effect = lambda value: value

        self.add_response(body=self.make_response_body())
        account = AccountWithCredentialsFactory.build(id=4, user=None)

        result = FetchVerify(account=account).fetch()
        new_user = User.objects.get(twitter_id=12552)

        self.assertEqual(result['account'], 'Account: 4')
        self.assertIsInstance(result['user'], User)
        self.assertEqual(result['user'].screen_name, 'philgyford')
        self.assertEqual(new_user.screen_name, 'philgyford')
        self.assertEqual(1, len(responses.calls))
        self.assertEqual(
                '%s/%s.json' % (self.api_url, 'account/verify_credentials'),
                responses.calls[0].request.url)

    @responses.activate
    @patch.object(UserSaver, '_fetch_and_save_avatar')
    def test_fetch_for_account_updates(self, fetch_avatar):
        "Saves and returns updated existing user after successful API call"
        # Just make the mocked method return the User that's passed in:
        fetch_avatar.side_effect = lambda value: value

        self.add_response(body=self.make_response_body())
        user = UserFactory(twitter_id=12552, screen_name='bob')
        account = AccountWithCredentialsFactory(user=user)

        result = FetchVerify(account=account).fetch()
        updated_user = User.objects.get(twitter_id=12552)

        self.assertEqual(result['account'], 'bob')
        self.assertIsInstance(result['user'], User)
        self.assertEqual(result['user'].screen_name, 'philgyford')
        self.assertEqual(updated_user.screen_name, 'philgyford')
        self.assertEqual(1, len(responses.calls))
        self.assertEqual(
                '%s/%s.json' % (self.api_url, 'account/verify_credentials'),
                responses.calls[0].request.url)

    @responses.activate
    def test_fetch_for_account_fails(self):
        "Returns error message if API call fails"
        self.add_response(
            body='{"errors":[{"message":"Could not authenticate you","code":32}]}',
            status=401)

        account = AccountWithCredentialsFactory.build(user=None)
        result = FetchVerify(account=account).fetch()

        self.assertEqual(result['account'], 'Unsaved Account')
        self.assertEqual(1, len(responses.calls))
        self.assertEqual(
                '%s/%s.json' % (self.api_url, 'account/verify_credentials'),
                responses.calls[0].request.url)
        self.assertTrue('Could not authenticate you' in result['messages'][0])


class FilesFetcherTestCase(TestCase):

    def setUp(self):
        self.fetched_image = PhotoFactory(twitter_id=99999999,
                                                image_file='downloaded.jpg')
        self.image = PhotoFactory(twitter_id=88888888, image_file='',
            image_url='https://pbs.twimg.com/media/abcdefghijklmno.png')

        self.animated_gif = AnimatedGifFactory(
            twitter_id=77777777,
            image_url='https://pbs.twimg.com/tweet_video_thumb/1234567890abcde.png',
            mp4_url='https://pbs.twimg.com/tweet_video/abcde1234567890.mp4',
            image_file='', mp4_file='')

        self.video = VideoFactory(twitter_id=66666666,
            image_url='https://pbs.twimg.com/ext_tw_video_thumb/740282905369444352/pu/img/zyxwvutsrqponml.jpg',
            image_file='', mp4_file='')

    @patch.object(FetchFiles, 'fetch')
    def test_calls_fetch_files(self, fetch):
        results = FilesFetcher().fetch()
        fetch.assert_has_calls([ call(fetch_all=False) ])

    @patch.object(FetchFiles, 'fetch')
    def test_calls_fetch_files_with_all(self, fetch):
        results = FilesFetcher().fetch(fetch_all=True)
        fetch.assert_has_calls([ call(fetch_all=True) ])

    @patch.object(FetchFiles, '_fetch_and_save_file')
    def test_calls_fetch_and_save_missing(self, fetch_and_save_file):
        "Goes to fetch for media without files already."
        results = FilesFetcher().fetch()
        calls = [
                    call(media_obj=self.image, media_type='image'),
                    call(media_obj=self.animated_gif, media_type='image'),
                    call(media_obj=self.animated_gif, media_type='mp4'),
                    call(media_obj=self.video, media_type='image'),
                ]
        fetch_and_save_file.assert_has_calls(calls)

    @patch.object(FetchFiles, '_fetch_and_save_file')
    def test_calls_fetch_and_save_all(self, fetch_and_save_file):
        "Goes to fetch for ALL media."
        results = FilesFetcher().fetch(fetch_all=True)
        calls = [
                    call(media_obj=self.fetched_image, media_type='image'),
                    call(media_obj=self.image, media_type='image'),
                    call(media_obj=self.animated_gif, media_type='image'),
                    call(media_obj=self.animated_gif, media_type='mp4'),
                    call(media_obj=self.video, media_type='image'),
                ]
        fetch_and_save_file.assert_has_calls(calls)

    @patch.object(FetchFiles, '_fetch_and_save_file')
    def test_results_for_fetch_missing(self, fetch_and_save_file):
        results = FilesFetcher().fetch()
        self.assertEqual(len(results), 1)
        self.assertTrue(results[0]['success'])
        # Three images and one MP4 file:
        self.assertEqual(results[0]['fetched'], 4)

    @patch.object(FetchFiles, '_fetch_and_save_file')
    def test_results_for_fetch_all(self, fetch_and_save_file):
        results = FilesFetcher().fetch(fetch_all=True)
        self.assertEqual(len(results), 1)
        self.assertTrue(results[0]['success'])
        self.assertEqual(results[0]['fetched'], 5)

    @patch.object(FetchFiles, '_fetch_and_save_file')
    def test_error_results(self, fetch_and_save_file):
        "Sets the correct error values if things go wrong."
        fetch_and_save_file.side_effect = FetchError('Oh dear')
        results = FilesFetcher().fetch()
        self.assertFalse(results[0]['success'])
        self.assertEqual(results[0]['fetched'], 0)
        self.assertEqual(len(results[0]['messages']), 4)
        self.assertEqual(results[0]['messages'][0], 'Oh dear')

    @patch.object(filedownloader, 'download')
    def test_downloads_image(self, download):
        "Calls the download method correctly for images."
        download.return_value = False
        FetchFiles()._fetch_and_save_file(
                                    media_obj=self.image, media_type='image')
        download.assert_has_calls( [ call(
                    self.image.image_url,
                    ['image/jpeg', 'image/jpg', 'image/png', 'image/gif',]
                ) ] )

    @patch.object(filedownloader, 'download')
    def test_downloads_video(self, download):
        "Calls the download method correctly for GIFs' videos."
        download.return_value = False
        FetchFiles()._fetch_and_save_file(
                            media_obj=self.animated_gif, media_type='mp4')
        download.assert_has_calls( [ call(
                    self.animated_gif.mp4_url,
                    ['video/mp4',]
                ) ] )

    def test_raises_error_with_invalid_media_type(self):
        with self.assertRaises(FetchError):
            FetchFiles()._fetch_and_save_file(self.image, 'bibbly boo')

    @patch.object(filedownloader, 'download')
    def test_raises_error_if_download_fails(self, download):
        "If download() raises an error, so does _fetch_and_save_file()"
        download.side_effect = DownloadException("Ooops")
        with self.assertRaises(FetchError):
            FetchFiles()._fetch_and_save_file(self.image, 'image')

    @override_settings(MEDIA_ROOT=tempfile.gettempdir())
    @patch.object(filedownloader, 'download')
    def test_saves_downloaded_image_file(self, download):
        # Make a temporary file, like download() would make:
        jpg = tempfile.NamedTemporaryFile()
        temp_filepath = jpg.name
        download.return_value = temp_filepath

        FetchFiles()._fetch_and_save_file(self.image, 'image')
        self.assertEqual(
            self.image.image_file.name,
            'twitter/media/%s/%s/%s' % (
                temp_filepath[-4:-2],
                temp_filepath[-2:],
                os.path.basename(temp_filepath)
            )
        )

    @override_settings(MEDIA_ROOT=tempfile.gettempdir())
    @patch.object(filedownloader, 'download')
    def test_saves_downloaded_mp4_file(self, download):
        # Make a temporary file, like download() would make:
        mp4 = tempfile.NamedTemporaryFile()
        temp_filepath = mp4.name
        download.return_value = temp_filepath

        FetchFiles()._fetch_and_save_file(self.animated_gif, 'mp4')
        self.assertEqual(
            self.animated_gif.mp4_file.name,
            'twitter/media/%s/%s/%s' % (
                temp_filepath[-4:-2],
                temp_filepath[-2:],
                os.path.basename(temp_filepath)
            )
        )

