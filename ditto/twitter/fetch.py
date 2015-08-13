# coding: utf-8
import datetime
import json
import pytz

from twython import Twython, TwythonError

from .models import Account, Tweet, User


class FetchTweets(object):

    def fetch_recent(self, num=None, screen_name=None):
        """Fetches the most recent Tweets for all or one Accounts.
        Creates/updates the Tweet objects.

        Keyword arguments:
        num -- the number of most recent Tweets to fetch, or None to fetch
                all Tweets since last time we fetched them.
        screen_name -- of the one Account to fetch for, or None for all
                Accounts.
        """
        accounts = self._get_accounts(screen_name)

        pass

    def fetch_favorites(self, num=10, screen_name=None):
        """Fetches the most recent Favorites for all or one Accounts.
        Creates/updates the Tweet objects.

        Keyword arguments:
        num -- the number of most recent Tweets to fetch.
        screen_name -- of the one Account to fetch for, or None for all.
        """
        pass

    def _get_accounts(self, screen_name):
        """Returns either all Accounts or just one, indicated by screen_name.
        Or, if there is no account with screen_name, an error string.

        Keyword arguments:
        screen_name -- of the one Account to get, or None for all Accounts.
        """
        if screen_name is None:
            accounts = Account.objects.all()
        else:
            try:
                accounts = [ Account.objects.get(screen_name=screen_name) ]
            except Account.DoesNotExist:
                return "There is no Account in the database with a screen_name of '%s'" % screen_name

        return accounts


class FetchUsers(object):

    def fetch_for_account(self, account):
        """Fetches the Twitter user details for an Account object, creating/
        updating the User object as necessary.
        Does not save the account with the new User.

        Keyword arguments:
        account -- An Account object.

        Returns either the User object or an error string.
        """
        twitter = Twython(account.consumer_key, account.consumer_secret,
                            account.access_token, account.access_token_secret)
        fetch_time = datetime.datetime.utcnow().replace(tzinfo=pytz.utc)

        try:
            api_user = twitter.verify_credentials()
            return self._save_user(api_user, fetch_time)
        except TwythonError as e:
            return 'Something went wrong when verifying credentials: %s' % e


    def _save_user(self, api_user, fetch_time):
        """With Twitter user data from the API, it creates or updates the User
        and returns the User object.

        Keyword arguments:
        api_user -- A dict of the data about a user from the API's JSON.
        fetch_time -- A UTC datetime representing when this data was fetched.

        Returns the User object.
        """

        raw_json = json.dumps(api_user)

        user, created = User.objects.update_or_create(
            twitter_id=api_user['id'],
            defaults={
                'fetch_time': fetch_time,
                'raw': raw_json,
                'screen_name': api_user['screen_name'],
                'name': api_user['name'],
                'url': api_user['url'],
                'is_private': api_user['protected'],
                'is_verified': api_user['verified'],
                # API's created_at is like 'Wed Nov 15 16:55:59 +0000 2006':
                'created_at': datetime.datetime.strptime(
                                                    api_user['created_at'],
                                                    '%a %b %d %H:%M:%S +0000 %Y'
                                                ).replace(tzinfo=pytz.utc),
                'description': api_user['description'],
                'location': api_user['location'],
                'time_zone': api_user['time_zone'],
                'profile_image_url': api_user['profile_image_url'],
                'profile_image_url_https': api_user['profile_image_url_https'],
                # Note favorites / favourites:
                'favorites_count': api_user['favourites_count'],
                'followers_count': api_user['followers_count'],
                'friends_count': api_user['friends_count'],
                'listed_count': api_user['listed_count'],
                'statuses_count': api_user['statuses_count'],
            }
        )

        return user

