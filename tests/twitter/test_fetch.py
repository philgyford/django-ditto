# coding: utf-8
import datetime
from decimal import Decimal
import json
from unittest.mock import call, patch

import pytz
import responses
from freezegun import freeze_time

from django.http import QueryDict
from django.test import TestCase

from ditto.twitter import factories
from ditto.twitter.fetch import FavoriteTweetsFetcher, FetchError,\
        TweetMixin, TwitterFetcher, RecentTweetsFetcher, UserMixin,\
        UsersFetcher, TweetsFetcher, VerifyFetcher, FetchVerify
from ditto.twitter.models import Account, Media, Tweet, User


class FetchTwitterTestCase(TestCase):
    """Parent class with commomn things."""

    api_url = 'https://api.twitter.com/1.1'

    # Should be set in child classes to use self.make_response_body():
    # eg 'account/verify_credentials'
    api_call = ''

    # Should be set in child classes to use self.make_response_body():
    # eg, 'tweets.json'
    api_fixture = ''

    def make_response_body(self):
        "Makes the JSON response to a call to the API"
        json_file = open(
                '%s%s' % ('tests/twitter/fixtures/api/', self.api_fixture))
        json_data = json_file.read()
        json_file.close()
        return json_data

    def add_response(self, body, status=200, querystring={}, match_querystring=False, method='GET'):
        """Add a Twitter API response.

        Keyword arguments:
        body -- The JSON string representing the body of the response.
        status -- Int, HTTP response status.
        querystring -- eg {'count': 200, 'user_id': 123}
        match_querystring -- You probably want this to be True if you've set
                             a querystring.
        method -- 'GET' or 'POST'.
        """
        url = '%s/%s.json' % (self.api_url, self.api_call)

        if len(querystring):
            qs = '&'.join("%s=%s" % (key, querystring[key])
                                                for key in querystring.keys())
            url = '%s?%s' % (url, qs)

        method = responses.POST if method == 'POST' else responses.GET

        responses.add(
            method,
            url,
            status=status,
            match_querystring=match_querystring,
            body=body,
            content_type='application/json; charset=utf-8'
        )


class TweetMixinTestCase(FetchTwitterTestCase):
    """Testing the TweetMixin"""

    # Note that we've changed the id and id_str of each Tweet in this
    # fixture to something much shorter, and easier to test with.
    api_fixture = 'tweets.json'

    def make_tweet(self, is_private=False):
        self.fetch_time = datetime.datetime.utcnow().replace(tzinfo=pytz.utc)

        # Get the JSON for a single tweet.
        tweets_data = json.loads(self.make_response_body())
        tweet_data = tweets_data[0]

        if is_private:
            tweet_data['user']['protected'] = True

        # Send the JSON, and our new User object, to try and save the tweet:
        mixin = TweetMixin()
        saved_tweet = mixin.save_tweet(tweet_data, self.fetch_time)

        # Load that saved tweet from the DB:
        return Tweet.objects.get(twitter_id=300)


    @freeze_time("2015-08-14 12:00:00", tz_offset=-8)
    def test_saves_correct_tweet_data(self):
        tweet = self.make_tweet()

        #And check it's all there:
        self.assertEqual(tweet.title, "@flaneur ooh, very exciting, thank you!  Both my ears owe you a drink.")
        self.assertEqual(tweet.summary, "@flaneur ooh, very exciting, thank you! Both my ears owe you a drink.")
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

class TweetMixinMediaTestCase(FetchTwitterTestCase):
    "Parent class for testing the save_media() method of the TweetMixin."

    # Child classes should have an api_fixture property.

    def setUp(self):
        "Save a tweet using the api_fixture's data."

        fetch_time = datetime.datetime.utcnow().replace(tzinfo=pytz.utc)

        tweet_data = json.loads(self.make_response_body())

        # Send the JSON, and our new User object, to try and save the tweet:
        mixin = TweetMixin()
        saved_tweet = mixin.save_tweet(tweet_data, fetch_time)

        # Load that saved tweet from the DB:
        self.tweet = Tweet.objects.get(twitter_id=9876543210)


class TweetMixinPhotosTestCase(TweetMixinMediaTestCase):
    "Testing that photos are saved correctly."

    api_fixture = 'tweet_with_photos.json'

    def test_saves_photos(self):
        self.assertEqual(self.tweet.media_count, 3)

        photos = Media.objects.filter(tweet=self.tweet)

        self.assertEqual(len(photos), 3)

        photo = photos[1]

        self.assertEqual(photo.media_type, 'photo')
        self.assertEqual(photo.twitter_id, 1234567890)
        self.assertEqual(photo.image_url,
                            "https://pbs.twimg.com/media/CSaWsSkWsAA-yXb.jpg")
        self.assertEqual(photo.is_private, self.tweet.is_private)
        self.assertEqual(photo.large_w, 935)
        self.assertEqual(photo.large_h, 397)
        self.assertEqual(photo.medium_w, 600)
        self.assertEqual(photo.medium_h, 254)
        self.assertEqual(photo.small_w, 340)
        self.assertEqual(photo.small_h, 144)
        self.assertEqual(photo.thumb_w, 150)
        self.assertEqual(photo.thumb_h, 150)


