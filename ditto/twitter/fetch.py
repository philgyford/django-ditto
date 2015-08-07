# coding: utf-8

from .models import Account, Tweet


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
        pass

    def fetch_favorites(self, num=10, screen_name=None):
        """Fetches the most recent Favorites for all or one Accounts.
        Creates/updates the Tweet objects.

        Keyword arguments:
        num -- the number of most recent Tweets to fetch.
        screen_name -- of the one Account to fetch for, or None for all.
        """
        pass

