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
# The *Fetcher classes are the ones that should be used externally, like:
#
#   fetcher = RecentTweetsFetcher(screen_name='philgyford')
#   fetcher.fetch()


class FetchError(Exception):
    pass


class TwitterItemMixin(object):
    def _api_time_to_datetime(self, api_time):
        """Change a text datetime from the API to a datetime with timezone.
        api_time is a string like 'Wed Nov 15 16:55:59 +0000 2006'.
        """
        return datetime.datetime.strptime(
                                        api_time,
                                        '%a %b %d %H:%M:%S +0000 %Y'
                                    ).replace(tzinfo=pytz.utc)


class TweetMixin(TwitterItemMixin):
    """Provides a method for creating/updating a Tweet using data from the API.
    
    Expects the class to have a self.fetch_time.
    """

    def save_tweet(self, result, extra={}):
        """Takes a dict of tweet data from the API and creates or updates a
        Tweet object.

        Keyword arguments:
        result -- The tweet data.
        extra['user'] -- A User object for whichever User posted this tweet.

        Returns:
        The Tweet object that was created or updated.
        """
        user = extra['user']

        raw_json = json.dumps(result)

        defaults = {
            'fetch_time':       self.fetch_time,
            'raw':              raw_json,
            'user':             user,
            'permalink':        'https://twitter.com/%s/status/%s' % (
                                            user.screen_name, result['id']),
            'title':            result['text'].replace('\n', ' ').replace('\r', ' '),
            'summary':          result['text'],
            'text':             result['text'],
            'twitter_id':       result['id'],
            'created_at':       self._api_time_to_datetime(result['created_at']),
            'favorite_count':   result['favorite_count'],
            'retweet_count':    result['retweet_count'],
            'language':         result['lang'],
            'source':           result['source']
        }

        if user.is_private:
            result['is_private'] = True
        else:
            result['is_private'] = False

        if result['coordinates'] and 'type' in result['coordinates']:
            if result['coordinates']['type'] == 'Point':
                defaults['latitude'] = result['coordinates']['coordinates'][1]
                defaults['longitude'] = result['coordinates']['coordinates'][0]
            # TODO: Handle Polygons?

        if result['in_reply_to_screen_name']:
            defaults['in_reply_to_screen_name'] =  result['in_reply_to_screen_name']
            defaults['in_reply_to_status_id'] = result['in_reply_to_status_id']
            defaults['in_reply_to_user_id'] = result['in_reply_to_user_id']

        if result['place'] is not None:
            if 'attributes' in result['place'] and 'street_address' in result['place']['attributes']:
                defaults['place_attribute_street_address'] = result['place']['attributes']['street_address']
            if 'full_name' in result['place']:
                defaults['place_full_name'] = result['place']['full_name']
            if 'country' in result['place']:
                defaults['place_country'] = result['place']['country']

        if 'quoted_status_id' in result:
            defaults['quoted_status_id'] = result['quoted_status_id']

        tweet, created = Tweet.objects.update_or_create(
                twitter_id=result['id'],
                defaults=defaults
            )
        return tweet


class UserMixin(TwitterItemMixin):
    """Provides a method for creating/updating a User using data from the API.
    
    Expects the class to have a self.fetch_time.
    """

    def save_user(self, result, extra={}):
        """With Twitter user data from the API, it creates or updates the User
        and returns the User object.

        Keyword arguments:
        result -- A dict of the data about a user from the API's JSON.

        Returns the User object.
        """
        raw_json = json.dumps(result)

        user, created = User.objects.update_or_create(
            twitter_id=result['id'],
            defaults={
                'fetch_time': self.fetch_time,
                'raw': raw_json,
                'screen_name': result['screen_name'],
                'name': result['name'],
                'url': result['url'] if result['url'] else '',
                'is_private': result['protected'],
                'is_verified': result['verified'],
                'created_at': self._api_time_to_datetime(result['created_at']),
                'description': result['description'] if result['description'] else '',
                'location': result['location'] if result['location'] else '',
                'time_zone': result['time_zone'] if result['time_zone'] else '',
                'profile_image_url': result['profile_image_url'],
                'profile_image_url_https': result['profile_image_url_https'],
                # Note favorites / favourites:
                'favorites_count': result['favourites_count'],
                'followers_count': result['followers_count'],
                'friends_count': result['friends_count'],
                'listed_count': result['listed_count'],
                'statuses_count': result['statuses_count'],
            }
        )

        return user


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
        user = self.save_user(self.results)
        self.objects = [user]


class RecentTweetsForAccount(TweetMixin, UserMixin, FetchForAccount):
    """For fetching recent tweets by a single Account."""

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
            user = self.save_user(tweet['user'])
            tw = self.save_tweet(tweet, extra={'user': user})
            self.objects.append(tw)

class FavoriteTweetsForAccount(TweetMixin, UserMixin, FetchForAccount):
    """For fetching tweets favorited by a single Account."""

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
            user = self.save_user(tweet['user'])
            tw = self.save_tweet(tweet, extra={'user': user})
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
    def _get_account_fetcher(self, account):
        return VerifyForAccount(account)


class RecentTweetsFetcher(TwitterFetcher):
    def _get_account_fetcher(self, account):
        return RecentTweetsForAccount(account)


class FavoriteTweetsFetcher(TwitterFetcher):
    def _get_account_fetcher(self, account):
        return FavoriteTweetsForAccount(account)

