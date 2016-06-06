import datetime
import pytz

from django.test import TestCase

from ditto.twitter.factories import AccountFactory, TweetFactory, UserFactory
from ditto.twitter.templatetags import ditto_twitter


class TemplatetagsRecentTweetsTestCase(TestCase):

    def setUp(self):
        user_1 = UserFactory(screen_name='terry')
        user_2 = UserFactory(screen_name='bob', is_private=True)
        user_3 = UserFactory(screen_name='thelma')
        account_1 = AccountFactory(user=user_1)
        account_2 = AccountFactory(user=user_2)
        account_3 = AccountFactory(user=user_3)
        self.tweets_1 = TweetFactory.create_batch(2, user=user_1)
        self.tweets_2 = TweetFactory.create_batch(3, user=user_2)
        self.tweets_3 = TweetFactory.create_batch(4, user=user_3)

    def test_recent_tweets(self):
        "Returns recent tweets from all public accounts"
        tweets = ditto_twitter.recent_tweets()
        self.assertEqual(6, len(tweets))
        # tweets[4] would be self.tweets_2[2] if user_2 wasn't private.
        self.assertEqual(tweets[4].pk, self.tweets_1[1].pk)

    def test_recent_tweets_account(self):
        "Returns recent tweets from one public account"
        tweets = ditto_twitter.recent_tweets(screen_name='terry')
        self.assertEqual(2, len(tweets))
        self.assertEqual(tweets[0].pk, self.tweets_1[1].pk)

    def test_recent_tweets_private_account(self):
        "Returns no tweets from a private account"
        tweets = ditto_twitter.recent_tweets(screen_name='bob')
        self.assertEqual(0, len(tweets))

    def test_recent_tweets_limit(self):
        tweets = ditto_twitter.recent_tweets(limit=5)
        self.assertEqual(5, len(tweets))
        self.assertEqual(tweets[4].pk, self.tweets_1[1].pk)


class TemplatetagsRecentFavoritesTestCase(TestCase):

    def setUp(self):
        user_1 = UserFactory(screen_name='terry')
        user_2 = UserFactory(screen_name='bob')
        user_3 = UserFactory(screen_name='thelma', is_private=True)
        account_1 = AccountFactory(user=user_1)
        account_2 = AccountFactory(user=user_2)
        account_3 = AccountFactory(user=user_3)

        tweets = TweetFactory.create_batch(6)
        # One of the tweets is private:
        tweets[0].user.is_private = True
        tweets[0].user.save()

        account_1.user.favorites.add(tweets[0])
        account_1.user.favorites.add(tweets[1])
        account_1.user.favorites.add(tweets[3])
        account_2.user.favorites.add(tweets[5])
        # Private user favoriting public tweets:
        account_3.user.favorites.add(tweets[5])

    def test_recent_favorites(self):
        "Returns recent public tweets favorited by any account."
        tweets = ditto_twitter.recent_favorites()
        self.assertEqual(len(tweets), 3)

    def test_recent_favorites_account(self):
        "Returns recent public tweets favorited by one account"
        tweets = ditto_twitter.recent_favorites(screen_name='terry')
        self.assertEqual(len(tweets), 2)

    def test_recent_favorites_limit(self):
        tweets = ditto_twitter.recent_favorites(limit=2)
        self.assertEqual(len(tweets), 2)

    def test_recent_favorites_private_account(self):
        "Doesn't return favorites by a private account"
        tweets = ditto_twitter.recent_favorites(screen_name='thelma')
        self.assertEqual(len(tweets), 0)


