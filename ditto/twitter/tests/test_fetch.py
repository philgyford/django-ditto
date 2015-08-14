# coding: utf-8
import datetime
from decimal import Decimal
import json

import pytz
import responses
from freezegun import freeze_time

from django.test import TestCase

from .. import factories
from ..fetch import FetchError, FetchTweets, FetchUsers
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


class FetchTwitterTweetsGetAccounts(FetchTwitterTestCase):
    "Testing the private _get_accounts() method"

    def setUp(self):
        user_1 = factories.UserFactory(screen_name='jill')
        user_2 = factories.UserFactory(screen_name='debs')
        account_1 = factories.AccountFactory(user=user_1)
        account_2 = factories.AccountFactory(user=user_2)

    def test_get_accounts_gets_one(self):
        "It gets a single account when passed its screen_name"
        accounts = FetchTweets()._get_accounts('debs')
        self.assertEqual(len(accounts), 1)
        self.assertIsInstance(accounts[0], Account)
        self.assertEqual(accounts[0].user.screen_name, 'debs')

    def test_get_accounts_gets_all(self):
        "It gets all accounts when passed no screen_names"
        accounts = FetchTweets()._get_accounts()
        self.assertEqual(len(accounts), 2)
        self.assertIsInstance(accounts[0], Account)
        self.assertEqual(accounts[0].user.screen_name, 'debs')
        self.assertIsInstance(accounts[1], Account)
        self.assertEqual(accounts[1].user.screen_name, 'jill')

    def test_get_accounts_raises_error(self):
        "It raises FetchError when passed a non-existent screen_name"
        with self.assertRaises(FetchError):
            accounts = FetchTweets()._get_accounts('percy')


class FetchTwitterRecentTweets(FetchTwitterTestCase):

    api_fixture = 'ditto/twitter/fixtures/api/tweets.json'

    api_call = 'statuses/user_timeline'

    def setUp(self):
        user_1 = factories.UserFactory(screen_name='jill')
        user_2 = factories.UserFactory(screen_name='debs')
        self.account_1 = factories.AccountWithCredentialsFactory(user=user_1)
        self.account_2 = factories.AccountWithCredentialsFactory(user=user_2)

    def test_raises_error_with_invalid_screen_name(self):
        user = factories.UserFactory(screen_name='goodname')
        account = factories.AccountFactory(user=user)
        with self.assertRaises(FetchError):
            result = FetchTweets().fetch_recent(screen_name='badname')

    @responses.activate
    def test_api_request_for_one_account(self):
        self.add_response(body=self.make_response_body())
        result = FetchTweets().fetch_recent(screen_name='jill')
        self.assertEqual(1, len(responses.calls))

    @responses.activate
    def test_api_requests_for_all_accounts(self):
        self.add_response(body=self.make_response_body())
        result = FetchTweets().fetch_recent()
        self.assertEqual(2, len(responses.calls))

    @responses.activate
    def test_ignores_account_with_no_creds(self):
        user_3 = factories.UserFactory()
        account_3 = factories.AccountFactory(user=user_3)
        self.add_response(body=self.make_response_body())
        result = FetchTweets().fetch_recent()
        self.assertEqual(2, len(responses.calls))

    @responses.activate
    def test_includes_last_fetch_id(self):
        "If an account has a last_fetch_id, use it in the request"
        self.account_1.last_fetch_id = 9876543210
        self.account_1.save()
        self.add_response(body=self.make_response_body())
        result = FetchTweets().fetch_recent(screen_name='jill')
        self.assertTrue('since_id=9876543210' in responses.calls[0][0].url)

    @responses.activate
    def test_omits_last_fetch_id(self):
        "If an account has no last_fetch_id, it is not used in the request"
        self.add_response(body=self.make_response_body())
        result = FetchTweets().fetch_recent(screen_name='jill')
        self.assertFalse('since_id=9876543210' in responses.calls[0][0].url)

    @responses.activate
    def test_updates_last_fetch_id(self):
        "The account's last_fetch_id should be set to the most recent tweet's"
        self.account_1.last_fetch_id = 9876543210
        self.account_1.save()
        self.add_response(body=self.make_response_body())
        result = FetchTweets().fetch_recent(screen_name='jill')
        self.account_1.refresh_from_db()
        self.assertEqual(self.account_1.last_fetch_id, 629377146222419968)

    @responses.activate
    def test_returns_correct_success_response(self):
        "Data returned is correct"
        self.add_response(body=self.make_response_body())
        result = FetchTweets().fetch_recent()
        self.assertEqual(len(result), 2)
        self.assertTrue(result[1]['account'], 'jill')
        self.assertTrue(result[1]['success'])
        self.assertEqual(result[1]['fetched'], 3)

    @responses.activate
    def test_returns_error_if_api_call_fails(self):
        self.add_response(body='{"errors":[{"message":"Rate limit exceeded","code":88}]}',
                            status=429)
        result = FetchTweets().fetch_recent(screen_name='jill')
        self.assertFalse(result[0]['success'])
        self.assertTrue('Rate limit exceeded' in result[0]['message'])

    @responses.activate
    def test_returns_error_if_no_creds(self):
        "If an account has no API credentials, the result is correct"
        user = factories.UserFactory(screen_name='bobby')
        account = factories.AccountFactory(user=user)
        self.add_response(body=self.make_response_body())
        result = FetchTweets().fetch_recent(screen_name='bobby')
        self.assertFalse(result[0]['success'])
        self.assertTrue('Account has no API credentials' in result[0]['message'])

    @responses.activate
    def test_saves_tweets(self):
        self.add_response(body=self.make_response_body())
        result = FetchTweets().fetch_recent(screen_name='jill')
        self.assertEqual(Tweet.objects.count(), 3)
        # Our sample tweets are from a different user, so there'll now be 3:
        self.assertEqual(User.objects.count(), 3)

    @responses.activate
    @freeze_time("2015-08-14 12:00:00", tz_offset=-8)
    def test_saves_correct_tweet_data(self):
        self.add_response(body=self.make_response_body())
        result = FetchTweets().fetch_recent(screen_name='jill')
        tweet = Tweet.objects.get(twitter_id=629377146222419968)

        self.assertEqual(tweet.title, "@flaneur ooh, very exciting, thank you!  Both my ears owe you a drink.")
        self.assertEqual(tweet.summary, "@flaneur ooh, very exciting, thank you! Both my ears owe you a drink.")
        self.assertEqual(tweet.text, "@flaneur ooh, very exciting, thank you!\n\nBoth my ears owe you a drink.")
        self.assertEqual(tweet.latitude, Decimal('40.05701649'))
        self.assertEqual(tweet.longitude, Decimal('-75.14310264'))
        self.assertEqual(tweet.is_private, False)
        self.assertEqual(tweet.fetch_time,
                        datetime.datetime.utcnow().replace(tzinfo=pytz.utc))
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


