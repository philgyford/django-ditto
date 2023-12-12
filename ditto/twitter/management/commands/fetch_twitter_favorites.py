from ditto.twitter.fetch.fetchers import FavoriteTweetsFetcher

from . import FetchTwitterCommand


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

    def fetch_tweets(self, screen_name, count):
        return FavoriteTweetsFetcher(screen_name=screen_name).fetch(count=count)
