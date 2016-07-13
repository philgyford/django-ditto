import os
import time

from django.core.files import File

from twython import Twython, TwythonError

from . import FetchError
from .savers import TweetSaver, UserSaver
from ..models import Media, Tweet, User
from ...core.utils import datetime_now
from ...core.utils.downloader import DownloadException, filedownloader


# Classes which fetch data from the Twitter API for a single Account.
# You're probably not going to call these classes directly - use the classes
# in fetch.fetchers.*


# CLASSES HERE:
#
# Fetch
#   FetchVerify
#   FetchLookup
#     FetchUsers
#     FetchTweets
#   FetchNewTweets
#     FetchTweetsRecent
#     FetchTweetsFavorite
# FetchFiles


class Fetch(object):
    """Parent class for children that will call the Twitter API to fetch data
    for a single Account.

    Children should define their own methods for:
        _call_api()
        _save_results()

    and optionally:
        _post_save()
        _post_fetch()

    Use it like:
        account = Account.objects.get(pk=1)
        fetcher = RecentTweetsFetcher(account)
        result = fetcher.fetch()
    """
    # Will be an Account object, passed into init()
    account = None

    # Will be the Twython object for calling the Twitter API.
    api = None

    # Will be the UTC datetime that we fetch the results.
    fetch_time = None

    # Will be the results fetched from the API via Twython.
    results = []

    # Will be a list of all the Users/Tweets/etc created/updated:
    objects = []

    # What we'll return for each account:
    return_value = {}

    # When fetching Tweets or Users this will be the total amount fetched.
    results_count = 0

    def __init__(self, account):
        self.account = account

    def fetch(self):
        self._reset()

        if self.account.user:
            self.return_value['account'] = self.account.user.screen_name
        elif self.account.pk:
            self.return_value['account'] = 'Account: %s' % str(self.account)
        else:
            self.return_value['account'] = 'Unsaved Account'

        if self.account.has_credentials():
            self.api = Twython(
                self.account.consumer_key, self.account.consumer_secret,
                self.account.access_token, self.account.access_token_secret)
            self._fetch_pages()
            self._post_fetch()
        else:
            self.return_value['success'] = False
            self.return_value['messages'] = ['Account has no API credentials']

        self.return_value['fetched'] = self.results_count

        return self.return_value

    def _reset(self):
        self.fetch_time = datetime_now()
        self.results = []
        self.objects = []
        self.return_value = {}
        self.results_count = 0

    def _fetch_pages(self):
        try:
            self._call_api()
        except TwythonError as e:
            self.return_value['success'] = False
            self.return_value['messages'] = ['Error when calling API: %s' % e]
        else:
            # If we've got to the last 'page' of tweet results, we'll receive
            # an empty list from the API.
            if (len(self.results) > 0):
                self._save_results()
                self._post_save()

            self.return_value['success'] = True
        return

    def _since_id(self):
        return None

    def _call_api(self):
        """Define in child classes.
        Should call self.api.a_function_name() and set self.results with the
        results.
        """
        raise FetchError("Children of the Fetch class should define their own _call_api() method.")

    def _save_results(self):
        """Define in child classes.
        Should go through self._results() and, probably, call
        TweetSaver().save_tweet() or UserSaver().save_user() for each one.
        """
        self.objects = []

    def _post_save(self):
        """Can optionally be defined in child classes.
        Do any extra things that need to be done after saving a page of data.
        """
        pass

    def _post_fetch(self):
        """Can optionally be defined in child classes.
        Do any extra things that need to be done after we've fetched all data.
        """
        pass


class FetchVerify(Fetch):
    """For verifying an Account's API credentials, but ALSO fetches the user
    data for that single Account.
    """

    def _call_api(self):
        """Sets self.results to data for a single Twitter User."""
        self.results = self.api.verify_credentials()

    def _post_save(self):
        "Adds the one User we fetched to the data we'll return from fetch()."
        self.return_value['user'] = self.objects[0]

    def _save_results(self):
        """Creates/updates the user data.
        In other sibling classes this would loop through results and save each
        in turn, but here we only have a single result.
        """
        user = UserSaver().save_user(self.results, self.fetch_time)
        self.objects = [user]


