from . import UpdateTwitterCommand
from ...fetch.fetchers import TweetsFetcher


class Command(UpdateTwitterCommand):
    """Fetches data for all Twitter Tweets in the DB, updating their info.

    Specify an account to use its API credentials:
    ./manage.py update_twitter_tweets --account=philgyford
    """

    help = "Fetches the latest data about each Twitter Tweet"

    singular_noun = 'Tweet'
    plural_noun = 'Tweets'

    def fetch(self, screen_name):
        return TweetsFetcher(screen_name=screen_name).fetch()

