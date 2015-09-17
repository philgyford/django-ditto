# coding: utf-8
import datetime
import json

import pytz
import responses

from django.core.urlresolvers import reverse
from django.db import IntegrityError
from django.test import TestCase

from .. import factories
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
        """Multiple accounts are by user.screen_name time ascending"""
        user_1 = factories.UserFactory(screen_name='terry')
        user_2 = factories.UserFactory(screen_name='june')
        account_1 = factories.AccountFactory(user=user_1)
        account_2 = factories.AccountFactory(user=user_2)
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
        self.assertTrue(result['success'])
        self.assertIsInstance(result['user'], User)
        self.assertIsInstance(account.user, User)
        self.assertEqual(account.user.screen_name, 'philgyford')
        self.assertEqual(1, len(responses.calls))
        self.assertEqual(
                '%s/%s.json' % (self.api_url, 'account/verify_credentials'),
                responses.calls[0].request.url)

    @responses.activate
    def test_update_user_returns_error_message(self):
        "Returns an error message if there's an API error."
        self.add_response(
            body='{"errors":[{"message":"Could not authenticate you","code":32}]}',
            call='account/verify_credentials',
            status=401)
        # Not saving (as that generates another request):
        account = factories.AccountWithCredentialsFactory.build(user=None)

        result = account.updateUserFromTwitter()
        self.assertEqual(1, len(responses.calls))
        self.assertEqual(
                '%s/%s.json' % (self.api_url, 'account/verify_credentials'),
                responses.calls[0].request.url)
        self.assertFalse(result['success'])
        self.assertIn('Could not authenticate you', result['message'])

    def test_has_credentials_true(self):
        self.add_response(body=self.make_verify_credentials_body(),
                            call='account/verify_credentials')
        account = factories.AccountWithCredentialsFactory.build(user=None)
        self.assertTrue(account.hasCredentials())

    def test_has_credentials_false(self):
        account = factories.AccountFactory.build(user=None)
        self.assertFalse(account.hasCredentials())

    def test_get_absolute_url_with_user(self):
        user = factories.UserFactory(screen_name='bill')
        account = factories.AccountFactory(user=user)
        self.assertEqual(account.get_absolute_url(),
            reverse('twitter:account_detail', kwargs={'screen_name': 'bill'}))

    def test_get_absolute_url_no_user(self):
        account = factories.AccountFactory(user=None)
        self.assertEqual(account.get_absolute_url(), '')


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

    def test_default_manager_recent(self):
        "The default manager includes tweets from public AND private users"
        public_user = factories.UserFactory(is_private=False)
        private_user = factories.UserFactory(is_private=True)
        public_tweets = factories.TweetFactory.create_batch(
                                                        2, user=public_user)
        private_tweet = factories.TweetFactory(user=private_user)
        self.assertEqual(len(Tweet.objects.all()), 3)

    def test_public_manager(self):
        "The public manager ONLY includes tweets from public users"
        public_user = factories.UserFactory(is_private=False)
        private_user = factories.UserFactory(is_private=True)
        public_tweets = factories.TweetFactory.create_batch(
                                                        2, user=public_user)
        private_tweet = factories.TweetFactory(user=private_user)
        tweets = Tweet.public_objects.all()
        self.assertEqual(len(tweets), 2)
        self.assertEqual(tweets[0].pk, public_tweets[1].pk)
        self.assertEqual(tweets[1].pk, public_tweets[0].pk)

    def test_favorites_manager(self):
        "Should contain recent tweets favorited by any account."
        accounts = factories.AccountFactory.create_batch(2)
        tweets = factories.TweetFactory.create_batch(5)
        accounts[0].user.favorites.add(tweets[2])
        accounts[0].user.favorites.add(tweets[4])
        accounts[1].user.favorites.add(tweets[2])
        favorites = Tweet.favorite_objects.all()
        self.assertEqual(len(favorites), 2)
        self.assertEqual(favorites[0].pk, tweets[4].pk)
        self.assertEqual(favorites[1].pk, tweets[2].pk)

    def test_public_favorites_manager(self):
        "Should contain recent PUBLIC tweets favorited by any account."
        accounts = factories.AccountFactory.create_batch(2)
        public_user = factories.UserFactory(is_private=False)
        private_user = factories.UserFactory(is_private=True)
        public_tweet = factories.TweetFactory(user=public_user)
        private_tweet = factories.TweetFactory(user=private_user)

        accounts[0].user.favorites.add(private_tweet)
        accounts[0].user.favorites.add(public_tweet)
        accounts[1].user.favorites.add(private_tweet)

        favorites = Tweet.public_favorite_objects.all()
        self.assertEqual(len(favorites), 1)
        self.assertEqual(favorites[0].pk, public_tweet.pk)

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

    def test_is_reply(self):
        tweet_1 = factories.TweetFactory(in_reply_to_screen_name='bob')
        self.assertTrue(tweet_1.is_reply)
        tweet_2 = factories.TweetFactory(in_reply_to_screen_name='')
        self.assertFalse(tweet_2.is_reply)


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

    def test_favorites(self):
        user = factories.UserFactory(screen_name='bill')
        tweet_1 = factories.TweetFactory(text ='Tweet 1')
        tweet_2 = factories.TweetFactory(text ='Tweet 2')
        user.favorites.add(tweet_1)
        user.favorites.add(tweet_2)
        faves = User.objects.get(screen_name='bill').favorites.all()
        self.assertEqual(len(faves), 2)
        self.assertIsInstance(faves[0], Tweet)
        self.assertEqual(faves[0].text, 'Tweet 2')
        self.assertEqual(faves[1].text, 'Tweet 1')

