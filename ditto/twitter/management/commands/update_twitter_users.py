from . import UpdateTwitterCommand
from ...fetch.fetchers import UsersFetcher


class Command(UpdateTwitterCommand):
    """Fetches data for all Twitter Users in the DB, updating their info.

    Specify an account to use its API credentials:
    ./manage.py update_twitter_users --account=philgyford
    """

    help = "Fetches the latest data about each Twitter user"

    singular_noun = 'User'
    plural_noun = 'Users'

    def fetch(self, screen_name):
        return UsersFetcher(screen_name=screen_name).fetch()

