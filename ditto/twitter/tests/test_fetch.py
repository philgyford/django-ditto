# coding: utf-8
import datetime
from decimal import Decimal
import json
from mock import call, patch

import pytz
import responses
from freezegun import freeze_time

from django.test import TestCase

from .. import factories
from ..fetch import FavoriteTweetsFetcher, FetchError, TweetMixin, TwitterFetcher, RecentTweetsFetcher, UserMixin, VerifyFetcher, VerifyForAccount
from ..models import Account, Tweet, User


class FetchTwitterTestCase(TestCase):
    """Parent class with commomn things."""

    api_url = 'https://api.twitter.com/1.1'

    # Should be set in child classes to use self.make_response_body():
    # eg 'account/verify_credentials'
    api_call = ''

    # Should be set in child classes to use self.make_response_body():
    # eg, 'ditto/twitter/fixtures/api/tweets.json'
    api_fixture = ''

    def make_response_body(self):
        "Makes the JSON response to a call to the API"
        json_file = open(self.api_fixture)
        json_data = json_file.read()
        json_file.close()
        return json_data

    def add_response(self, body, status=200):
        """Add a Twitter API response.

        Keyword arguments:
        body -- The JSON string representing the body of the response.
        status -- Int, HTTP response status
        """
        responses.add(
            responses.GET,
            '%s/%s.json' % (self.api_url, self.api_call),
            status=status,
            match_querystring=False,
            body=body,
            content_type='application/json; charset=utf-8'
        )


class TweetMixinTestCase(FetchTwitterTestCase):
    """Testing the TweetMixin"""

    api_fixture = 'ditto/twitter/fixtures/api/tweets.json'

    @freeze_time("2015-08-14 12:00:00", tz_offset=-8)
    def test_saves_correct_tweet_data(self):

        fetch_time = datetime.datetime.utcnow().replace(tzinfo=pytz.utc)

        # Get the JSON for a single tweet.
        tweets_data = json.loads(self.make_response_body())
        tweet_data = tweets_data[0]

        # A bit horrid; need to rely on UserMixin working so we can make a
        # User object correctly, so we can then make the tweet:
        user_mixin = UserMixin()
        user = user_mixin.save_user(tweet_data['user'], fetch_time)

        # Send the JSON, and our new User object, to try and save the tweet:
        mixin = TweetMixin()
        saved_tweet = mixin.save_tweet(tweet_data, fetch_time, user)

        # Load that saved tweet from the DB:
        tweet = Tweet.objects.get(twitter_id=629377146222419968)

        #And check it's all there:
        self.assertEqual(tweet.title, "@flaneur ooh, very exciting, thank you!  Both my ears owe you a drink.")
        self.assertEqual(tweet.summary, "@flaneur ooh, very exciting, thank you! Both my ears owe you a drink.")
        self.assertEqual(tweet.text, "@flaneur ooh, very exciting, thank you!\n\nBoth my ears owe you a drink.")
        self.assertEqual(tweet.latitude, Decimal('40.05701649'))
        self.assertEqual(tweet.longitude, Decimal('-75.14310264'))
        self.assertFalse(tweet.is_private)
        self.assertEqual(tweet.fetch_time, fetch_time)
        self.assertEqual(tweet.permalink,
                    'https://twitter.com/philgyford/status/629377146222419968')

        tweets = json.loads(self.make_response_body())
        self.assertEqual(tweet.raw, json.dumps(tweets[0]))

        self.assertEqual(tweet.user.screen_name, 'philgyford')
        self.assertEqual(tweet.twitter_id, 629377146222419968)
        self.assertEqual(tweet.created_at, datetime.datetime.strptime(
                                    '2015-08-06 19:42:59', '%Y-%m-%d %H:%M:%S'
                                ).replace(tzinfo=pytz.utc))
        self.assertEqual(tweet.favorite_count, 2)
        self.assertEqual(tweet.retweet_count, 1)
        self.assertEqual(tweet.in_reply_to_screen_name, 'flaneur')
        self.assertEqual(tweet.in_reply_to_status_id, 629375876216528896)
        self.assertEqual(tweet.in_reply_to_user_id, 1859981)
        self.assertEqual(tweet.language, 'en')
        self.assertEqual(tweet.place_attribute_street_address, '795 Folsom St')
        self.assertEqual(tweet.place_full_name, 'Twitter HQ, San Francisco')
        self.assertEqual(tweet.place_country, 'United States')
        self.assertEqual(tweet.source, u'<a href="http://tapbots.com/tweetbot" rel="nofollow">Tweetbot for iΟS</a>')

    def test_saves_private_tweets_correctly(self):
        """If the user is protected, their tweets should be marked private."""

        fetch_time = datetime.datetime.utcnow().replace(tzinfo=pytz.utc)

        # Get the JSON for a single tweet.
        tweets_data = json.loads(self.make_response_body())
        tweet_data = tweets_data[0]
        tweet_data['user']['protected'] = True

        user_mixin = UserMixin()
        user = user_mixin.save_user(tweet_data['user'], fetch_time)

        mixin = TweetMixin()
        saved_tweet = mixin.save_tweet(tweet_data, fetch_time, user)

        # Load that saved tweet from the DB:
        tweet = Tweet.objects.get(twitter_id=629377146222419968)
        self.assertTrue(tweet.is_private)


