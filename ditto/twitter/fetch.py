# coding: utf-8
import datetime
import json
import pytz

from twython import Twython, TwythonError

from .models import Account, Tweet, User


# CLASSES HERE:
#
# FetchError
#
# TwitterItemMixin
#   TweetMixin
#   UserMixin
#
# FetchForAccount
#   VerifyForAccount
#   RecentTweetsForAccount
#   FavoriteTweetsForAccount
#
# TwitterFetcher
#   VerifyFetcher
#   RecentTweetsFetcher
#   FavoriteTweetsFetcher
#
# UserFetcher
#
#
# The *Fetcher classes are the ones that should be used externally, like:
#
#   fetcher = RecentTweetsFetcher(screen_name='philgyford')
#   fetcher.fetch()


class FetchError(Exception):
    pass


class TwitterItemMixin(object):

    def __init__(self, *args, **kwargs):
        super(TwitterItemMixin, self).__init__(*args, **kwargs)

    def _api_time_to_datetime(self, api_time, time_format='%a %b %d %H:%M:%S +0000 %Y'):
        """Change a text datetime from the API to a datetime with timezone.
        api_time is a string like 'Wed Nov 15 16:55:59 +0000 2006'.
        """
        return datetime.datetime.strptime(api_time, time_format).replace(
                                                            tzinfo=pytz.utc)


