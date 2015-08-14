# coding: utf-8
import datetime
import json

import pytz
import responses

from django.db import IntegrityError
from django.test import TestCase

from .. import factories
from ..managers import UserManager
from ..models import Account, Tweet, User


class TwitterAccountTestCase(TestCase):

    api_url = 'https://api.twitter.com/1.1'

    api_fixture = 'ditto/twitter/fixtures/api/verify_credentials.json'

    def make_verify_credentials_body(self):
        "Makes the JSON response to a call to verify_credentials"
        json_file = open(self.api_fixture)
        json_data = json_file.read()
        json_file.close()
        return json_data

    def add_response(self, body, call, status=200):
        """Add a Twitter API response.

        Keyword arguments:
        body -- The JSON string representing the body of the response.
        call -- String, appended to self.api_url, eg
                    'account/verfiy_credentials'.
        status -- Int, HTTP response status
        """
        responses.add(
            responses.GET,
            '%s/%s.json' % (self.api_url, call),
            status=status,
            match_querystring=False,
            body=body,
            content_type='application/json; charset=utf-8'
        )

    def test_str_1(self):
        "Has the correct string represntation when it has no user"
        account = factories.AccountFactory(user=None)
        self.assertEqual(account.__str__(), '%d' % account.pk)

    def test_str_2(self):
        "Has the correct string represntation when it has a user"
        user = factories.UserFactory()
        account = factories.AccountFactory(user=user)
        self.assertEqual(account.__str__(), user.screen_name)

    def test_ordering(self):
        """Multiple accounts are by creation time descending"""
        account_1 = factories.AccountFactory()
        account_2 = factories.AccountFactory()
        accounts = Account.objects.all()
        self.assertEqual(accounts[0].pk, account_2.pk)

    @responses.activate
    def test_creates_user(self):
        "Should fetch user from API on save if it has no user"
        self.add_response(body=self.make_verify_credentials_body(),
                            call='account/verify_credentials')
        account = factories.AccountWithCredentialsFactory(user=None)
        self.assertIsInstance(account.user, User)
        self.assertEqual(account.user.screen_name, 'philgyford')
        self.assertEqual(1, len(responses.calls))
        self.assertEqual(
                '%s/%s.json' % (self.api_url, 'account/verify_credentials'),
                responses.calls[0].request.url)

    @responses.activate
    def test_does_not_update_user(self):
        "Shouldn't fetch user from API on save if it already has a user"
        self.add_response(body=self.make_verify_credentials_body(),
                            call='account/verify_credentials')
        user = factories.UserFactory(twitter_id=12552, screen_name='oldname')
        account = factories.AccountWithCredentialsFactory(user=user)
        self.assertIsInstance(account.user, User)
        # Screen name is not changed to the one in our mocked API response:
        self.assertEqual(account.user.screen_name, 'oldname')
        self.assertEqual(0, len(responses.calls))

    @responses.activate
    def test_update_user_does_nothing_with_no_credentials(self):
        "Doesn't verify_credentials if Account has none"
        self.add_response(body=self.make_verify_credentials_body(),
                            call='account/verify_credentials')
        # Not saving (as that generates another request):
        account = factories.AccountFactory.build(user=None)
        result = account.updateUserFromTwitter()
        self.assertEqual(result, False)
        self.assertEqual(0, len(responses.calls))

    @responses.activate
    def test_update_user_updates_user(self):
        "Sets the Account's user and returns it if all is well."
        self.add_response(body=self.make_verify_credentials_body(),
                            call='account/verify_credentials')
        # Not saving (as that generates another request):
        account = factories.AccountWithCredentialsFactory.build(user=None)

        result = account.updateUserFromTwitter()
        self.assertIsInstance(result, User)
        self.assertIsInstance(account.user, User)
        self.assertEqual(account.user.screen_name, 'philgyford')
        self.assertEqual(1, len(responses.calls))
        self.assertEqual(
                '%s/%s.json' % (self.api_url, 'account/verify_credentials'),
                responses.calls[0].request.url)

    @responses.activate
    def test_update_user_returns_error_message(self):
        "Returns an error message if there's an API error."
        self.add_response(body='{"errors":[{"message":"Could not authenticate you","code":32}]}',
                            call='account/verify_credentials',
                            status=401)
        # Not saving (as that generates another request):
        account = factories.AccountWithCredentialsFactory.build(user=None)

        result = account.updateUserFromTwitter()
        self.assertEqual(1, len(responses.calls))
        self.assertEqual(
                '%s/%s.json' % (self.api_url, 'account/verify_credentials'),
                responses.calls[0].request.url)
        self.assertTrue('Could not authenticate you' in result)

    def test_has_credentials_true(self):
        self.add_response(body=self.make_verify_credentials_body(),
                            call='account/verify_credentials')
        account = factories.AccountWithCredentialsFactory.build(user=None)
        self.assertTrue(account.hasCredentials())

    def test_has_credentials_false(self):
        account = factories.AccountFactory.build(user=None)
        self.assertFalse(account.hasCredentials())