class UserMixinTestCase(FetchTwitterTestCase):

    api_fixture = 'ditto/twitter/fixtures/api/verify_credentials.json'

    @freeze_time("2015-08-14 12:00:00", tz_offset=-8)
    def test_saves_correct_user_data(self):

        fetch_time = datetime.datetime.utcnow().replace(tzinfo=pytz.utc)

        # Get the JSON for a single user.
        raw_json = self.make_response_body()
        user_data = json.loads(raw_json)

        user_mixin = UserMixin()
        saved_user = user_mixin.save_user(user_data, fetch_time)

        user = User.objects.get(twitter_id=12552)

        self.assertEqual(user.fetch_time, fetch_time)
        self.assertEqual(user.raw, json.dumps(user_data))
        self.assertEqual(user.screen_name, 'philgyford')
        self.assertEqual(user.url, 'http://t.co/UEs0CCkdrl')
        self.assertFalse(user.is_private)
        self.assertFalse(user.is_verified)
        self.assertEqual(user.created_at, datetime.datetime.strptime(
                                    '2006-11-15 16:55:59', '%Y-%m-%d %H:%M:%S'
                                ).replace(tzinfo=pytz.utc))
        self.assertEqual(user.description, 'Good. Good to Firm in places.')
        self.assertEqual(user.location, 'London, UK')
        self.assertEqual(user.time_zone, 'London')
        self.assertEqual(user.profile_image_url,'http://pbs.twimg.com/profile_images/1167616130/james_200208_300x300_normal.jpg')
        self.assertEqual(user.profile_image_url_https, 'https://pbs.twimg.com/profile_images/1167616130/james_200208_300x300_normal.jpg')
        self.assertEqual(user.favorites_count, 1389)
        self.assertEqual(user.followers_count, 2435)
        self.assertEqual(user.friends_count, 309)
        self.assertEqual(user.listed_count, 138)
        self.assertEqual(user.statuses_count, 16428)

    def test_saves_alternate_data(self):
        """Check some different data to in the main user test."""

        fetch_time = datetime.datetime.utcnow().replace(tzinfo=pytz.utc)

        # Get the JSON for a single user.
        raw_json = self.make_response_body()
        user_data = json.loads(raw_json)

        user_data['protected'] = True
        user_data['verified'] = True

        user_mixin = UserMixin()
        saved_user = user_mixin.save_user(user_data, fetch_time)

        user = User.objects.get(twitter_id=12552)

        self.assertTrue(user.is_private)
        self.assertTrue(user.is_verified)


class TwitterFetcherSetAccountsTestCase(FetchTwitterTestCase):
    """Testing the private _set_accounts() method of the parent TwitterFetcher
    class.
    """

    def setUp(self):
        user_1 = factories.UserFactory(screen_name='jill')
        user_2 = factories.UserFactory(screen_name='debs')
        account_1 = factories.AccountFactory(user=user_1)
        account_2 = factories.AccountFactory(user=user_2)
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

    def test_set_accounts_raises_error(self):
        "It raises FetchError when passed a non-existent screen_name"
        with self.assertRaises(FetchError):
            self.fetcher._set_accounts('percy')