class FetchLookup(Fetch):
    """
    Parent class for classes that call lookup* queries on the Twitter API.
    eg, lookup_user or lookup_status.
    """

    # Maximum number of users/tweets to ask for per query, allowed by the API:
    fetch_per_query = 100

    # Will be all the IDs we have yet to fetch from the API:
    ids_remaining_to_fetch = []

    # Maxmum number of requests allowed per 15 minute window:
    max_requests = 60

    def fetch(self, ids=[]):
        """
        Keyword arguments:
        ids -- A list of Twitter user/tweet IDs to fetch. Optional. If not
        supplied, we fetch data for all Users/Tweets in the DB. Up to the
        maximum allowed in a reasonable window. At time of writing, the API
        allows 100 per query, and 60 queries per 15 minute window. So 6000
        ids would be the maximum.
        """
        self._set_initial_ids(ids)
        return super().fetch()

    def _set_initial_ids(self, ids):
        """ids is a list of Twitter User/Tweet IDs, or an empty list."""

        if len(ids) == 0:
            # What's the biggest number we're able to fetch:
            limit = self.fetch_per_query * self.max_requests
            # Get all the IDs, up to the limit, ordered by fetch_time, so
            # that we get the least-recently updated this time.
            ids = self.model.objects.values_list('twitter_id', flat=True).order_by('fetch_time')[:limit]

        self.ids_remaining_to_fetch = ids

    def _post_save(self):
        # Remove the IDs we just fetched from the list:
        self.ids_remaining_to_fetch = self.ids_remaining_to_fetch[
                                                        self.fetch_per_query:]

        self.results_count += len(self.results)

        if self._more_to_fetch():
            time.sleep(0.5)
            self._fetch_pages()

    def _more_to_fetch(self):
        if len(self.ids_remaining_to_fetch) > 0:
            return True
        else:
            return False

    def _ids_to_fetch_in_query(self):
        """
        If self.fetch_per_query is 100, this returns the next 100 ids from
        self.ids_remaining_to_fetch.
        """
        return self.ids_remaining_to_fetch[:self.fetch_per_query]


class FetchUsers(FetchLookup):
    """For fetching users.

    Supply fetch() with a list of Twitter user IDs, and corresponding Users
    will be created/updated in the DB. Or, if no IDs are supplied, fetch the
    least-recently-fetched Users.
    """

    model = User

    def _call_api(self):
        # Sometimes this worked fine with numeric IDs, other times Tweepy
        # didn't put them in the URL and they had to be strings. Odd.
        ids = [str(id) for id in self._ids_to_fetch_in_query()]
        self.results = self.api.lookup_user(
                            user_id=ids,
                            include_entities=True
                        )

    def _save_results(self):
        for user in self.results:
            user_obj = UserSaver().save_user(user, self.fetch_time)
            self.objects.append(user_obj)


class FetchTweets(FetchLookup):
    """For fetching specific Tweets.

    Supply fetch() with a list of Twitter Tweet IDs, and coresponding Tweets
    will be created/updated in the DB. Or, if no IDs are supplied, fetch the
    least-recently-fetched Tweets.
    """

    model = Tweet

    def _call_api(self):
        ids = [str(id) for id in self._ids_to_fetch_in_query()]
        self.results = self.api.lookup_status(
                            id=ids,
                            tweet_mode='extended',
                            include_entities=True,
                            trim_user=False,
                            map=False
                        )

    def _save_results(self):
        for tweet in self.results:
            tweet_obj = TweetSaver().save_tweet(tweet, self.fetch_time)
            self.objects.append(tweet_obj)


