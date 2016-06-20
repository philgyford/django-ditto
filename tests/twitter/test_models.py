# coding: utf-8
import datetime
import json
import os
from unittest.mock import Mock, patch

import pytz
import responses

from django.core.urlresolvers import reverse
from django.db import IntegrityError
from django.test import TestCase

from ditto.twitter import app_settings
from ditto.twitter.factories import AccountFactory,\
        AccountWithCredentialsFactory, PhotoFactory, TweetFactory,\
        UserFactory, VideoFactory, AnimatedGifFactory
from ditto.twitter.models import Account, Media, Tweet, User
from ditto.twitter.fetch.savers import UserSaver


class AccountTestCase(TestCase):

    api_url = 'https://api.twitter.com/1.1'

    api_fixture = 'tests/twitter/fixtures/api/verify_credentials.json'

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
        account = AccountFactory(user=None)
        self.assertEqual(account.__str__(), '%d' % account.pk)

    def test_str_2(self):
        "Has the correct string represntation when it has a user"
        user = UserFactory()
        account = AccountFactory(user=user)
        self.assertEqual(account.__str__(), '@%s' % user.screen_name)

    def test_ordering(self):
        """Multiple accounts are by user.screen_name time ascending"""
        user_1 = UserFactory(screen_name='terry')
        user_2 = UserFactory(screen_name='june')
        account_1 = AccountFactory(user=user_1)
        account_2 = AccountFactory(user=user_2)
        accounts = Account.objects.all()
        self.assertEqual(accounts[0].pk, account_2.pk)

    @responses.activate
    @patch.object(UserSaver, '_fetch_and_save_avatar')
    def test_creates_user(self, fetch_avatar):
        "Should fetch user from API on save if it has no user"
        # Just make the mocked method return the User that's passed in:
        fetch_avatar.side_effect = lambda value: value

        self.add_response(body=self.make_verify_credentials_body(),
                            call='account/verify_credentials')
        account = AccountWithCredentialsFactory(user=None)
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
        user = UserFactory(twitter_id=12552, screen_name='oldname')
        account = AccountWithCredentialsFactory(user=user)
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
        account = AccountFactory.build(user=None)
        result = account.updateUserFromTwitter()
        self.assertEqual(result, False)
        self.assertEqual(0, len(responses.calls))

    @responses.activate
    @patch.object(UserSaver, '_fetch_and_save_avatar')
    def test_update_user_updates_user(self, fetch_avatar):
        "Sets the Account's user and returns it if all is well."
        # Just make the mocked method return the User that's passed in:
        fetch_avatar.side_effect = lambda value: value

        self.add_response(body=self.make_verify_credentials_body(),
                            call='account/verify_credentials')
        # Not saving (as that generates another request):
        account = AccountWithCredentialsFactory.build(user=None)

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
        account = AccountWithCredentialsFactory.build(user=None)

        result = account.updateUserFromTwitter()
        self.assertEqual(1, len(responses.calls))
        self.assertEqual(
                '%s/%s.json' % (self.api_url, 'account/verify_credentials'),
                responses.calls[0].request.url)
        self.assertFalse(result['success'])
        self.assertIn('Could not authenticate you', result['messages'][0])

    def test_has_credentials_true(self):
        self.add_response(body=self.make_verify_credentials_body(),
                            call='account/verify_credentials')
        account = AccountWithCredentialsFactory.build(user=None)
        self.assertTrue(account.has_credentials())

    def test_has_credentials_false(self):
        account = AccountFactory.build(user=None)
        self.assertFalse(account.has_credentials())

    def test_get_absolute_url(self):
        user = UserFactory(screen_name='bill')
        account = AccountFactory(user=user)
        self.assertEqual(account.get_absolute_url(),
            reverse('twitter:user_detail', kwargs={'screen_name': 'bill'}))


