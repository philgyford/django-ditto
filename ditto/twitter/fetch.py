# coding: utf-8
import datetime
import json
import pytz

from twython import Twython, TwythonError

from .models import Account, Tweet, User


class FetchError(Exception):
    pass


class TwitterFetcher(object):

    def api_time_to_datetime(self, api_time):
        # API's created_at is like 'Wed Nov 15 16:55:59 +0000 2006':
        return datetime.datetime.strptime(api_time,
                                          '%a %b %d %H:%M:%S +0000 %Y'
                                        ).replace(tzinfo=pytz.utc)


class FetchTweets(TwitterFetcher):

    def fetch_recent(self, screen_name=None):
        """Fetches the most recent Tweets for all or one Accounts.
        Creates/updates the Tweet objects.

        Keyword arguments:
        screen_name -- of the one Account to fetch for, or None for all
                Accounts.

        Returns a list of dicts, one per Twitter account fetched.
        Each dict is like:
            {'account': 'screenname', 'success': True, 'fetched': 37}
        or:
            {'account': 'screenname', 'success': False, 'message': 'It broke'}

        Raises:
        FetchError if passed a screen_name there is no Account for.
        """
        accounts = self._get_accounts(screen_name)
        # Will collect the result info for each account:
        results = []

        for account in accounts:
            # What we'll return for each account:
            result = {'account': account.user.screen_name}
            if account.hasCredentials():
                api = Twython(
                            account.consumer_key, account.consumer_secret,
                            account.access_token, account.access_token_secret)

                try:
                    # account.last_recent_id might be None, in which case it's
                    # not used in the API call:
                    tweets = api.get_user_timeline(
                                            user_id=account.user.twitter_id,
                                            include_rts=True,
                                            since_id=account.last_recent_id)
                except TwythonError as e:
                    result['success'] = False
                    result['message'] = 'Error when calling API: %s' % e
                else:
                    if (len(tweets) > 0):
                        fetch_time = datetime.datetime.utcnow().replace(
                                                            tzinfo=pytz.utc)
                        self.save_tweets(tweets, fetch_time)
                        account.last_recent_id = tweets[0]['id']
                        account.save()
                    result['success'] = True
                    result['fetched'] = len(tweets)
            else:
                result['success'] = False
                result['message'] = 'Account has no API credentials'

            results.append(result)

        return results

    def fetch_favorites(self, screen_name=None):
        """Fetches the most recent Favorites for all or one Accounts.
        Creates/updates the Tweet objects.

        Keyword arguments:
        screen_name -- of the one Account to fetch for, or None for all.

        Raises:
        FetchError if passed a screen_name there is no Account for.
        """
        accounts = self._get_accounts(screen_name)
        # Will collect the result info for each account:
        results = []

        for account in accounts:
            # What we'll return for each account:
            result = {'account': account.user.screen_name}
            if account.hasCredentials():
                api = Twython(
                            account.consumer_key, account.consumer_secret,
                            account.access_token, account.access_token_secret)

                try:
                    tweets = api.get_favorites(
                                            user_id=account.user.twitter_id,
                                            since_id=account.last_favorite_id)
                except TwythonError as e:
                    result['success'] = False
                    result['message'] = 'Error when calling API: %s' % e
                else:
                    # TODO: Link Favorite to User.
                    if (len(tweets) > 0):
                        fetch_time = datetime.datetime.utcnow().replace(
                                                            tzinfo=pytz.utc)
                        self.save_tweets(tweets, fetch_time)
                        account.last_favorite_id = tweets[0]['id']
                        account.save()
                    result['success'] = True
                    result['fetched'] = len(tweets)
            else:
                result['success'] = False
                result['message'] = 'Account has no API credentials'

            results.append(result)

        return results


    def save_tweets(self, tweets, fetch_time):
        """Takes a list of tweet data from the API and creates or updates the
        Tweet objects and the posters' User objects.

        Keyword arguments:
        tweets -- The tweets' data.
        fetch_time -- datetime object for when this data was fetched.
        """
        for tweet in tweets:
            user = FetchUsers().save_user(tweet['user'], fetch_time)
            tw = self.save_tweet(tweet, user, fetch_time)

    def save_tweet(self, tweet, user, fetch_time):
        """Takes a dict of tweet data from the API and creates or updates a
        Tweet object.

        Keyword arguments:
        tweet -- The tweet data.
        user -- A User object for whichever User posted this tweet.
        fetch_time -- datetime object for when this data was fetched.

        Returns:
        The Tweet object.
        """

        raw_json = json.dumps(tweet)

        defaults = {
            'fetch_time':       fetch_time,
            'raw':              raw_json,
            'user':             user,
            'permalink':        'https://twitter.com/%s/status/%s' % (
                                                user.screen_name, tweet['id']),
            'title':            tweet['text'].replace('\n', ' ').replace('\r', ' '),
            'summary':          tweet['text'],
            'text':             tweet['text'],
            'twitter_id':       tweet['id'],
            'created_at':       self.api_time_to_datetime(tweet['created_at']),
            'favorite_count':   tweet['favorite_count'],
            'retweet_count':    tweet['retweet_count'],
            'language':         tweet['lang'],
            'source':           tweet['source']
        }

        if user.is_private:
            tweet['is_private'] = True
        else:
            tweet['is_private'] = False

        if tweet['coordinates'] and 'type' in tweet['coordinates']:
            if tweet['coordinates']['type'] == 'Point':
                defaults['latitude'] = tweet['coordinates']['coordinates'][1]
                defaults['longitude'] = tweet['coordinates']['coordinates'][0]
            # TODO: Handle Polygons?

        if tweet['in_reply_to_screen_name']:
            defaults['in_reply_to_screen_name'] =  tweet['in_reply_to_screen_name']
            defaults['in_reply_to_status_id'] = tweet['in_reply_to_status_id']
            defaults['in_reply_to_user_id'] = tweet['in_reply_to_user_id']

        if tweet['place'] is not None:
            if 'attributes' in tweet['place'] and 'street_address' in tweet['place']['attributes']:
                defaults['place_attribute_street_address'] = tweet['place']['attributes']['street_address']
            if 'full_name' in tweet['place']:
                defaults['place_full_name'] = tweet['place']['full_name']
            if 'country' in tweet['place']:
                defaults['place_country'] = tweet['place']['country']

        if 'quoted_status_id' in tweet:
            defaults['quoted_status_id'] = tweet['quoted_status_id']

        tw, created = Tweet.objects.update_or_create(
                twitter_id=tweet['id'],
                defaults=defaults
            )
        return tw

    def _get_accounts(self, screen_name=None):
        """Returns either all Accounts or just one, indicated by screen_name.

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

        return accounts


class FetchUsers(TwitterFetcher):

    def fetch_for_account(self, account):
        """Fetches the Twitter user details for an Account object, creating/
        updating the User object as necessary.
        Does not save the account with the new User.

        Keyword arguments:
        account -- An Account object.

        Returns either the User object or an error string.
        """
        api = Twython(account.consumer_key, account.consumer_secret,
                            account.access_token, account.access_token_secret)
        fetch_time = datetime.datetime.utcnow().replace(tzinfo=pytz.utc)

        try:
            api_user = api.verify_credentials()
        except TwythonError as e:
            return 'Something went wrong when verifying credentials: %s' % e
        else:
            return self.save_user(api_user, fetch_time)


    def save_user(self, api_user, fetch_time):
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
                'url': api_user['url'] if api_user['url'] else '',
                'is_private': api_user['protected'],
                'is_verified': api_user['verified'],
                'created_at': self.api_time_to_datetime(api_user['created_at']),
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