class FetchNewTweets(Fetch):
    """A parent class for those which fetch "new" Tweets. ie, fetching a
    quantity of the most recent Tweets/favorited Tweets. As opposed to fetching
    a specified selection of Tweets, regardless of when they were.
    """

    # When fetching 'new' Tweets, after a query, this will be set as the
    # max_id to use for the next query.
    max_id = None

    # When fetching 'new' Tweets, this will be set as the highest ID
    # fetched, so it can be used to set account.last_recent_id or
    # account.last_favorite_id when we're done.
    last_id = None

    remaining_to_fetch = 0

    # Will be 'new' or 'number':
    fetch_type = 'new'

    def fetch(self, count='new'):
        """
        Keyword arguments:
        count -- Either 'new' (get the Tweets since the last fetch) or a number
                to fetch that many, up to the API limit (3200 currently).
        """
        if count == 'new':
            self.fetch_type = 'new'
        else:
            self.fetch_type = 'number'
            self.remaining_to_fetch = count

        return super().fetch()

    def _post_save(self):
        "After saving a page of results, what to do..."

        if self.last_id is None:
            self.last_id = self.results[0]['id']

        # The max_id for the next 'page' of tweets:
        self.max_id = self.results[-1]['id'] - 1

        if self.fetch_type == 'number':
            self.remaining_to_fetch -= len(self.results)

        self.results_count += len(self.results)

        if self._more_to_fetch():
            time.sleep(0.5)
            self._fetch_pages()

    def _more_to_fetch(self):
        if self.fetch_type == 'new':
            if self._since_id() is None or self.max_id > self._since_id():
                return True
            else:
                return False
        elif self.fetch_type == 'number':
            if self.remaining_to_fetch > 0:
                return True
            else:
                return False
        return False

    def _tweets_to_fetch_in_query(self):
        "How many Tweets to fetch in the current API query."
        to_fetch = 200
        if self.fetch_type == 'number' and self.remaining_to_fetch < 200:
            to_fetch = self.remaining_to_fetch
        return to_fetch


class FetchTweetsRecent(FetchNewTweets):
    """For fetching recent tweets by a single Account."""

    def _since_id(self):
        if self.fetch_type == 'new':
            return self.account.last_recent_id
        else:
            return None

    def _call_api(self):
        """Sets self.results to be the timeline of tweets for this Account.
        If the account's `last_recent_id` is set, we fetch tweets from that ID
        onwards, up to 200.
        Otherwise we fetch the most recent 200.
        """
        # account.last_recent_id might be None, in which case it's not used in
        # the API call:
        self.results = self.api.get_user_timeline(
                                user_id=self.account.user.twitter_id,
                                include_rts=True,
                                count=self._tweets_to_fetch_in_query(),
                                max_id=self.max_id,
                                since_id=self._since_id())

    def _post_fetch(self):
        "Set last_recent_id of our Account to the most recent Tweet fetched."
        if self.last_id is not None:
            self.account.last_recent_id = self.last_id
            self.account.save()

    def _save_results(self):
        """Takes the list of tweet data from the API and creates or updates the
        Tweet objects and the posters' User objects.
        Adds each new Tweet object to self.objects.
        """
        for tweet in self.results:
            tw = TweetSaver().save_tweet(tweet, self.fetch_time)
            self.objects.append(tw)