class TwitterFetcherTestCase(FetchTwitterTestCase):
    """Testing the parent TwitterFetcher class."""

    api_fixture = 'ditto/twitter/fixtures/api/tweets.json'

    def setUp(self):
        user_1 = factories.UserFactory(screen_name='jill')
        user_2 = factories.UserFactory(screen_name='debs')
        self.account_1 = factories.AccountWithCredentialsFactory(user=user_1)
        self.account_2 = factories.AccountWithCredentialsFactory(user=user_2)

    def test_raises_error_with_invalid_screen_name(self):
        user = factories.UserFactory(screen_name='goodname')
        account = factories.AccountFactory(user=user)
        with self.assertRaises(FetchError):
            result = RecentTweetsFetcher(screen_name='badname')


class RecentTweetsFetcherTestCase(TwitterFetcherTestCase):
    """Testing the RecentTweetsFetcher class."""

    api_call = 'statuses/user_timeline'

    @responses.activate
    def test_api_request_for_one_account(self):
        self.add_response(body=self.make_response_body())
        result = RecentTweetsFetcher(screen_name='jill').fetch()
        self.assertEqual(1, len(responses.calls))

    @responses.activate
    def test_api_requests_for_all_accounts(self):
        self.add_response(body=self.make_response_body())
        result = RecentTweetsFetcher().fetch()
        self.assertEqual(2, len(responses.calls))

    @responses.activate
    def test_ignores_account_with_no_creds(self):
        user_3 = factories.UserFactory()
        account_3 = factories.AccountFactory(user=user_3)
        self.add_response(body=self.make_response_body())
        result = RecentTweetsFetcher().fetch()
        self.assertEqual(2, len(responses.calls))

    @responses.activate
    def test_includes_last_recent_id_in_response(self):
        "If an account has a last_recent_id, use it in the request"
        self.account_1.last_recent_id = 9876543210
        self.account_1.save()
        self.add_response(body=self.make_response_body())
        result = RecentTweetsFetcher(screen_name='jill').fetch()
        self.assertTrue('since_id=9876543210' in responses.calls[0][0].url)

    @responses.activate
    def test_omits_last_recent_id_from_response(self):
        "If an account has no last_recent_id, it is not used in the request"
        self.add_response(body=self.make_response_body())
        result = RecentTweetsFetcher(screen_name='jill').fetch()
        self.assertFalse('since_id=9876543210' in responses.calls[0][0].url)

    @responses.activate
    def test_updates_last_recent_id(self):
        "The account's last_recent_id should be set to the most recent tweet's"
        self.account_1.last_recent_id = 9876543210
        self.account_1.save()
        self.add_response(body=self.make_response_body())
        result = RecentTweetsFetcher(screen_name='jill').fetch()
        self.account_1.refresh_from_db()
        self.assertEqual(self.account_1.last_recent_id, 629377146222419968)

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
        self.add_response(body='{"errors":[{"message":"Rate limit exceeded","code":88}]}',
                            status=429)
        result = RecentTweetsFetcher(screen_name='jill').fetch()
        self.assertFalse(result[0]['success'])
        self.assertTrue('Rate limit exceeded' in result[0]['message'])

    @responses.activate
    def test_returns_error_if_no_creds(self):
        "If an account has no API credentials, the result is correct"
        user = factories.UserFactory(screen_name='bobby')
        account = factories.AccountFactory(user=user)
        self.add_response(body=self.make_response_body())
        result = RecentTweetsFetcher(screen_name='bobby').fetch()
        self.assertFalse(result[0]['success'])
        self.assertTrue('Account has no API credentials' in result[0]['message'])

    @responses.activate
    def test_saves_tweets(self):
        self.add_response(body=self.make_response_body())
        result = RecentTweetsFetcher(screen_name='jill').fetch()
        self.assertEqual(Tweet.objects.count(), 3)
        # Our sample tweets are from a different user, so there'll now be 3:
        self.assertEqual(User.objects.count(), 3)

    @responses.activate
    @patch('ditto.twitter.fetch.TweetMixin.save_tweet')
    def test_saves_correct_tweet_data(self, save_tweet):
        """Assert save_tweet is called once per tweet.
        Not actually checking what's passed in."""
        save_tweet.side_effect = [factories.TweetFactory(),
                        factories.TweetFactory(), factories.TweetFactory()]
        self.add_response(body=self.make_response_body())
        result = RecentTweetsFetcher(screen_name='jill').fetch()
        self.assertEqual(save_tweet.call_count, 3)


