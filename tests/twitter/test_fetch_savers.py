import datetime
from decimal import Decimal
import json
import os
import pytz
import tempfile
from unittest.mock import patch

from freezegun import freeze_time

from ditto.core.utils import datetime_now
from ditto.core.utils.downloader import DownloadException, filedownloader
from django.test import override_settings

from .test_fetch import FetchTwitterTestCase
from ditto.twitter.fetch.savers import TweetSaver, UserSaver
from ditto.twitter.models import Media, Tweet, User


class TweetSaverTestCase(FetchTwitterTestCase):
    """Testing the TweetSaver class"""

    # Note that we've changed the id and id_str of each Tweet in this
    # fixture to something much shorter, and easier to test with.
    api_fixture = 'tweets.json'

    def make_tweet(self, is_private=False):
        self.fetch_time = datetime_now()

        # Get the JSON for a single tweet.
        tweets_data = json.loads(self.make_response_body())
        tweet_data = tweets_data[0]

        if is_private:
            tweet_data['user']['protected'] = True

        # Send the JSON, and our new User object, to try and save the tweet:
        saved_tweet = TweetSaver().save_tweet(tweet_data, self.fetch_time)

        # Load that saved tweet from the DB:
        return Tweet.objects.get(twitter_id=300)


    @freeze_time("2015-08-14 12:00:00", tz_offset=-8)
    def test_saves_correct_tweet_data(self):
        tweet = self.make_tweet()

        #And check it's all there:
        self.assertEqual(tweet.title, "@flaneur ooh, very exciting, thank you!  Both my ears owe you a drink.")
        self.assertEqual(tweet.summary, "@flaneur ooh, very exciting, thank you!\n\nBoth my ears owe you a drink.")
        self.assertEqual(tweet.text, "@flaneur ooh, very exciting, thank you!\n\nBoth my ears owe you a drink.")
        self.assertEqual(tweet.latitude, Decimal('40.057016'))
        self.assertEqual(tweet.longitude, Decimal('-75.143103'))
        self.assertFalse(tweet.is_private)
        self.assertEqual(tweet.fetch_time, self.fetch_time)
        self.assertEqual(tweet.permalink,
                                'https://twitter.com/philgyford/status/300')

        tweets = json.loads(self.make_response_body())
        self.assertEqual(tweet.raw, json.dumps(tweets[0]))

        self.assertEqual(tweet.user.screen_name, 'philgyford')
        self.assertEqual(tweet.twitter_id, 300)
        self.assertEqual(tweet.post_time, datetime.datetime.strptime(
                                    '2015-08-06 19:42:59', '%Y-%m-%d %H:%M:%S'
                                ).replace(tzinfo=pytz.utc))
        self.assertEqual(tweet.favorite_count, 2)
        self.assertEqual(tweet.retweet_count, 1)
        self.assertEqual(tweet.media_count, 0)
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
        tweet = self.make_tweet(is_private=True)

        self.assertTrue(tweet.is_private)

    def test_saves_user(self):
        "Saving a Tweet should also save its user."
        tweet = self.make_tweet()

        self.assertEqual(tweet.user.twitter_id, 12552)
        self.assertEqual(tweet.user.fetch_time, self.fetch_time)

    def test_saves_quoted_tweets(self):
        "Saving a Tweet that quotes another Tweet should save the quoted Tweet."
        self.api_fixture = 'tweets_with_quoted_tweet.json'
        tweet = self.make_tweet()

        self.assertEqual(tweet.text, 'Quoting a couple of tweets: https://t.co/HSaYtiWAbg and https://t.co/hpX1aGkWsv')
        self.assertEqual(tweet.quoted_status_id, 663744897778872321)

        quoted_tweet = Tweet.objects.get(twitter_id=663744897778872321)
        self.assertEqual(quoted_tweet.text, 'Very quiet in the basement of #Innovate2015 come say hi and talk #iot')
        self.assertEqual(quoted_tweet.user.screen_name, 'iotwatch')

    def test_saves_double_quoted_tweets(self):
        """Saving Tweet 1 that quotes Tweet 2 that quotes Tweet 3 should save
        Tweet 2, and cope with Tweet 3 not being savable."""
        self.api_fixture = 'tweets_with_double_quoted_tweet.json'
        tweet1 = self.make_tweet()

        self.assertEqual(tweet1.text, 'Anyone fancy meeting sometime today/tomorrow to see @genmon\u2019s book vending machine at Google Campus, EC2? https://t.co/1ScaCLOUxb')
        # ie, tweet2's ID:
        self.assertEqual(tweet1.quoted_status_id, 714528026650869760)

        tweet2 = Tweet.objects.get(twitter_id=714528026650869760)
        self.assertEqual(tweet2.text, 'Ludicrous hobby is ludicrous. But here we go https://t.co/DqYZB2gtQv')
        self.assertEqual(tweet2.user.screen_name, 'genmon')

        # ie, tweet3's ID:
        self.assertEqual(tweet2.quoted_status_id, 714527559946473474)

    def test_saves_retweeted_tweets(self):
        "Saving a Tweet that is a retweet should save the retweeted Tweet."
        self.api_fixture = 'tweets_with_retweeted_tweet.json'
        tweet = self.make_tweet()

        self.assertEqual(tweet.text, 'RT @stefiorazi: Twitter help: Looking for early Barbican Estate residents to interview. mail@modernistestates RTs appreciated https://t.co/\u2026')
        self.assertEqual(tweet.retweeted_status_id, 735555565724827649)

        retweeted_tweet = Tweet.objects.get(twitter_id=735555565724827649)
        self.assertEqual(retweeted_tweet.text,
            'Twitter help: Looking for early Barbican Estate residents to interview. mail@modernistestates RTs appreciated https://t.co/IFSZIh9DHm')
        self.assertEqual(retweeted_tweet.user.screen_name, 'stefiorazi')

    def test_extended_2016_tweets(self):
        """Saves correctly from the new (2016) tweet format.
        https://dev.twitter.com/overview/api/upcoming-changes-to-tweets
        """
        self.api_fixture = 'tweets_extended_format_2016.json'
        tweet = self.make_tweet()

        self.assertEqual(tweet.text, '@philgyford Here\u2019s a test tweet that goes on as much as possible and includes an image. Hi to my fans in testland! https://t.co/tzhyk2QWSr')
        self.assertEqual(tweet.summary, 'Here\u2019s a test tweet that goes on as much as possible and includes an image. Hi to my fans in testland!')
        self.assertEqual(tweet.title, 'Here\u2019s a test tweet that goes on as much as possible and includes an image. Hi to my fans in testland!')