class TweetMixin(TwitterItemMixin):
    """Provides a method for creating/updating a Tweet using data from the API.
    Also used by ingest.TweetIngester()
    """

    def __init__(self, *args, **kwargs):
        super(TweetMixin, self).__init__(*args, **kwargs)

    def save_tweet(self, tweet, fetch_time, user):
        """Takes a dict of tweet data from the API and creates or updates a
        Tweet object.

        Keyword arguments:
        tweet -- The tweet data.
        fetch_time -- A datetime.
        user -- A User object for whichever User posted this tweet.

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

        defaults = {
            'fetch_time':       fetch_time,
            'raw':              raw_json,
            'user':             user,
            'created_at':       created_at,
            'permalink':        'https://twitter.com/%s/status/%s' % (
                                            user.screen_name, tweet['id']),
            'title':            tweet['text'].replace('\n', ' ').replace('\r', ' '),
            'summary':          tweet['text'],
            'text':             tweet['text'],
            'twitter_id':       tweet['id'],
            'source':           tweet['source']
        }

        if user.is_private:
            defaults['is_private'] = True
        else:
            defaults['is_private'] = False

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

        tweet_obj, created = Tweet.objects.update_or_create(
                twitter_id=tweet['id'],
                defaults=defaults
            )
        return tweet_obj


class UserMixin(TwitterItemMixin):
    "Provides a method for creating/updating a User using data from the API."

    def __init__(self, *args, **kwargs):
        super(UserMixin, self).__init__(*args, **kwargs)

    def save_user(self, user, fetch_time, extra={}):
        """With Twitter user data from the API, it creates or updates the User
        and returns the User object.

        Keyword arguments:
        user -- A dict of the data about a user from the API's JSON.
        fetch_time -- A datetime.

        Returns the User object.
        """
        raw_json = json.dumps(user)

        # If there's a URL it will be a t.co shortened one.
        # So we go through the entities to find its expanded version.
        if user['url']:
            user_url = user['url']
            if 'url' in user['entities'] and 'urls' in user['entities']['url']:
                for url in user['entities']['url']['urls']:
                    if url['url'] == user['url']:
                        user_url = url['expanded_url']
        else:
            user_url = ''

        user_obj, created = User.objects.update_or_create(
            twitter_id=user['id'],
            defaults={
                'fetch_time': fetch_time,
                'raw': raw_json,
                'screen_name': user['screen_name'],
                'name': user['name'],
                'url': user_url,
                'is_private': user['protected'],
                'is_verified': user['verified'],
                'created_at': self._api_time_to_datetime(user['created_at']),
                'description': user['description'] if user['description'] else '',
                'location': user['location'] if user['location'] else '',
                'time_zone': user['time_zone'] if user['time_zone'] else '',
                'profile_image_url': user['profile_image_url'],
                'profile_image_url_https': user['profile_image_url_https'],
                # Note favorites / favourites:
                'favorites_count': user['favourites_count'],
                'followers_count': user['followers_count'],
                'friends_count': user['friends_count'],
                'listed_count': user['listed_count'],
                'statuses_count': user['statuses_count'],
            }
        )

        return user_obj


class FetchForAccount(object):
    """Parent class for children that will call the Twitter API to fetch data
    for a single Account.
    Children should define their own methods for:
        _call_api()
        _save_results()
    and optionally:
        _post_save()

    Use it like:
        account = Account.objects.get(pk=1)
        accountFetcher = RecentTweetsForAccount(account)
        result = accountFetcher.fetch()
    """

    def __init__(self, account):

        self.account = account

        # Will be the Twython object for calling the Twitter API.
        self.api = None

        # Will be the results fetched from the API via Twython.
        self.results = []

        # Will be a list of all the Users/Tweets/etc created/updated:
        self.objects = []

        self.fetch_time = datetime.datetime.utcnow().replace(tzinfo=pytz.utc)

        # What we'll return for each account:
        self.return_value = {}

    def fetch(self):
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

            try:
                self._call_api()
            except TwythonError as e:
                self.return_value['success'] = False
                self.return_value['message'] = 'Error when calling API: %s' % e
            else:
                if (len(self.results) > 0):
                    self._save_results()
                    self._post_save()
                self.return_value['success'] = True
                self.return_value['fetched'] = len(self.results)
        else:
            self.return_value['success'] = False
            self.return_value['message'] = 'Account has no API credentials'

        return self.return_value

    def _call_api(self):
        """Define in child classes.
        Should call self.api.a_function_name() and set self.results with the
        results.
        """
        pass

    def _post_save(self):
        """Can optionally be defined in child classes.
        Do any extra things that need to be done after saving the data.
        """
        pass

    def _save_results(self):
        """Define in child classes.
        Should go through self._results() and, probably, call
        self.save_tweet() or self.save_user() for each one.
        """
        self.objects = []


class VerifyForAccount(UserMixin, FetchForAccount):
    """For verifying an Account's API credentials, but ALSO fetches the user
    data for that single Account.
    """

    def __init__(self, account):
        super(VerifyForAccount, self).__init__(account)

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


class RecentTweetsForAccount(TweetMixin, UserMixin, FetchForAccount):
    """For fetching recent tweets by a single Account."""

    def __init__(self, *args, **kwargs):
        super(RecentTweetsForAccount, self).__init__(*args, **kwargs)

    def _call_api(self):
        """Sets self.results to be the timeline of tweets for this Account."""
        # account.last_recent_id might be None, in which case it's not used in
        # the API call:
        self.results = self.api.get_user_timeline(
                                user_id=self.account.user.twitter_id,
                                include_rts=True,
                                since_id=self.account.last_recent_id)

    def _post_save(self):
        """Set the last_recent_id of our Account to the most recent Tweet we
        fetched.
        """
        self.account.last_recent_id = self.results[0]['id']
        self.account.save()

    def _save_results(self):
        """Takes the list of tweet data from the API and creates or updates the
        Tweet objects and the posters' User objects.
        Adds each new Tweet object to self.objects.
        """
        for tweet in self.results:
            user = self.save_user(tweet['user'], self.fetch_time)
            tw = self.save_tweet(tweet, self.fetch_time, user)
            self.objects.append(tw)


class FavoriteTweetsForAccount(TweetMixin, UserMixin, FetchForAccount):
    """For fetching tweets favorited by a single Account."""

    def __init__(self, *args, **kwargs):
        super(FavoriteTweetsForAccount, self).__init__(*args, **kwargs)

    def _call_api(self):
        """Sets self.results to be recent tweets favorited by this Account."""
        # account.last_favorite_id might be None, in which case it's not used in
        # the API call:
        self.results = self.api.get_favorites(
                                user_id=self.account.user.twitter_id,
                                since_id=self.account.last_favorite_id)

    def _post_save(self):
        """Set the last_favorite_id of our Account to the most recent Tweet we
        fetched.
        """
        self.account.last_favorite_id = self.results[0]['id']
        self.account.save()

    def _save_results(self):
        """Takes the list of tweet data from the API and creates or updates the
        Tweet objects and the posters' User objects.
        Adds each new Tweet object to self.objects.

        TODO: Associate each favorited tweet with self.account.
        """
        for tweet in self.results:
            user = self.save_user(tweet['user'], self.fetch_time)
            tw = self.save_tweet(tweet, self.fetch_time, user)
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

    def fetch(self):
        """Fetch data for one or more Accounts.

        Returns:
        A list of dicts, one dict per Account, containing data about
        success/failure.
        """
        for account in self.accounts:
            accountFetcher = self._get_account_fetcher(account)
            return_value = accountFetcher.fetch()
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
        FetchError if passed a screen_name there is no Account for.
        """
        if screen_name is None:
            accounts = Account.objects.all()
        else:
            try:
                accounts = [Account.objects.get(user__screen_name=screen_name)]
            except Account.DoesNotExist:
                raise FetchError("There is no Account in the database with a screen_name of '%s'" % screen_name)

        self.accounts = accounts


class VerifyFetcher(TwitterFetcher):
    """Calls verify_credentials for one/all Accounts.

    If an Account verifies OK, its Twitter User data is fetched and its User
    is created/updated in the databse.

    Usage (or omit screen_name for all Accounts):
        fetcher = VerifyFetcher(screen_name='aScreenName')
        results = fetcher.fetch()
    """

    def _get_account_fetcher(self, account):
        return VerifyForAccount(account)


class RecentTweetsFetcher(TwitterFetcher):
    """Fetches the most recent tweets for one/all Accounts.

    Will fetch tweets since the last fetch.

    Usage (or omit screen_name for all Accounts):
        fetcher = RecentTweetsFetcher(screen_name='aScreenName')
        results = fetcher.fetch()
    """

    def _get_account_fetcher(self, account):
        return RecentTweetsForAccount(account)


class FavoriteTweetsFetcher(TwitterFetcher):
    """Fetches tweets favorited by one/all Accounts, and associate each one
    with the Accounts' twitter User.

    Will fetch favorites since the last fetch.

    Usage (or omit screen_name for all Accounts):
        fetcher = FavoriteTweetsFetcher(screen_name='aScreenName')
        results = fetcher.fetch()
    """

    def _get_account_fetcher(self, account):
        return FavoriteTweetsForAccount(account)