class FavoriteTweetsFetcherTestCase(TwitterFetcherTestCase):
    """Testing the FavoriteTweetsFetcher class."""

    api_call = 'favorites/list'

    @responses.activate
    def test_api_request_for_one_account(self):
        self.add_response(body=self.make_response_body())
        result = FavoriteTweetsFetcher(screen_name='jill').fetch()
        self.assertEqual(1, len(responses.calls))

    @responses.activate
    def test_api_requests_for_all_accounts(self):
        self.add_response(body=self.make_response_body())
        result = FavoriteTweetsFetcher().fetch()
        self.assertEqual(2, len(responses.calls))

    @responses.activate
    def test_ignores_account_with_no_creds(self):
        user_3 = factories.UserFactory()
        account_3 = factories.AccountFactory(user=user_3)
        self.add_response(body=self.make_response_body())
        result = FavoriteTweetsFetcher().fetch()
        self.assertEqual(2, len(responses.calls))

    @responses.activate
    def test_includes_last_favorite_id_in_response(self):
        "If an account has a last_favorite_id, use it in the request"
        self.account_1.last_favorite_id = 9876543210
        self.account_1.save()
        self.add_response(body=self.make_response_body())
        result = FavoriteTweetsFetcher(screen_name='jill').fetch()
        self.assertTrue('since_id=9876543210' in responses.calls[0][0].url)

    @responses.activate
    def test_omits_last_favorite_id_from_response(self):
        "If an account has no last_favorite_id, it is not used in the request"
        self.add_response(body=self.make_response_body())
        result = FavoriteTweetsFetcher(screen_name='jill').fetch()
        self.assertFalse('since_id=9876543210' in responses.calls[0][0].url)

    @responses.activate
    def test_updates_last_favorite_id(self):
        "The account's last_favorite_id should be set to the most recent tweet's"
        self.account_1.last_favorite_id = 9876543210
        self.account_1.save()
        self.add_response(body=self.make_response_body())
        result = FavoriteTweetsFetcher(screen_name='jill').fetch()
        self.account_1.refresh_from_db()
        self.assertEqual(self.account_1.last_favorite_id, 629377146222419968)

    @responses.activate
    def test_returns_correct_success_response(self):
        "Data returned is correct"
        self.add_response(body=self.make_response_body())
        result = FavoriteTweetsFetcher().fetch()
        self.assertEqual(len(result), 2)
        self.assertTrue(result[1]['account'], 'jill')
        self.assertTrue(result[1]['success'])
        self.assertEqual(result[1]['fetched'], 3)

    @responses.activate
    def test_returns_error_if_api_call_fails(self):
        self.add_response(body='{"errors":[{"message":"Rate limit exceeded","code":88}]}',
                            status=429)
        result = FavoriteTweetsFetcher(screen_name='jill').fetch()
        self.assertFalse(result[0]['success'])
        self.assertTrue('Rate limit exceeded' in result[0]['message'])

    @responses.activate
    def test_returns_error_if_no_creds(self):
        "If an account has no API credentials, the result is correct"
        user = factories.UserFactory(screen_name='bobby')
        account = factories.AccountFactory(user=user)
        self.add_response(body=self.make_response_body())
        result = FavoriteTweetsFetcher(screen_name='bobby').fetch()
        self.assertFalse(result[0]['success'])
        self.assertTrue('Account has no API credentials' in result[0]['message'])

    @responses.activate
    def test_saves_tweets(self):
        self.add_response(body=self.make_response_body())
        result = FavoriteTweetsFetcher(screen_name='jill').fetch()
        self.assertEqual(Tweet.objects.count(), 3)
        # Our sample tweets are from a different user, so there'll now be 3:
        self.assertEqual(User.objects.count(), 3)

    @responses.activate
    @patch('ditto.twitter.fetch.UserMixin.save_user')
    @patch('ditto.twitter.fetch.TweetMixin.save_tweet')
    def test_saves_correct_tweet_data(self, save_tweet, save_user):
        """Assert save_tweet is called once per tweet.
        Not actually checking what's passed in."""
        save_tweet.side_effect = [factories.TweetFactory(),
                        factories.TweetFactory(), factories.TweetFactory()]
        self.add_response(body=self.make_response_body())
        result = FavoriteTweetsFetcher(screen_name='jill').fetch()
        self.assertEqual(save_tweet.call_count, 3)
        self.assertEqual(save_user.call_count, 3)

    @responses.activate
    def test_associates_users_with_favorites(self):
        self.add_response(body=self.make_response_body())
        result = FavoriteTweetsFetcher(screen_name='jill').fetch()
        jill = User.objects.get(screen_name='jill')
        jills_faves = jill.favorites.all()
        self.assertEqual(len(jills_faves), 3)
        self.assertIsInstance(jills_faves[0], Tweet)
        self.assertEqual(jills_faves[0].twitter_id, 629377146222419968)