class TwitterTweetTestCase(TestCase):

    def test_str(self):
        "Has the correct string represntation"
        tweet = factories.TweetFactory(title='My tweet text')
        self.assertEqual(tweet.__str__(), 'My tweet text')

    def test_ordering(self):
        """Multiple accounts are sorted by created_at descending"""
        time_now = datetime.datetime.utcnow().replace(tzinfo=pytz.utc)
        tweet_1 = factories.TweetFactory(
                        created_at=time_now - datetime.timedelta(minutes=1))
        tweet_2 = factories.TweetFactory(created_at=time_now)
        tweets = Tweet.objects.all()
        self.assertEqual(tweets[0].pk, tweet_2.pk)

    def test_unique_twitter_id(self):
        "Ensures twitter_id is unique"
        tweet_1 = factories.TweetFactory(twitter_id=123)
        with self.assertRaises(IntegrityError):
            tweet_2 = factories.TweetFactory(twitter_id=123)

    def test_summary_creation(self):
        "Creates the Tweet's summary correctly on save"
        tweet = factories.TweetFactory(text='This is my tweet text')
        self.assertEqual(tweet.summary, 'This is my tweet text')

    def test_default_manager(self):
        "The default manager includes tweets from public AND private users"
        public_user = factories.UserFactory(is_private=False)
        private_user = factories.UserFactory(is_private=True)
        public_tweet_1 = factories.TweetFactory(user=public_user)
        private_tweet = factories.TweetFactory(user=private_user)
        public_tweet_2 = factories.TweetFactory(user=public_user)
        self.assertEqual(len(Tweet.objects.all()), 3)

    def test_public_manager(self):
        "The public manager ONLY includes tweets from public users"
        public_user = factories.UserFactory(is_private=False)
        private_user = factories.UserFactory(is_private=True)
        public_tweet_1 = factories.TweetFactory(user=public_user)
        private_tweet = factories.TweetFactory(user=private_user)
        public_tweet_2 = factories.TweetFactory(user=public_user)
        tweets = Tweet.public_objects.all()
        self.assertEqual(len(tweets), 2)
        self.assertEqual(tweets[0].pk, public_tweet_2.pk)
        self.assertEqual(tweets[1].pk, public_tweet_1.pk)

    def test_is_public(self):
        "Tweet should be public if tweet's user is public"
        user = factories.UserFactory(is_private=False)
        tweet = factories.TweetFactory(user=user)
        self.assertFalse(tweet.is_private)

    def test_is_private(self):
        "Tweet should be private if tweet's user is private"
        user = factories.UserFactory(is_private=True)
        tweet = factories.TweetFactory(user=user)
        self.assertTrue(tweet.is_private)


class TwitterUserTestCase(TestCase):

    def test_str(self):
        "Has the correct string represntation"
        user = factories.UserFactory(screen_name='bill')
        self.assertEqual(user.__str__(), 'bill')

    def test_ordering(self):
        """Multiple users are sorted by screen_name"""
        user_1 = factories.UserFactory(screen_name='bill')
        user_2 = factories.UserFactory(screen_name='alice')
        users = User.objects.all()
        self.assertEqual(users[0].pk, user_2.pk)

    def test_permalink(self):
        "Generates the correct permalink"
        user = factories.UserFactory(screen_name='bill')
        self.assertEqual(user.permalink, 'https://twitter.com/bill')

    def test_unique_twitter_id(self):
        "Ensures twitter_id is unique"
        user_1 = factories.UserFactory(twitter_id=123)
        with self.assertRaises(IntegrityError):
            user_2 = factories.UserFactory(twitter_id=123)

    def test_going_private(self):
        "Makes the user's tweets private if they go private"
        # Start off public:
        user = factories.UserFactory(is_private=False)
        tweet = factories.TweetFactory(user=user)
        self.assertFalse(tweet.is_private)
        # Now change to private:
        user.is_private = True
        # Should change the user's tweets to private:
        user.save()
        tweet.refresh_from_db()
        self.assertTrue(tweet.is_private)

    def test_going_public(self):
        "Makes the user's tweets public if they go public"
        # Start off private:
        user = factories.UserFactory(is_private=True)
        tweet = factories.TweetFactory(user=user)
        self.assertTrue(tweet.is_private)
        # Now change to public:
        user.is_private = False
        # Should change the user's tweets to public:
        user.save()
        tweet.refresh_from_db()
        self.assertFalse(tweet.is_private)
