# coding: utf-8
import datetime
import json
import pytz
import time

from twython import Twython, TwythonError

from .models import Account, Media, Tweet, User


# CLASSES HERE:
#
# FetchError
#
# TwitterItemMixin
#   UserMixin
#     TweetMixin
#
# Fetch
#   FetchVerify
#   FetchUsers
#   FetchTweets
#     FetchTweetsRecent
#     FetchTweetsFavorite
#
# TwitterFetcher
#   VerifyFetcher
#   UsersFetcher
#   RecentTweetsFetcher
#   FavoriteTweetsFetcher
#
# The *Fetcher classes are the ones that should be used externally, like:
#
#   fetcher = RecentTweetsFetcher(screen_name='philgyford')
#   fetcher.fetch(count=20)


class FetchError(Exception):
    pass


class TwitterItemMixin(object):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _api_time_to_datetime(self, api_time, time_format='%a %b %d %H:%M:%S +0000 %Y'):
        """Change a text datetime from the API to a datetime with timezone.
        api_time is a string like 'Wed Nov 15 16:55:59 +0000 2006'.
        """
        return datetime.datetime.strptime(api_time, time_format).replace(
                                                            tzinfo=pytz.utc)


class UserMixin(TwitterItemMixin):
    "Provides a method for creating/updating a User using data from the API."

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def save_user(self, user, fetch_time, extra={}):
        """With Twitter user data from the API, it creates or updates the User
        and returns the User object.

        Keyword arguments:
        user -- A dict of the data about a user from the API's JSON.
        fetch_time -- A datetime.

        Returns the User object.
        """
        raw_json = json.dumps(user)

        defaults = {
            'fetch_time': fetch_time,
            'raw': raw_json,
            'screen_name': user['screen_name'],
            'name': user['name'],
            'is_private': user['protected'],
            'is_verified': user['verified'],
            'profile_image_url_https': user['profile_image_url_https'],
        }

        # When ingesting tweets there are lots of fields the 'user' element
        # doesn't have, compared to the API:

        if 'created_at' in user:
            defaults['created_at'] = self._api_time_to_datetime(user['created_at'])

        # If there's a URL it will be a t.co shortened one.
        # So we go through the entities to find its expanded version.
        if 'url' in user and user['url']:
            user_url = user['url']
            if 'url' in user['entities'] and 'urls' in user['entities']['url']:
                for url_dict in user['entities']['url']['urls']:
                    if url_dict['url'] == user['url'] and url_dict['expanded_url'] is not None:
                        user_url = url_dict['expanded_url']
            defaults['url'] = user_url

        if 'description' in user:
            defaults['description'] = user['description'] if user['description'] else ''

        if 'location' in user:
            defaults['location'] = user['location'] if user['location'] else ''

        if 'time_zone' in user:
            defaults['time_zone'] = user['time_zone'] if user['time_zone'] else ''

        if 'favourites_count' in user:
            defaults['favourites_count'] = user['favourites_count']

        for a_count in ['followers_count', 'friends_count', 'listed_count', 'statuses_count']:
            if a_count in user:
                defaults[a_count] = user[a_count]

        user_obj, created = User.objects.update_or_create(
            twitter_id=user['id'], defaults=defaults
        )

        return user_obj