class PhotoTestCase(TestCase):
    "Testing things like ordering, privacy. Not individual properties. Sorry."

    def test_str(self):
        photo = PhotoFactory()
        self.assertEqual(photo.__str__(), 'Photo %d' % photo.id)

    def test_media_type(self):
        photo = PhotoFactory()
        self.assertEqual(photo.media_type, 'photo')

    def test_ordering(self):
        """Multiple accounts are sorted by time_created ascending"""
        time_now = datetime.datetime.utcnow().replace(tzinfo=pytz.utc)
        photo_1 = PhotoFactory(
                        time_created=time_now - datetime.timedelta(minutes=1))
        photo_2 = PhotoFactory(time_created=time_now)
        photos = Media.objects.all()
        self.assertEqual(photos[0].pk, photo_1.pk)

    def test_unique_twitter_id(self):
        "Ensures twitter_id is unique"
        photo_1 = PhotoFactory(twitter_id=123)
        with self.assertRaises(IntegrityError):
            photo_2 = PhotoFactory(twitter_id=123)

    def test_default_manager(self):
        "Default Manager shows both private and public photos"
        public_user = UserFactory(is_private=False)
        private_user = UserFactory(is_private=True)
        public_tweet = TweetFactory(user=public_user)
        private_tweet = TweetFactory(user=private_user)
        public_photos = PhotoFactory.create_batch(2, tweets=(public_tweet,))
        private_photos = PhotoFactory.create_batch(1, tweets=(private_tweet,))
        self.assertEqual(len(Media.objects.all()), 3)

    def test_size_urls(self):
        url = 'http://www.example.org/image.jpg'
        photo = PhotoFactory(image_url=url)
        self.assertEqual(photo.large_url,  '%s:large' % url)
        self.assertEqual(photo.medium_url, '%s:medium' % url)
        self.assertEqual(photo.small_url,  '%s:small' % url)
        self.assertEqual(photo.thumb_url,  '%s:thumb' % url)
        self.assertEqual(photo.thumbnail_url,  '%s:thumb' % url)

    def test_tweets(self):
        "It should be possible to belong to more than one tweet."
        tweet_1 = TweetFactory(text='1')
        tweet_2 = TweetFactory(text='2')
        photo = PhotoFactory(tweets=(tweet_1, tweet_2,))
        self.assertEqual(2, photo.tweets.count())
        self.assertEqual(photo.tweets.all()[0], tweet_2)
        self.assertEqual(photo.tweets.all()[1], tweet_1)

    def test_thumnail_dimensions(self):
        "Thumbnail dimensions should always be 150px."
        photo = PhotoFactory(thumb_w=100, thumb_h=100)
        self.assertEqual(150, photo.thumbnail_w)
        self.assertEqual(150, photo.thumbnail_h)

    def test_video_url(self):
        photo = PhotoFactory()
        self.assertEqual('', photo.video_url)


class PhotoLocalTestCase(TestCase):
    "Testing photos when using local files."

    def setUp(self):
        "Set the value of this setting that's used in ditto.twitter.models."
        super().setUp()
        self.default_use_local = app_settings.DITTO_TWITTER_USE_LOCAL_MEDIA
        app_settings.DITTO_TWITTER_USE_LOCAL_MEDIA = True

    def tearDown(self):
        app_settings.DITTO_TWITTER_USE_LOCAL_MEDIA = self.default_use_local

    def test_size_urls(self):
        url = 'http://www.example.org/image.jpg'
        photo = PhotoFactory(image_url=url)
        self.assertEqual(photo.large_url, photo.image_file.url)
        self.assertRegexpMatches(photo.medium_url,
            'CACHE/images/twitter/media/mp/le/example.[^\.]+\.jpg')
        self.assertRegexpMatches(photo.small_url,
            'CACHE/images/twitter/media/mp/le/example.[^\.]+\.jpg')
        self.assertRegexpMatches(photo.thumb_url,
            'CACHE/images/twitter/media/mp/le/example.[^\.]+\.jpg')
        self.assertRegexpMatches(photo.thumbnail_url,
            'CACHE/images/twitter/media/mp/le/example.[^\.]+\.jpg')

    def test_image_url_when_original_missing(self):
        "If we have no original file, we should use the 'missing' image."
        photo = PhotoFactory(image_file='')
        self.assertEqual(photo.small_url, '/static/img/original_missing.jpg')

    def test_broken_image(self):
        "We have an original file, but can't make a smaller version."
        photo = PhotoFactory()
        generator = Mock(side_effect=Exception('Error'))
        # A minimal version of Medial.IMAGE_SIZES for our test:
        image_sizes = {'small': {'generator': generator,},}
        with patch.dict('ditto.twitter.models.Media.IMAGE_SIZES', image_sizes):
            self.assertEqual(photo.small_url,
                             '/static/img/original_error.jpg')


