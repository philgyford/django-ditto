# coding: utf-8
import datetime
import pytz

from django.db import IntegrityError
from django.test import TestCase

from .. import factories
from ..models import Account, Tweet, User


class TwitterAccountTestCase(TestCase):

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


class TwitterTweetTestCase(TestCase):

    def test_str(self):
        "Has the correct string represntation"
        tweet = factories.TweetFactory(text='My tweet text')
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

    def test_unique_twitter_id_str(self):
        "Ensures twitter_id_str is unique"
        tweet_1 = factories.TweetFactory(twitter_id_str='123')
        with self.assertRaises(IntegrityError):
            tweet_2 = factories.TweetFactory(twitter_id_str='123')

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

    def test_unique_twitter_id_str(self):
        "Ensures twitter_id_str is unique"
        user_1 = factories.UserFactory(twitter_id_str='123')
        with self.assertRaises(IntegrityError):
            user_2 = factories.UserFactory(twitter_id_str='123')

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

