# coding: utf-8
import argparse

from django.core.management.base import CommandError

from ._fetch_twitter import FetchTwitterCommand
from ...fetch import FavoriteTweetsFetcher


class Command(FetchTwitterCommand):
    """Fetches favorites from Twitter.

    Fetch recent tweets favorited by all accounts, since last time:
    ./manage.py fetch_twitter_likes --recent=new

    Fetch 100 most recent tweets favorited by all accounts:
    ./manage.py fetch_twitter_likes --recent=100

    Fetch recent tweets favorited by one account:
    ./manage.py fetch_twitter_likes --recent=new --account=philgyford
    """

    help = "Fetches recent liked Tweets from Twitter"

    recent_help = 'Fetch the most recent liked Tweets, eg "100" or "new".'

    def fetch_tweets(self, account, count):
        return FavoriteTweetsFetcher(screen_name=account).fetch(count=count)