class TweetSaverMediaTestCase(FetchTwitterTestCase):
    "Parent class for testing the save_media() method of the TweetSaver class."

    # Child classes should have an api_fixture property.

    def setUp(self):
        "Save a tweet using the api_fixture's data."

        fetch_time = datetime_now()

        tweet_data = json.loads(self.make_response_body())

        # Send the JSON, and our new User object, to try and save the tweet:
        saved_tweet = TweetSaver().save_tweet(tweet_data, fetch_time)

        # Load that saved tweet from the DB:
        self.tweet = Tweet.objects.get(twitter_id=9876543210)


class TweetSaverPhotosTestCase(TweetSaverMediaTestCase):
    "Testing that photos are saved correctly."

    api_fixture = 'tweet_with_photos.json'

    def test_saves_photos(self):
        self.assertEqual(self.tweet.media_count, 3)

        photos = Media.objects.filter(tweets__pk=self.tweet.pk)

        self.assertEqual(len(photos), 3)

        photo = photos[1]

        self.assertEqual(photo.media_type, 'photo')
        self.assertEqual(photo.twitter_id, 1234567890)
        self.assertEqual(photo.image_url,
                            "https://pbs.twimg.com/media/CSaWsSkWsAA-yXb.jpg")
        self.assertEqual(photo.large_w, 935)
        self.assertEqual(photo.large_h, 397)
        self.assertEqual(photo.medium_w, 600)
        self.assertEqual(photo.medium_h, 254)
        self.assertEqual(photo.small_w, 340)
        self.assertEqual(photo.small_h, 144)
        self.assertEqual(photo.thumb_w, 150)
        self.assertEqual(photo.thumb_h, 150)
        self.assertIn(self.tweet, photo.tweets.all())