class TemplatetagsDayTweetsTestCase(TestCase):

    def setUp(self):
        user_1 = UserFactory(screen_name='terry')
        user_2 = UserFactory(screen_name='bob')
        user_3 = UserFactory(screen_name='thelma', is_private=True)
        account_1 = AccountFactory(user=user_1)
        account_2 = AccountFactory(user=user_2)
        account_3 = AccountFactory(user=user_3)
        self.tweets_1 = TweetFactory.create_batch(2, user=user_1)
        self.tweets_2 = TweetFactory.create_batch(2, user=user_2)
        self.tweets_3 = TweetFactory.create_batch(2, user=user_3)

        post_time = datetime.datetime(2015, 3, 18, 12, 0, 0).replace(
                                                            tzinfo=pytz.utc)
        self.tweets_1[0].post_time = post_time
        self.tweets_1[0].save()
        self.tweets_2[1].post_time = post_time + datetime.timedelta(hours=1)
        self.tweets_2[1].save()
        self.tweets_3[0].post_time = post_time + datetime.timedelta(hours=2)
        self.tweets_3[0].save()

    def test_day_tweets(self):
        "Returns only public Tweets from the date"
        tweets = ditto_twitter.day_tweets(datetime.date(2015, 3, 18))
        self.assertEqual(2, len(tweets))
        self.assertEqual(tweets[0].pk, self.tweets_2[1].pk)
        self.assertEqual(tweets[1].pk, self.tweets_1[0].pk)

    def test_day_tweets_public_account(self):
        "Returns only Tweets from the day if it's a public account"
        tweets = ditto_twitter.day_tweets(
                            datetime.date(2015, 3, 18), screen_name='terry')
        self.assertEqual(1, len(tweets))
        self.assertEqual(tweets[0].pk, self.tweets_1[0].pk)

    def test_day_tweets_private_account(self):
        "Doesn't return Tweets from the day if it's a private account"
        tweets = ditto_twitter.day_tweets(
                            datetime.date(2015, 3, 18), screen_name='thelma')
        self.assertEqual(0, len(tweets))


class TemplatetagsDayFavoritesTestCase(TestCase):

    def setUp(self):
        user_1 = UserFactory(screen_name='terry')
        user_2 = UserFactory(screen_name='bob')
        user_3 = UserFactory(screen_name='thelma', is_private=True)
        account_1 = AccountFactory(user=user_1)
        account_2 = AccountFactory(user=user_2)
        account_3 = AccountFactory(user=user_3)

        self.tweets = TweetFactory.create_batch(6)
        # One of the tweets is private:
        self.tweets[0].user.is_private = True
        self.tweets[0].user.save()

        post_time = datetime.datetime(2015, 3, 18, 12, 0, 0).replace(
                                                            tzinfo=pytz.utc)
        self.tweets[0].post_time = post_time
        self.tweets[0].save()
        self.tweets[1].post_time = post_time + datetime.timedelta(hours=1)
        self.tweets[1].save()
        self.tweets[5].post_time = post_time + datetime.timedelta(hours=2)
        self.tweets[5].save()

        account_1.user.favorites.add(self.tweets[0]) # private tweet
        account_1.user.favorites.add(self.tweets[1])
        account_1.user.favorites.add(self.tweets[2])
        account_1.user.favorites.add(self.tweets[3])
        account_2.user.favorites.add(self.tweets[4])
        account_3.user.favorites.add(self.tweets[5]) # private user favoriting

    def test_day_favorites(self):
        "Returns only favorited Tweets from the date, favorited by public Accounts"
        tweets = ditto_twitter.day_favorites(datetime.date(2015, 3, 18))
        self.assertEqual(1, len(tweets))
        self.assertEqual(tweets[0].pk, self.tweets[1].pk)

    def test_day_favorites_public_account(self):
        "Returns only favorited Tweets from the date, favorited by a public Account"
        tweets = ditto_twitter.day_favorites(
                            datetime.date(2015, 3, 18), screen_name='terry')
        self.assertEqual(1, len(tweets))
        self.assertEqual(tweets[0].pk, self.tweets[1].pk)

    def test_day_favorites_private_account(self):
        "Doesn't return Tweets favorited by a public Account"
        tweets = ditto_twitter.day_favorites(
                            datetime.date(2015, 3, 18), screen_name='thelma')
        self.assertEqual(0, len(tweets))