class VideoTestCase(TestCase):
    "Most things are the same for photos and videos, so not re-testing here."

    def test_str(self):
        video = VideoFactory()
        self.assertEqual(video.__str__(), 'Video %d' % video.id)

    def test_media_type(self):
        video = VideoFactory()
        self.assertEqual(video.media_type, 'video')

    def test_video_url_xmpeg(self):
        video = VideoFactory(xmpeg_url='https://example.org/test.m3u8')
        self.assertEqual(video.video_url, video.xmpeg_url)

    def test_video_url_dash(self):
        video = VideoFactory(xmpeg_url='',
                            dash_url='https://example.org/test.mpd')
        self.assertEqual(video.video_url, video.dash_url)

    def test_video_url_mp4(self):
        video = VideoFactory(xmpeg_url='', dash_url='',
                            mp4_url='https://example.org/test.mp4')
        self.assertEqual(video.video_url, video.mp4_url)

    def test_video_url_empty(self):
        video = VideoFactory(xmpeg_url='', mp4_url='', dash_url='')
        self.assertEqual(video.video_url, '')

    def test_video_mime_type_xmpeg(self):
        video = VideoFactory(xmpeg_url='https://example.org/test.m3u8')
        self.assertEqual(video.video_mime_type, 'application/x-mpegURL')

    def test_video_mime_type_dash(self):
        video = VideoFactory(xmpeg_url='',
                            dash_url='https://example.org/test.mpd')
        self.assertEqual(video.video_mime_type, 'application/dash+xml')


class VideoLocalTestCase(TestCase):
    "Testing videos when using local files."

    def setUp(self):
        "Set the value of this setting that's used in ditto.twitter.models."
        super().setUp()
        self.default_use_local = app_settings.DITTO_TWITTER_USE_LOCAL_MEDIA
        app_settings.DITTO_TWITTER_USE_LOCAL_MEDIA = True

    def tearDown(self):
        app_settings.DITTO_TWITTER_USE_LOCAL_MEDIA = self.default_use_local

    def test_video_url_xmpeg(self):
        "Will be same as remote URL."
        video = VideoFactory(xmpeg_url='https://example.org/test.m3u8')
        self.assertEqual(video.video_url, video.xmpeg_url)

    def test_video_url_dash(self):
        "Will be same as remote URL."
        video = VideoFactory(xmpeg_url='',
                            dash_url='https://example.org/test.mpd')
        self.assertEqual(video.video_url, video.dash_url)


class AnimatedGifTestCase(TestCase):
    "Most things are the same for photos and videos, so not re-testing here."

    def test_str(self):
        gif = AnimatedGifFactory()
        self.assertEqual(gif.__str__(), 'Animated GIF %d' % gif.id)

    def test_media_type(self):
        gif = AnimatedGifFactory()
        self.assertEqual(gif.media_type, 'animated_gif')

    def test_video_url_mp4(self):
        gif = AnimatedGifFactory(mp4_url='https://example.org/test.mp4')
        self.assertEqual(gif.video_url, gif.mp4_url)

    def test_video_mime_type_mp4(self):
        gif = AnimatedGifFactory(xmpeg_url='https://example.org/test.mp4')
        self.assertEqual(gif.video_mime_type, 'video/mp4')


class AnimatedGifLocalTestCase(TestCase):
    "Testing Animated GIFs when using local files."

    def setUp(self):
        "Set the value of this setting that's used in ditto.twitter.models."
        super().setUp()
        self.default_use_local = app_settings.DITTO_TWITTER_USE_LOCAL_MEDIA
        app_settings.DITTO_TWITTER_USE_LOCAL_MEDIA = True

    def tearDown(self):
        app_settings.DITTO_TWITTER_USE_LOCAL_MEDIA = self.default_use_local

    def test_video_url_mp4(self):
        gif = AnimatedGifFactory(mp4_url='https://example.org/test.mp4')
        filename = os.path.basename(gif.mp4_file.name)
        self.assertEqual(gif.video_url, 'twitter/media/mp/le/%s' % filename)