class TweetMixin(UserMixin):
    """Provides a method for creating/updating a Tweet (and its User) using
    data from the API. Also used by ingest.TweetIngester()
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def save_media(self, tweet):
        """Takes a Tweet object and creates or updates any photos and videos
        based on the JSON data in its `raw` field.

        Keyword arguments:
        tweet -- The Tweet object. Must have been saved as we need its id.

        Returns:
        Total number of items for this Tweet (regardless of whether they were
            created or updated).
        """
        import itertools

        # What we'll return:
        media_count = 0

        try:
            json_data = json.loads(tweet.raw)
        except ValueError as error:
            return media_count

        try:
            media = json_data['extended_entities']['media']
        except KeyError:
            return media_count

        for item in media:
            # Things common to photos and videos.

            defaults = {
                'tweet':        tweet,
                'media_type':   'photo',
                'twitter_id':   item['id'],
                'image_url':    item['media_url_https'],
                'is_private':   tweet.is_private,
            }

            for size in ['large', 'medium', 'small', 'thumb']:
                if size in item['sizes']:
                    defaults[size+'_w'] = item['sizes'][size]['w']
                    defaults[size+'_h'] = item['sizes'][size]['h']
                else:
                    defaults[size+'_w'] = None
                    defaults[size+'_h'] = None

            # Adding things ony used for videos:
            if 'type' in item and item['type'] == 'video' and 'video_info' in item:
                defaults['media_type'] = 'video'

                info = item['video_info']

                # eg, '16:9'
                defaults['aspect_ratio'] = '%s:%s' % (
                        info['aspect_ratio'][0], info['aspect_ratio'][1])

                defaults['duration'] = info['duration_millis']

                # Group the variants into a dict with keys like 'video/mp4'
                # and values being a list of dicts. Each of those dicts
                # being a single variant.
                # [
                #   {'video/mp4': [{'url':'...', 'bitrate':320000},
                #                  {'url':'...', 'bitrate':832000},]
                #   },
                # ]

                # Sort the list of dicts by 'content_type'.
                # Need to do this for the next grouping stage.
                sorted_variants = sorted(
                            info['variants'], key=lambda k: k['content_type'])
                grouped_variants = {}

                for key, variants in itertools.groupby(sorted_variants, lambda k: k['content_type']):
                    #grouped_variants[key] = sorted(
                                    #list(items), key=lambda k: k['bitrate'])
                    grouped_variants[key] = list(variants)

                if 'application/dash+xml' in grouped_variants:
                    defaults['dash_url'] = grouped_variants['application/dash+xml'][0]['url']
                if 'application/x-mpegURL' in grouped_variants:
                    defaults['xmpeg_url'] = grouped_variants['application/x-mpegURL'][0]['url']
                if 'video/webm' in grouped_variants:
                    defaults['webm_url'] = grouped_variants['video/webm'][0]['url']
                    defaults['webm_bitrate'] = grouped_variants['video/webm'][0]['bitrate']

                if 'video/mp4' in grouped_variants:
                    # Sort them by bitrate:
                    mp4s = sorted(grouped_variants['video/mp4'],
                                                    key=lambda k: k['bitrate'])

                    for idx, mp4 in enumerate(mp4s):
                        if idx < 3:
                            defaults['mp4_url_%s' % (idx+1)] = mp4['url']
                            defaults['mp4_bitrate_%s' % (idx+1)] = mp4['bitrate']

            media_obj, created = Media.objects.update_or_create(
                    twitter_id=item['id'],
                    defaults=defaults
                )
            media_count += 1

        return media_count

    def save_tweet(self, tweet, fetch_time):
        """Takes a dict of tweet data from the API and creates or updates a
        Tweet object and its associated User object.

        Keyword arguments:
        tweet -- The tweet data.
        fetch_time -- A datetime.

        Returns:
        The Tweet object that was created or updated.
        """
        raw_json = json.dumps(tweet)
        try:
            created_at = self._api_time_to_datetime(tweet['created_at'])
        except ValueError:
            # Because the tweets imported from a downloaded archive have a
            # different format for created_at. Of course. Why not?!
            created_at = self._api_time_to_datetime(tweet['created_at'], time_format='%Y-%m-%d %H:%M:%S +0000')

        user = self.save_user(tweet['user'], fetch_time)

        defaults = {
            'fetch_time':       fetch_time,
            'raw':              raw_json,
            'user':             user,
            'is_private':       user.is_private,
            'post_time':        created_at,
            'permalink':        'https://twitter.com/%s/status/%s' % (
                                            user.screen_name, tweet['id']),
            'title':            tweet['text'].replace('\n', ' ').replace('\r', ' '),
            'summary':          tweet['text'],
            'text':             tweet['text'],
            'twitter_id':       tweet['id'],
            'source':           tweet['source']
        }

        # Some of these are only present in tweets from the API (not in the
        # tweets from the downloaded archive).
        # Some are just not always present, such as coordinates and place stuff.

        if 'favorite_count' in tweet:
            defaults['favorite_count'] = tweet['favorite_count']

        if 'retweet_count' in tweet:
            defaults['retweet_count'] = tweet['retweet_count']

        if 'lang' in tweet:
            defaults['language'] = tweet['lang']

        if 'coordinates' in tweet and tweet['coordinates'] and 'type' in tweet['coordinates']:
            if tweet['coordinates']['type'] == 'Point':
                defaults['latitude'] = tweet['coordinates']['coordinates'][1]
                defaults['longitude'] = tweet['coordinates']['coordinates'][0]
            # TODO: Handle Polygons?

        if 'in_reply_to_screen_name' in tweet and tweet['in_reply_to_screen_name']:
            defaults['in_reply_to_screen_name'] =  tweet['in_reply_to_screen_name']
        else:
            defaults['in_reply_to_screen_name'] = ''

        if 'in_reply_to_status_id' in tweet:
            defaults['in_reply_to_status_id'] = tweet['in_reply_to_status_id']

        if 'in_reply_to_user_id' in tweet:
            defaults['in_reply_to_user_id'] = tweet['in_reply_to_user_id']

        if 'place' in tweet and tweet['place'] is not None:
            if 'attributes' in tweet['place'] and 'street_address' in tweet['place']['attributes']:
                defaults['place_attribute_street_address'] = tweet['place']['attributes']['street_address']
            if 'full_name' in tweet['place']:
                defaults['place_full_name'] = tweet['place']['full_name']
            if 'country' in tweet['place']:
                defaults['place_country'] = tweet['place']['country']

        if 'quoted_status_id' in tweet:
            defaults['quoted_status_id'] = tweet['quoted_status_id']
            # We'll also create/update the quoted User object, and quoted Tweet.
            quoted_user = self.save_user(
                                    tweet['quoted_status']['user'], fetch_time)
            quoted_tweet_obj = self.save_tweet(
                                            tweet['quoted_status'], fetch_time)

        tweet_obj, created = Tweet.objects.update_or_create(
                twitter_id=tweet['id'],
                defaults=defaults
            )

        # Create/update any Photos, and update the Tweet's photo_count:
        media_count = self.save_media(tweet=tweet_obj)
        tweet_obj.media_count = media_count

        tweet_obj.save()

        return tweet_obj



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

        if self.account.hasCredentials():
            self.api = Twython(
                self.account.consumer_key, self.account.consumer_secret,
                self.account.access_token, self.account.access_token_secret)
            self._fetch_pages()
            self._post_fetch()
        else:
            self.return_value['success'] = False
            self.return_value['message'] = 'Account has no API credentials'

        self.return_value['fetched'] = self.results_count

        return self.return_value

    def _reset(self):
        self.fetch_time = datetime.datetime.utcnow().replace(tzinfo=pytz.utc)
        self.results = []
        self.objects = []
        self.return_value = {}
        self.results_count = 0

    def _fetch_pages(self):
        try:
            self._call_api()
        except TwythonError as e:
            self.return_value['success'] = False
            self.return_value['message'] = 'Error when calling API: %s' % e
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

    def _save_results(self):
        """Define in child classes.
        Should go through self._results() and, probably, call
        self.save_tweet() or self.save_user() for each one.
        """
        self.objects = []


class FetchVerify(UserMixin, Fetch):
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
        user = self.save_user(self.results, self.fetch_time)
        self.objects = [user]


class FetchUsers(UserMixin, Fetch):
    """For fetching users.

    Supply fetch() with a list of Twitter user IDs, and corresponding Users
    will be created/updated in the DB.
    """

    # Maximum number of users to ask for per query, allowed by the API:
    fetch_per_query = 100

    # Will be all the IDs we have yet to fetch from the API:
    ids_remaining_to_fetch = []

    # Maxmum number of requests allowed per 15 minute window:
    max_requests = 60

    def fetch(self, user_ids=[]):
        """
        Keyword arguments:
        user_ids -- A list of Twitter user IDs to fetch. Optional. If not
        supplied, we fetch data for all Users in the DB. Up to the maximum
        allowed in a reasonable window. At time of writing, the API allows
        100 per query, and 60 queries per 15 minute window. So 6000 user_ids
        would be the maximum.
        """

        if len(user_ids) == 0:
            # What's the biggest number we're able to fetch:
            limit = self.fetch_per_query * self.max_requests
            # Get all the IDs, up to the limit, ordered by fetch_time, so
            # that we get the least-recently updated this time.
            user_ids = User.objects.values_list('twitter_id', flat=True).order_by('fetch_time')[:limit]

        self.ids_remaining_to_fetch = user_ids
        return super().fetch()

    def _call_api(self):
        # Sometimes this worked fine with numeric IDs, other times Tweepy
        # didn't put them in the URL and they had to be strings. Odd.
        ids = [str(id) for id in self._ids_to_fetch_in_query()]
        self.results = self.api.lookup_user(
                            user_id=ids,
                            include_entities=False
                        )

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

    def _save_results(self):
        for user in self.results:
            user_obj = self.save_user(user, self.fetch_time)
            self.objects.append(user_obj)

    def _ids_to_fetch_in_query(self):
        """
        If self.fetch_per_query is 100, this returns the next 100 user_ids from
        self.ids_remaining_to_fetch.
        """
        return self.ids_remaining_to_fetch[:self.fetch_per_query]


class FetchTweets(TweetMixin, Fetch):
    """A parent class for those which fetch Tweets - RecentTweets or
    FavoriteTweets.
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

        if self.fetch_type == 'new':
            # The max_id for the next 'page' of tweets:
            self.max_id = self.results[-1]['id'] - 1
        elif self.fetch_type == 'number':
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