class TweetMixinVideosTestCase(TweetMixinMediaTestCase):
    "Testing that videos are saved correctly."

    api_fixture = 'tweet_with_video.json'

    def test_saves_videos(self):
        self.assertEqual(self.tweet.media_count, 1)

        videos = Media.objects.filter(tweet=self.tweet)
        self.assertEqual(len(videos), 1)

        video = videos[0]

        self.assertEqual(video.media_type, 'video')
        self.assertEqual(video.twitter_id, 1234567890)
        self.assertEqual(video.image_url, "https://pbs.twimg.com/ext_tw_video_thumb/661601811007188992/pu/img/gcxHGl7EA08a-Gps.jpg")
        self.assertEqual(video.is_private, self.tweet.is_private)
        self.assertEqual(video.large_w, 640)
        self.assertEqual(video.large_h, 360)
        self.assertEqual(video.medium_w, 600)
        self.assertEqual(video.medium_h, 338)
        self.assertEqual(video.small_w, 340)
        self.assertEqual(video.small_h, 191)
        self.assertEqual(video.thumb_w, 150)
        self.assertEqual(video.thumb_h, 150)

        self.assertEqual(video.aspect_ratio, '16:9')
        self.assertEqual(video.dash_url, 'https://video.twimg.com/ext_tw_video/661601811007188992/pu/pl/K0pVjBgnc5BI_4e5.mpd')
        self.assertEqual(video.xmpeg_url, 'https://video.twimg.com/ext_tw_video/661601811007188992/pu/pl/K0pVjBgnc5BI_4e5.m3u8')


class TweetMixinAnimatedGifTestCase(TweetMixinMediaTestCase):
    "Testing that animated GIFs are saved correctly."

    api_fixture = 'tweet_with_animated_gif.json'

    def test_saves_gifs(self):
        self.assertEqual(self.tweet.media_count, 1)

        media = Media.objects.filter(tweet=self.tweet)
        self.assertEqual(len(media), 1)

        gif = media[0]

        self.assertEqual(gif.media_type, 'animated_gif')
        self.assertEqual(gif.twitter_id, 726396540303073281)
        self.assertEqual(gif.image_url, "https://pbs.twimg.com/tweet_video_thumb/ChStzgbWYAErHLi.jpg")
        self.assertEqual(gif.is_private, self.tweet.is_private)
        self.assertEqual(gif.large_w, 320)
        self.assertEqual(gif.large_h, 232)
        self.assertEqual(gif.medium_w, 320)
        self.assertEqual(gif.medium_h, 232)
        self.assertEqual(gif.small_w, 320)
        self.assertEqual(gif.small_h, 232)
        self.assertEqual(gif.thumb_w, 150)
        self.assertEqual(gif.thumb_h, 150)
        self.assertEqual(gif.aspect_ratio, '40:29')
        self.assertEqual(gif.mp4_url, 'https://pbs.twimg.com/tweet_video/ChStzgbWYAErHLi.mp4')


class UserMixinTestCase(FetchTwitterTestCase):

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

    def make_user_object(self, user_data):
        """"Creates/updates a User from API data, then fetches that User from
        the DB and returns it.
        """
        fetch_time = datetime.datetime.utcnow().replace(tzinfo=pytz.utc)
        user_mixin = UserMixin()
        saved_user = user_mixin.save_user(user_data, fetch_time)
        return User.objects.get(twitter_id=12552)

    @freeze_time("2015-08-14 12:00:00", tz_offset=-8)
    def test_saves_correct_user_data(self):

        user_data = self.make_user_data()
        user = self.make_user_object(user_data)

        self.assertEqual(user.fetch_time,
                        datetime.datetime.utcnow().replace(tzinfo=pytz.utc))
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

    def test_set_accounts_bad_screen_name(self):
        "It raises FetchError when passed a non-existent screen_name"
        with self.assertRaises(FetchError):
            self.fetcher._set_accounts('percy')