class TweetTestCase(TestCase):

    def test_str(self):
        "Has the correct string represntation"
        tweet = TweetFactory(title='My tweet text')
        self.assertEqual(str(tweet), 'My tweet text')

    def test_ditto_item_name(self):
        tweet = TweetFactory()
        self.assertEqual(tweet.ditto_item_name, 'twitter_tweet')

    def test_get_absolute_url(self):
        tweet = TweetFactory(user=UserFactory(screen_name='bob'),
                            twitter_id=1234567890)
        self.assertEqual(tweet.get_absolute_url(), '/twitter/bob/1234567890/')

    def test_ordering(self):
        """Multiple tweets are sorted by post_time descending"""
        time_now = datetime.datetime.utcnow().replace(tzinfo=pytz.utc)
        tweet_1 = TweetFactory(
                        post_time=time_now - datetime.timedelta(minutes=1))
        tweet_2 = TweetFactory(post_time=time_now)
        tweets = Tweet.objects.all()
        self.assertEqual(tweets[0].pk, tweet_2.pk)

    def test_unique_twitter_id(self):
        "Ensures twitter_id is unique"
        tweet_1 = TweetFactory(twitter_id=123)
        with self.assertRaises(IntegrityError):
            tweet_2 = TweetFactory(twitter_id=123)

    def test_account_exists(self):
        "If the tweet is from an Account the account property should return it."
        user = UserFactory()
        account = AccountFactory(user=user)
        tweet = TweetFactory(text='This is my tweet text', user=user)
        self.assertEqual(tweet.account, account)

    def test_account_none(self):
        "If the tweet isn't from an Account its account property should be None."
        tweet = TweetFactory(text='This is my tweet text', user=UserFactory())
        self.assertIsNone(tweet.account)

    def test_default_manager_recent(self):
        "The default manager includes tweets from public AND private users"
        public_user = UserFactory(is_private=False)
        private_user = UserFactory(is_private=True)
        public_tweets = TweetFactory.create_batch(2, user=public_user)
        private_tweet = TweetFactory(user=private_user)
        self.assertEqual(len(Tweet.objects.all()), 3)

    def test_public_manager(self):
        "The public manager ONLY includes tweets from public users"
        public_user = UserFactory(is_private=False)
        private_user = UserFactory(is_private=True)
        public_tweets = TweetFactory.create_batch(2, user=public_user)
        private_tweet = TweetFactory(user=private_user)
        tweets = Tweet.public_objects.all()
        self.assertEqual(len(tweets), 2)
        self.assertEqual(tweets[0].pk, public_tweets[1].pk)
        self.assertEqual(tweets[1].pk, public_tweets[0].pk)

    def test_favorites_manager(self):
        "Should contain recent tweets favorited by any account."
        accounts = AccountFactory.create_batch(2)
        tweets = TweetFactory.create_batch(5)
        accounts[0].user.favorites.add(tweets[2])
        accounts[0].user.favorites.add(tweets[4])
        accounts[1].user.favorites.add(tweets[2])
        favorites = Tweet.favorite_objects.all()
        self.assertEqual(len(favorites), 2)
        self.assertEqual(favorites[0].pk, tweets[4].pk)
        self.assertEqual(favorites[1].pk, tweets[2].pk)

    def test_public_favorites_tweets_manager(self):
        "Should contain recent PUBLIC tweets favorited the Accounts"
        accounts = AccountFactory.create_batch(2)
        public_user = UserFactory(is_private=False)
        private_user = UserFactory(is_private=True)
        public_tweet = TweetFactory(user=public_user)
        private_tweet = TweetFactory(user=private_user)

        accounts[0].user.favorites.add(private_tweet)
        accounts[0].user.favorites.add(public_tweet)
        accounts[1].user.favorites.add(private_tweet)

        favorites = Tweet.public_favorite_objects.all()
        self.assertEqual(len(favorites), 1)
        self.assertEqual(favorites[0].pk, public_tweet.pk)

    def test_public_favorites_accounts_manager(self):
        "Should only show tweets favorited by public Accounts"
        public_user = UserFactory(is_private=False)
        private_user = UserFactory(is_private=True)
        account_1 = AccountFactory(user=public_user)
        account_2 = AccountFactory(user=private_user)
        tweets = TweetFactory.create_batch(5)
        account_1.user.favorites.add(tweets[0])
        account_1.user.favorites.add(tweets[3])
        account_2.user.favorites.add(tweets[1])
        account_2.user.favorites.add(tweets[3])

        favorites = Tweet.public_favorite_objects.all()
        self.assertEqual(len(favorites), 2)
        self.assertEqual(favorites[0].pk, tweets[3].pk)
        self.assertEqual(favorites[1].pk, tweets[0].pk)

    def test_is_public(self):
        "Tweet should be public if tweet's user is public"
        user = UserFactory(is_private=False)
        tweet = TweetFactory(user=user)
        self.assertFalse(tweet.is_private)

    def test_is_private(self):
        "Tweet should be private if tweet's user is private"
        user = UserFactory(is_private=True)
        tweet = TweetFactory(user=user)
        self.assertTrue(tweet.is_private)

    def test_is_reply(self):
        tweet_1 = TweetFactory(in_reply_to_screen_name='bob')
        self.assertTrue(tweet_1.is_reply)
        tweet_2 = TweetFactory(in_reply_to_screen_name='')
        self.assertFalse(tweet_2.is_reply)

    def test_in_reply_to_url(self):
        tweet_1 = TweetFactory(in_reply_to_screen_name='bob',
                                in_reply_to_status_id=1234567)
        self.assertEqual(tweet_1.in_reply_to_url,
                        'https://twitter.com/bob/status/1234567')
        tweet_2 = TweetFactory(in_reply_to_screen_name='')
        self.assertEqual(tweet_2.in_reply_to_url, '')

    @patch('ditto.twitter.models.htmlify_tweet')
    def test_makes_text_html(self, htmlify_method):
        "When save() is called, text_html should be created from the raw JSON"
        htmlify_method.return_value = 'my test text'
        tweet = TweetFactory()
        tweet.raw = '{"text":"my test text"}'
        tweet.save()
        htmlify_method.assert_called_once_with({'text': 'my test text'})
        self.assertEqual(tweet.text_html, 'my test text')

    def test_get_quoted_tweet(self):
        quoted_tweet = TweetFactory(text='The quote!', twitter_id=123)
        tweet = TweetFactory(quoted_status_id=123)
        self.assertEqual(tweet.get_quoted_tweet().text, 'The quote!')

    def test_get_quoted_tweet_none(self):
        tweet = TweetFactory(quoted_status_id=None)
        self.assertIsNone(tweet.get_quoted_tweet())

    @patch('ditto.twitter.models.Tweet.public_objects.get')
    def test_get_quoted_tweet_caches(self, get_method):
        "Should only fetch quoted Tweet from DB once."
        quoted_tweet = TweetFactory(text='The quote!', twitter_id=123)
        tweet = TweetFactory(quoted_status_id=123)
        tweet.get_quoted_tweet()
        tweet.get_quoted_tweet()
        self.assertEqual(get_method.call_count, 1)

    def test_get_retweeted_tweet(self):
        retweeted_tweet = TweetFactory(text='Retweeted tweet!', twitter_id=123)
        tweet = TweetFactory(retweeted_status_id=123)
        self.assertEqual(tweet.get_retweeted_tweet().text, 'Retweeted tweet!')

    def test_get_retweeted_tweet_none(self):
        tweet = TweetFactory(retweeted_status_id=None)
        self.assertIsNone(tweet.get_retweeted_tweet())

    @patch('ditto.twitter.models.Tweet.public_objects.get')
    def test_get_retweeted_tweet_caches(self, get_method):
        "Should only fetch retweeted Tweet from DB once."
        retweeted_tweet = TweetFactory(text='Retweeted tweet!', twitter_id=123)
        tweet = TweetFactory(retweeted_status_id=123)
        tweet.get_retweeted_tweet()
        tweet.get_retweeted_tweet()
        self.assertEqual(get_method.call_count, 1)

    def test_media(self):
        tweet = TweetFactory()
        photo_1 = PhotoFactory()
        photo_2 = PhotoFactory()
        photo_1.tweets.add(tweet)
        photo_2.tweets.add(tweet)
        self.assertEqual(2, tweet.media.count())