class VerifyFetcherTestCase(TwitterFetcherTestCase):

    api_fixture = 'ditto/twitter/fixtures/api/verify_credentials.json'

    api_call = 'account/verify_credentials'

    @responses.activate
    def test_api_request_for_one_account(self):
        self.add_response(body=self.make_response_body())
        result = VerifyFetcher(screen_name='jill').fetch()
        self.assertEqual(1, len(responses.calls))

    @responses.activate
    def test_api_requests_for_all_accounts(self):
        self.add_response(body=self.make_response_body())
        result = VerifyFetcher().fetch()
        self.assertEqual(2, len(responses.calls))

    @responses.activate
    def test_ignores_account_with_no_creds(self):
        user_3 = factories.UserFactory()
        account_3 = factories.AccountFactory(user=user_3)
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
        self.assertTrue('Rate limit exceeded' in result[0]['message'])

    @responses.activate
    def test_returns_error_if_no_creds(self):
        "If an account has no API credentials, the result is correct"
        user = factories.UserFactory(screen_name='bobby')
        account = factories.AccountFactory(user=user)
        self.add_response(body=self.make_response_body())
        result = VerifyFetcher(screen_name='bobby').fetch()
        self.assertFalse(result[0]['success'])
        self.assertTrue('Account has no API credentials' in result[0]['message'])

    @responses.activate
    def test_saves_users(self):
        "Updates the Account's user data in the DB with fetched data."
        user = factories.UserFactory(twitter_id=12552,
                        screen_name='philgyford', name='This should change')
        account = factories.AccountWithCredentialsFactory(id=4, user=user)

        self.add_response(body=self.make_response_body())
        result = VerifyFetcher(screen_name='philgyford').fetch()

        user_reloaded = User.objects.get(screen_name='philgyford')
        self.assertEqual(user_reloaded.name, 'Phil Gyford')


class VerifyForAccountTestCase(FetchTwitterTestCase):

    api_fixture = 'ditto/twitter/fixtures/api/verify_credentials.json'

    api_call = 'account/verify_credentials'

    @responses.activate
    def test_fetch_for_account_creates(self):
        "Saves and returns new user after successful API call"
        self.add_response(body=self.make_response_body())
        account = factories.AccountWithCredentialsFactory.build(id=4, user=None)

        result = VerifyForAccount(account=account).fetch()
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
    def test_fetch_for_account_updates(self):
        "Saves and returns updated existing user after successful API call"
        self.add_response(body=self.make_response_body())
        user = factories.UserFactory(twitter_id=12552, screen_name='bob')
        account = factories.AccountWithCredentialsFactory(user=user)

        result = VerifyForAccount(account=account).fetch()
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

        account = factories.AccountWithCredentialsFactory.build(user=None)
        result = VerifyForAccount(account=account).fetch()

        self.assertEqual(result['account'], 'Unsaved Account')
        self.assertEqual(1, len(responses.calls))
        self.assertEqual(
                '%s/%s.json' % (self.api_url, 'account/verify_credentials'),
                responses.calls[0].request.url)
        self.assertTrue('Could not authenticate you' in result['message'])