class TwitterFetcherInactiveAccountsTestCase(FetchTwitterTestCase):

    def setUp(self):
        user_1 = factories.UserFactory(screen_name='jill')
        user_2 = factories.UserFactory(screen_name='debs')
        account_1 = factories.AccountFactory(user=user_1, is_active=False)
        account_2 = factories.AccountFactory(user=user_2, is_active=False)

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
        user_1 = factories.UserFactory(screen_name='jill', twitter_id=1)
        user_2 = factories.UserFactory(screen_name='debs', twitter_id=2)
        self.account_1 = factories.AccountWithCredentialsFactory(
                        user=user_1, last_recent_id=100, last_favorite_id=100)
        self.account_2 = factories.AccountWithCredentialsFactory(
                        user=user_2, last_recent_id=100, last_favorite_id=100)

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
        with patch('ditto.twitter.fetch.FetchTweetsRecent._save_results'):
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
        with patch('ditto.twitter.fetch.FetchTweetsRecent._save_results'):
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
        user = factories.UserFactory(screen_name='bobby')
        account = factories.AccountFactory(user=user)
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
    @patch('ditto.twitter.fetch.TweetMixin.save_tweet')
    def test_saves_correct_tweet_data(self, save_tweet):
        """Assert save_tweet is called once per tweet.
        Not actually checking what's passed in."""
        save_tweet.side_effect = [factories.TweetFactory(),
                        factories.TweetFactory(), factories.TweetFactory()]
        self.add_response(body=self.make_response_body())
        result = RecentTweetsFetcher(screen_name='jill').fetch()
        self.assertEqual(save_tweet.call_count, 3)

    @responses.activate
    def test_fetches_multiple_pages_for_new(self):
        "Fetches subsequent pages until no more recent results are returned."
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

        with patch('ditto.twitter.fetch.FetchTweetsRecent._save_results'):
            with patch('time.sleep'):
                result = RecentTweetsFetcher(screen_name='jill').fetch(
                                                                    count=700)
                self.assertEqual(4, len(responses.calls))


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
        with patch('ditto.twitter.fetch.FetchTweetsFavorite._save_results'):
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
        with patch('ditto.twitter.fetch.FetchTweetsFavorite._save_results'):
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
        user = factories.UserFactory(screen_name='bobby')
        account = factories.AccountFactory(user=user)
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
    @patch('ditto.twitter.fetch.TweetMixin.save_tweet')
    def test_saves_correct_tweet_data(self, save_tweet):
        """Assert save_tweet is called once per tweet.
        Not actually checking what's passed in."""
        save_tweet.side_effect = [factories.TweetFactory(),
                        factories.TweetFactory(), factories.TweetFactory()]
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
    def test_fetches_multiple_pages_for_new(self):
        """Fetches subsequent pages until no results are returned."""
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

        with patch('ditto.twitter.fetch.FetchTweetsFavorite._save_results'):
            with patch('time.sleep'):
                result = FavoriteTweetsFetcher(screen_name='jill').fetch(
                                                                    count=700)
                self.assertEqual(4, len(responses.calls))


class UsersFetcherTestCase(TwitterFetcherTestCase):

    api_fixture = 'users_lookup.json'

    api_call = 'users/lookup'

    @responses.activate
    def test_makes_one_api_call(self):
        self.add_response(body=self.make_response_body())
        result = UsersFetcher(screen_name='jill').fetch([460060168, 26727655, 6795192])
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
        users = factories.UserFactory.create_batch(5)
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
        user = factories.UserFactory.create(
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

        with patch('ditto.twitter.fetch.FetchUsers._save_results'):
            with patch('time.sleep'):
                result = UsersFetcher(screen_name='jill').fetch(ids)
                self.assertEqual(4, len(responses.calls))


class TweetsFetcherTestCase(TwitterFetcherTestCase):

    api_fixture = 'tweets.json'

    api_call = 'statuses/lookup'

    @responses.activate
    def test_makes_one_api_call(self):
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
        tweets = factories.TweetFactory.create_batch(5)
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
        tweets = factories.TweetFactory.create(
                                    twitter_id=200, text='Will change')
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

        with patch('ditto.twitter.fetch.FetchTweets._save_results'):
            with patch('time.sleep'):
                result = TweetsFetcher(screen_name='jill').fetch(ids)
                self.assertEqual(4, len(responses.calls))


class VerifyFetcherTestCase(TwitterFetcherTestCase):

    api_fixture = 'verify_credentials.json'

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
        self.assertIn('Rate limit exceeded', result[0]['messages'][0])

    @responses.activate
    def test_returns_error_if_no_creds(self):
        "If an account has no API credentials, the result is correct"
        user = factories.UserFactory(screen_name='bobby')
        account = factories.AccountFactory(user=user)
        self.add_response(body=self.make_response_body())
        result = VerifyFetcher(screen_name='bobby').fetch()
        self.assertFalse(result[0]['success'])
        self.assertIn('Account has no API credentials',
                                                    result[0]['messages'][0])

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


class FetchVerifyTestCase(FetchTwitterTestCase):

    api_fixture = 'verify_credentials.json'

    api_call = 'account/verify_credentials'

    @responses.activate
    def test_fetch_for_account_creates(self):
        "Saves and returns new user after successful API call"
        self.add_response(body=self.make_response_body())
        account = factories.AccountWithCredentialsFactory.build(id=4, user=None)

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
    def test_fetch_for_account_updates(self):
        "Saves and returns updated existing user after successful API call"
        self.add_response(body=self.make_response_body())
        user = factories.UserFactory(twitter_id=12552, screen_name='bob')
        account = factories.AccountWithCredentialsFactory(user=user)

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

        account = factories.AccountWithCredentialsFactory.build(user=None)
        result = FetchVerify(account=account).fetch()

        self.assertEqual(result['account'], 'Unsaved Account')
        self.assertEqual(1, len(responses.calls))
        self.assertEqual(
                '%s/%s.json' % (self.api_url, 'account/verify_credentials'),
                responses.calls[0].request.url)
        self.assertTrue('Could not authenticate you' in result['messages'][0])