class TweetNextPrevTestCase(TestCase):

    def setUp(self):
        dt = datetime.datetime.strptime(
                                    '2016-04-08 12:00:00', '%Y-%m-%d %H:%M:%S'
                                ).replace(tzinfo=pytz.utc)

        user = UserFactory()
        account = AccountFactory(user=user)
        self.tweet_1 = TweetFactory(user=user, post_time=dt)

        private_user = UserFactory(is_private=True)
        private_account = AccountFactory(user=private_user)
        self.private_tweeet = TweetFactory(user=private_user,
                                post_time=dt + datetime.timedelta(days=1))

        # Tweet by a different user:
        user_2 = UserFactory()
        account_2 = AccountFactory(user=user_2)
        self.other_tweet = TweetFactory(user=user_2,
                                post_time=dt + datetime.timedelta(days=2))

        self.tweet_2 = TweetFactory(user=user,
                                    post_time=dt + datetime.timedelta(days=3))

    def test_next_public_by_post_time(self):
        self.assertEqual(self.tweet_1.get_next_public_by_post_time(),
                        self.tweet_2)

    def test_next_public_by_post_time_none(self):
        self.assertIsNone(self.tweet_2.get_next_public_by_post_time())

    def test_previous_public_by_post_time(self):
        self.assertEqual(self.tweet_2.get_previous_public_by_post_time(),
                        self.tweet_1)

    def test_previous_public_by_post_time_none(self):
        self.assertIsNone(self.tweet_1.get_previous_public_by_post_time())

    def test_next(self):
        self.assertEqual(self.tweet_1.get_next(),self.tweet_2)

    def test_next_none(self):
        self.assertIsNone(self.tweet_2.get_next())

    def test_previous(self):
        self.assertEqual(self.tweet_2.get_previous(), self.tweet_1)

    def test_previous_none(self):
        self.assertIsNone(self.tweet_1.get_previous())