class FetchTweetsRecent(FetchTweets):
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
            tw = self.save_tweet(tweet, self.fetch_time)
            self.objects.append(tw)


class FetchTweetsFavorite(FetchTweets):
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
            tw = self.save_tweet(tweet, self.fetch_time)
            # Associate this tweet with the Account's user:
            self.account.user.favorites.add(tw)
            self.objects.append(tw)


class TwitterFetcher(object):
    """Parent class for children that will call the Twitter API to fetch data
    for one or several Accounts.

    Use like:
        fetcher = ChildFetcher(screen_name='philgyford')
        fetcher.fetch()

    Or, for all accounts:
        fetcher = ChildTwitterFetcher()
        fetcher.fetch()

    Child classes should at least override:
        _get_account_fetcher()
    """

    def __init__(self, screen_name=None):
        """Keyword arguments:
        screen_name -- of the one Account to get, or None for all Accounts.

        Raises:
        FetchError if passed a screen_name there is no Account for.
        """
        # Sets self.accounts:
        self._set_accounts(screen_name)

        # Will be a list of dicts that we return detailing succes/failure
        # results, one dict per account we've fetched for. eg:
        # [ {'account': 'thescreename', 'success': True, 'fetched': 200} ]
        self.return_values = []

    def fetch(self, **kwargs):
        """Fetch data for one or more Accounts.

        Returns:
        A list of dicts, one dict per Account, containing data about
        success/failure.
        """
        for account in self.accounts:
            accountFetcher = self._get_account_fetcher(account)
            return_value = accountFetcher.fetch(**kwargs)
            self._add_to_return_values(return_value)

        return self.return_values

    def _get_account_fetcher(self, account):
        """Should be changed for each child class.
        Should return an instance of a child of TwitterAccountFetcher().

        Keyword arguments:
        account -- An Account object.
        """
        return TwitterAccountFetcher(account)

    def _add_to_return_values(self, return_value):
        """Add return_value to the list in self.return_values."""
        self.return_values.append(return_value)

    def _set_accounts(self, screen_name=None):
        """Sets self.accounts to all Accounts or just one.

        Keyword arguments:
        screen_name -- of the one Account to get, or None for all Accounts.

        Raises:
        FetchError if passed a screen_name there is no Account for, or if none
            of the requested account(s) are marked as is_active.
        """
        if screen_name is None:
            accounts = Account.objects.filter(is_active=True)
            if (len(accounts) == 0):
                raise FetchError("No active Accounts were found to fetch.")
        else:
            try:
                accounts = [Account.objects.get(user__screen_name=screen_name)]
            except Account.DoesNotExist:
                raise FetchError("There is no Account in the database with a screen_name of '%s'" % screen_name)
            else:
                if accounts[0].is_active == False:
                    raise FetchError("The '%s' Account is marked as inactive." % screen_name)

        self.accounts = accounts