class TweetSaverVideosTestCase(TweetSaverMediaTestCase):
    "Testing that videos are saved correctly."

    api_fixture = 'tweet_with_video.json'

    def test_saves_videos(self):
        self.assertEqual(self.tweet.media_count, 1)

        videos = Media.objects.filter(tweets__pk=self.tweet.pk)
        self.assertEqual(len(videos), 1)

        video = videos[0]

        self.assertEqual(video.media_type, 'video')
        self.assertEqual(video.twitter_id, 1234567890)
        self.assertEqual(video.image_url, "https://pbs.twimg.com/ext_tw_video_thumb/661601811007188992/pu/img/gcxHGl7EA08a-Gps.jpg")
        self.assertEqual(video.large_w, 640)
        self.assertEqual(video.large_h, 360)
        self.assertEqual(video.medium_w, 600)
        self.assertEqual(video.medium_h, 338)
        self.assertEqual(video.small_w, 340)
        self.assertEqual(video.small_h, 191)
        self.assertEqual(video.thumb_w, 150)
        self.assertEqual(video.thumb_h, 150)
        self.assertIn(self.tweet, video.tweets.all())

        self.assertEqual(video.aspect_ratio, '16:9')
        self.assertEqual(video.dash_url, 'https://video.twimg.com/ext_tw_video/661601811007188992/pu/pl/K0pVjBgnc5BI_4e5.mpd')
        self.assertEqual(video.xmpeg_url, 'https://video.twimg.com/ext_tw_video/661601811007188992/pu/pl/K0pVjBgnc5BI_4e5.m3u8')


class TweetSaverAnimatedGifTestCase(TweetSaverMediaTestCase):
    "Testing that animated GIFs are saved correctly."

    api_fixture = 'tweet_with_animated_gif.json'

    def test_saves_gifs(self):
        self.assertEqual(self.tweet.media_count, 1)

        media = Media.objects.filter(tweets__pk=self.tweet.pk)
        self.assertEqual(len(media), 1)

        gif = media[0]

        self.assertEqual(gif.media_type, 'animated_gif')
        self.assertEqual(gif.twitter_id, 726396540303073281)
        self.assertEqual(gif.image_url, "https://pbs.twimg.com/tweet_video_thumb/ChStzgbWYAErHLi.jpg")
        self.assertEqual(gif.large_w, 320)
        self.assertEqual(gif.large_h, 232)
        self.assertEqual(gif.medium_w, 320)
        self.assertEqual(gif.medium_h, 232)
        self.assertEqual(gif.small_w, 320)
        self.assertEqual(gif.small_h, 232)
        self.assertEqual(gif.thumb_w, 150)
        self.assertEqual(gif.thumb_h, 150)
        self.assertIn(self.tweet, gif.tweets.all())
        self.assertEqual(gif.aspect_ratio, '40:29')
        self.assertEqual(gif.mp4_url, 'https://pbs.twimg.com/tweet_video/ChStzgbWYAErHLi.mp4')