class FetchTweetsFavorite(FetchNewTweets):
    """For fetching tweets favorited by a single Account."""

    def _since_id(self):
        if self.fetch_type == 'new':
            return self.account.last_favorite_id
        else:
            return None

    def _call_api(self):
        """Sets self.results to be recent tweets favorited by this Account.
        If the account has `last_favorite_id` set, all the favorites since
        that ID are fetched (up to 200).
        Otherwise, the most recent 200 are fetched.
        """
        # account.last_favorite_id might be None, in which case it's not used in
        # the API call:
        self.results = self.api.get_favorites(
                                user_id=self.account.user.twitter_id,
                                count=self._tweets_to_fetch_in_query(),
                                max_id=self.max_id,
                                since_id=self._since_id())

    def _post_fetch(self):
        """Set the last_favorite_id of our Account to the most recent Tweet we
        fetched.
        """
        if self.last_id is not None:
            self.account.last_favorite_id = self.last_id
            self.account.save()

    def _save_results(self):
        """Takes the list of tweet data from the API and creates or updates the
        Tweet objects and the posters' User objects.
        Adds each new Tweet object to self.objects.
        """
        for tweet in self.results:
            tw = TweetSaver().save_tweet(tweet, self.fetch_time)
            # Associate this tweet with the Account's user:
            self.account.user.favorites.add(tw)
            self.objects.append(tw)


class FetchFiles(object):
    """
    For fetching image files and Animated GIFs' MP4 files.

    Doesn't inherit from Fetch because it doesn't use the API or rely on having
    an Account object.

    Doesn't fetch MP4s (or other movie files) for videos because the URLs
    for MP4 video files (as opposed to MP4 Animated GIF files) will be
    discontinued from 2016-08-01.
    https://twittercommunity.com/t/retiring-mp4-video-output/66093/15?u=philgyford

    Use it like:
        fetcher = FilesFetcher()
        result = fetcher.fetch()
    or:
        result = fetcher.fetch(fetch_all=True)
    """

    # What we'll return for each account:
    return_value = {}

    # When fetching Tweets or Users this will be the total amount fetched.
    results_count = 0

    def fetch(self, fetch_all=False):
        """
        Download and save original images for all Media objects
        (or just those that don't already have them).

        fetch_all -- Boolean. Fetch ALL images, even if we've already
                        got them?
        """

        self._fetch_files(fetch_all)

        self.return_value['fetched'] = self.results_count

        return self.return_value

    def _fetch_files(self, fetch_all):
        """
        Download and save original images for all Media objects
        (or just those that don't already have them).

        fetch_all -- Boolean. Fetch ALL images, even if we've already
                        got them?
        """

        media = Media.objects.all()

        if not fetch_all:
            media = media.filter(image_file='')

        error_messages = []

        for media_obj in media:
            try:
                self._fetch_and_save_file(
                                    media_obj=media_obj, media_type='image')
                self.results_count += 1
            except FetchError as e:
                error_messages.append(str(e))

            if media_obj.media_type == 'animated_gif':
                try:
                    self._fetch_and_save_file(
                                        media_obj=media_obj, media_type='mp4')
                    self.results_count += 1
                except FetchError as e:
                    error_messages.append(str(e))

        if len(error_messages) > 0:
            self.return_value['success'] = False
            self.return_value['messages'] = error_messages
        else:
            self.return_value['success'] = True

    def _fetch_and_save_file(self, media_obj, media_type):
        """
        Downloads an image file and saves it to the Media object.

        Expects:
            media_obj -- A Media object.
            media_type -- String, either 'image' or 'mp4'.

        Raises FetchError if something goes wrong.
        """

        if media_type == 'mp4':
            url = media_obj.mp4_url
            acceptable_content_types = ['video/mp4',]
        elif media_type == 'image':
            url = media_obj.image_url
            acceptable_content_types = [
                        'image/jpeg', 'image/jpg', 'image/png', 'image/gif',]
        else:
            raise FetchError('media_type should be "image" or "mp4"')

        filepath = False
        try:
            # Saves the file to /tmp/:
            filepath = filedownloader.download(url, acceptable_content_types)
        except DownloadException as e:
            raise FetchError(e)

        if filepath:
            # Reopen file and save to the Media object:
            reopened_file = open(filepath, 'rb')
            django_file = File(reopened_file)

            if media_type == 'mp4':
                media_obj.mp4_file.save(
                                    os.path.basename(filepath), django_file)
            else:
                media_obj.image_file.save(
                                    os.path.basename(filepath), django_file)




