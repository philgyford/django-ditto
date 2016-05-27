# coding: utf-8
from .import FetchTwitterCommand
from ...fetch.fetchers import RecentTweetsFetcher


class Command(FetchTwitterCommand):
    """Fetches tweets from Twitter.

    Fetch recent tweets since the last fetch, from all accounts:
    ./manage.py fetch_twitter_tweets --recent=new

    Fetch 100 most recent tweets, from all accounts:
    ./manage.py fetch_twitter_tweets --recent=100

    Fetch recent tweets since the last fetch, from one account:
    ./manage.py fetch_twitter_tweets --recent=new --account=philgyford
    """

    help = "Fetches recent Tweets from Twitter"

    recent_help = 'Fetches the most recent Tweets, eg "100" or "new".'

    def fetch_tweets(self, screen_name, count):
        return RecentTweetsFetcher(screen_name=screen_name).fetch(count=count)