class UserSaverTestCase(FetchTwitterTestCase):

    api_fixture = 'verify_credentials.json'

    def make_user_data(self, custom={}):
        """Get the JSON for a single user.
        custom is a dict of attributes to override on the default data.
        eg, {'protected': True}
        """
        raw_json = self.make_response_body()
        user_data = json.loads(raw_json)
        for key, value in custom.items():
            user_data[key] = value
        return user_data

    @patch.object(filedownloader, 'download')
    def make_user_object(self, user_data, download):
        """"Creates/updates a User from API data, then fetches that User from
        the DB and returns it.
        """
        # Quietly prevents avatar files being fetched:
        download.side_effect = DownloadException('Oops')
        saved_user = UserSaver().save_user(user_data, datetime_now())
        return User.objects.get(twitter_id=12552)

    @freeze_time("2015-08-14 12:00:00", tz_offset=-8)
    def test_saves_correct_user_data(self):

        user_data = self.make_user_data()
        user = self.make_user_object(user_data)

        self.assertEqual(user.fetch_time, datetime_now())
        self.assertEqual(user.raw, json.dumps(user_data))
        self.assertEqual(user.screen_name, 'philgyford')
        self.assertEqual(user.url, 'http://www.gyford.com/')
        self.assertFalse(user.is_private)
        self.assertFalse(user.is_verified)
        self.assertEqual(user.created_at, datetime.datetime.strptime(
                                    '2006-11-15 16:55:59', '%Y-%m-%d %H:%M:%S'
                                ).replace(tzinfo=pytz.utc))
        self.assertEqual(user.description, 'Good. Good to Firm in places.')
        self.assertEqual(user.location, 'London, UK')
        self.assertEqual(user.time_zone, 'London')
        self.assertEqual(user.profile_image_url_https, 'https://pbs.twimg.com/profile_images/1167616130/james_200208_300x300_normal.jpg')
        self.assertEqual(user.favourites_count, 1389)
        self.assertEqual(user.followers_count, 2435)
        self.assertEqual(user.friends_count, 309)
        self.assertEqual(user.listed_count, 138)
        self.assertEqual(user.statuses_count, 16428)

    def test_saves_alternate_data(self):
        """Check some different data to in the main user test."""

        user_data = self.make_user_data({'protected': True, 'verified': True})
        user = self.make_user_object(user_data)
        self.assertTrue(user.is_private)
        self.assertTrue(user.is_verified)

    def test_handles_missing_expanded_url(self):
        """Test fix for when expanded_url is None, as here:
            {'indices': [0, 28], 'url': 'http://www.benhammersley.com', 'expanded_url': None}
        """
        entities = {'url':{'urls':[
            {'indices': [0, 22], 'url': 'http://t.co/UEs0CCkdrl', 'expanded_url': None}
        ]}}
        user_data = self.make_user_data({'entities': entities})
        user = self.make_user_object(user_data)
        self.assertEqual(user.url, 'http://t.co/UEs0CCkdrl')

    @patch.object(filedownloader, 'download')
    @patch.object(UserSaver, '_fetch_and_save_avatar')
    def test_calls_fetch_and_save_avatar(self, fetch_avatar, download):
        "_fetch_and_save_avatar should be called with the User object."
        # Quietly prevents avatar files being fetched:
        download.side_effect = DownloadException('Oops')
        # Just make the mocked method return the User that's passed in:
        fetch_avatar.side_effect = lambda value: value

        user_data = self.make_user_data()
        saved_user = UserSaver().save_user(user_data, datetime_now())
        fetch_avatar.assert_called_once_with(saved_user)

    @override_settings(MEDIA_ROOT=tempfile.gettempdir())
    @patch.object(filedownloader, 'download')
    def test_downloads_and_saves_avatar(self, download):
        "Should call download() and save avatar."
        # Make a temporary file, like download() would make:
        jpg = tempfile.NamedTemporaryFile()
        temp_filepath = jpg.name
        download.return_value = temp_filepath

        user_data = self.make_user_data()
        saved_user = UserSaver().save_user(user_data, datetime_now())

        download.assert_called_once_with(saved_user.profile_image_url_https,
                        ['image/jpeg', 'image/jpg', 'image/png', 'image/gif'])

        self.assertEqual(saved_user.avatar, 'twitter/avatars/25/52/12552/%s' %
                                            os.path.basename(temp_filepath))

    @patch.object(filedownloader, 'download')
    @patch.object(os.path, 'exists')
    def test_does_not_download_and_save_avatar(self, exists, download):
        "If we already have the user's avatar, don't download it."
        # Fake that the file we look for exists:
        exists.return_value = True

        user_data = self.make_user_data()
        saved_user = UserSaver().save_user(user_data, datetime_now())
        assert not download.called