class UserTestCase(TestCase):

    def test_str(self):
        "Has the correct string represntation"
        user = UserFactory(screen_name='bill')
        self.assertEqual(user.__str__(), '@bill')

    def test_ordering(self):
        """Multiple users are sorted by screen_name"""
        user_1 = UserFactory(screen_name='bill')
        user_2 = UserFactory(screen_name='alice')
        users = User.objects.all()
        self.assertEqual(users[0].pk, user_2.pk)

    def test_permalink(self):
        "Generates the correct permalink"
        user = UserFactory(screen_name='bill')
        self.assertEqual(user.permalink, 'https://twitter.com/bill')

    def test_avatar_url(self):
        user = UserFactory(twitter_id=123456, avatar__filename='my_face.jpg')
        self.assertEqual(user.avatar_url,
                                    'twitter/avatars/34/56/123456/my_face.jpg')

    def test_avatar_url_short_id(self):
        user = UserFactory(twitter_id=12, avatar__filename='my_face.jpg')
        self.assertEqual(user.avatar_url,
                                    'twitter/avatars/12/12/my_face.jpg')

    def test_avatar_url_missing(self):
        user = UserFactory(avatar=None)
        self.assertEqual(user.avatar_url, '/static/img/default_avatar.png')

    def test_profile_image_url(self):
        url = 'https://twitter.com/tester.jpg'
        user = UserFactory(profile_image_url_https=url)
        self.assertEqual(user.profile_image_url, url)

    def test_favorites_count(self):
        user = UserFactory(favourites_count=37)
        self.assertEqual(user.favorites_count, 37)

    def test_unique_twitter_id(self):
        "Ensures twitter_id is unique"
        user_1 = UserFactory(twitter_id=123)
        with self.assertRaises(IntegrityError):
            user_2 = UserFactory(twitter_id=123)

    def test_going_private(self):
        "Makes the user's tweets private if they go private"
        # Start off public:
        user = UserFactory(is_private=False)
        tweet = TweetFactory(user=user)
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
        user = UserFactory(is_private=True)
        tweet = TweetFactory(user=user)
        self.assertTrue(tweet.is_private)
        # Now change to public:
        user.is_private = False
        # Should change the user's tweets to public:
        user.save()
        tweet.refresh_from_db()
        self.assertFalse(tweet.is_private)

    def test_favorites(self):
        user = UserFactory(screen_name='bill')
        tweet_1 = TweetFactory(text ='Tweet 1')
        tweet_2 = TweetFactory(text ='Tweet 2')
        user.favorites.add(tweet_1)
        user.favorites.add(tweet_2)
        faves = User.objects.get(screen_name='bill').favorites.all()
        self.assertEqual(len(faves), 2)
        self.assertIsInstance(faves[0], Tweet)
        self.assertEqual(faves[0].text, 'Tweet 2')
        self.assertEqual(faves[1].text, 'Tweet 1')

    def test_with_accounts_manager(self):
        "Only returns Users with Accounts"
        users = UserFactory.create_batch(4)
        account_1 = AccountFactory(user=users[0])
        account_2 = AccountFactory(user=users[2])
        users_with_accounts = User.objects_with_accounts.all()
        self.assertEqual(2, len(users_with_accounts))
        self.assertEqual(users_with_accounts[0].pk, users[0].pk)
        self.assertEqual(users_with_accounts[1].pk, users[2].pk)

    @patch('ditto.twitter.models.htmlify_description')
    def test_makes_description_html(self, htmlify_method):
        "When save() is called description_html should be created from raw JSON"
        htmlify_method.return_value = 'my test description'
        user = UserFactory()
        user.raw = '{"description":"my test description"}'
        user.save()
        htmlify_method.assert_called_once_with(
                                        {'description': 'my test description'})
        self.assertEqual(user.description_html, 'my test description')

    def test_get_absolute_url(self):
        user = UserFactory(screen_name='bob')
        self.assertEqual(user.get_absolute_url(), '/twitter/bob/')