class VerifyFetcher(TwitterFetcher):
    """Calls verify_credentials for one/all Accounts.

    If an Account verifies OK, its Twitter User data is fetched and its User
    is created/updated in the databse.

    Usage (or omit screen_name for all Accounts):
        fetcher = VerifyFetcher(screen_name='aScreenName')
        results = fetcher.fetch()
    """

    def fetch(self):
        "No special arguments."
        return super().fetch()

    def _get_account_fetcher(self, account):
        return FetchVerify(account)


class UsersFetcher(TwitterFetcher):
    """Fetches data for a list of Twitter users, based on their ID.

    A screen_name for an Account is required, as we need to fetch the users
    using the API credentials from an Account.

    Usage:
        fetcher = UsersFetcher(screen_name='aScreenName')
        results = fetcher.fetch(user_ids=[123456,9876,])
    """

    def fetch(self, user_ids=[]):
        """
        Keyword arguments:
        user_ids -- A list of Twitter user IDs to fetch and store data for.
        """
        return super().fetch(user_ids=user_ids)

    def _get_account_fetcher(self, account):
        return FetchUsers(account)


class RecentTweetsFetcher(TwitterFetcher):
    """Fetches the most recent tweets for one/all Accounts.

    Will fetch tweets since the last fetch.

    Usage (or omit screen_name for all Accounts):
        fetcher = RecentTweetsFetcher(screen_name='aScreenName')
        results = fetcher.fetch(count=200) # or count='new'
    """

    def fetch(self, count='new'):
        """
        Keyword arguments:
        count -- Either 'new' (to fetch all tweets since the last time), or a
                number (eg, 100), to fetch that many of the most recent tweets,
                per Account.
        """
        return super().fetch(count=count)

    def _get_account_fetcher(self, account):
        return FetchTweetsRecent(account)


class FavoriteTweetsFetcher(TwitterFetcher):
    """Fetches tweets favorited by one/all Accounts, and associate each one
    with the Accounts' twitter User.

    Will fetch favorites since the last fetch.

    Usage (or omit screen_name for all Accounts):
        fetcher = FavoriteTweetsFetcher(screen_name='aScreenName')
        results = fetcher.fetch(count=200) # or count='new'
    """

    def fetch(self, count='new'):
        """
        Keyword arguments:
        count -- Either 'new' (to fetch all tweets since the last time), or a
                number (eg, 100), to fetch that many of the most recent
                favorite tweets, per Account.
        """
        return super().fetch(count=count)

    def _get_account_fetcher(self, account):
        return FetchTweetsFavorite(account)