class FetchTwitterUsers(FetchTwitterTestCase):

    api_fixture = 'ditto/twitter/fixtures/api/verify_credentials.json'

    api_call = 'account/verify_credentials'

    @responses.activate
    def test_fetch_for_account_creates(self):
        "Saves and returns new user after successful API call"
        self.add_response(body=self.make_response_body())
        account = factories.AccountWithCredentialsFactory.build(id=4, user=None)

        result = FetchUsers().fetch_for_account(account=account)
        new_user = User.objects.get(twitter_id=12552)

        self.assertIsInstance(result, User)
        self.assertEqual(result.screen_name, 'philgyford')
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

        result = FetchUsers().fetch_for_account(account=account)
        updated_user = User.objects.get(twitter_id=12552)

        self.assertIsInstance(result, User)
        self.assertEqual(result.screen_name, 'philgyford')
        self.assertEqual(updated_user.screen_name, 'philgyford')
        self.assertEqual(1, len(responses.calls))
        self.assertEqual(
                '%s/%s.json' % (self.api_url, 'account/verify_credentials'),
                responses.calls[0].request.url)

    @responses.activate
    def test_fetch_for_account_fails(self):
        "Returns error message if API call fails"
        self.add_response(body='{"errors":[{"message":"Could not authenticate you","code":32}]}',
                            status=401)

        account = factories.AccountWithCredentialsFactory.build(user=None)
        result = FetchUsers().fetch_for_account(account=account)

        self.assertEqual(1, len(responses.calls))
        self.assertEqual(
                '%s/%s.json' % (self.api_url, 'account/verify_credentials'),
                responses.calls[0].request.url)
        self.assertTrue('Could not authenticate you' in result)

