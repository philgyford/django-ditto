from . import FetchError
from .fetch import (
    Fetch,
    FetchFiles,
    FetchTweetsRecent,
    FetchTweetsFavorite,
    FetchTweets,
    FetchUsers,
    FetchVerify,
)
from ..models import Account


# The classes to call to fetch data from the API to create/update objects.
# Each one can fetch a kind of thing for ONE OR MORE Accounts.
#
# They call the classes in fetch.fetch.* to do the actual API calling.
#
# In general (FilesFetcher excepted), use them something like this:
#
#   fetcher = RecentTweetsFetcher(screen_name='philgyford')
#   results = fetcher.fetch(count=20)

# CLASSES HERE:
#
# TwitterFetcher
#   VerifyFetcher
#   UsersFetcher
#   TweetsFetcher
#   RecentTweetsFetcher
#   FavoriteTweetsFetcher
# FilesFetcher


class TwitterFetcher(object):
    """Parent class for children that will call the Twitter API to fetch data
    for one or several Accounts.

    Use like:
        fetcher = ChildTwitterFetcher(screen_name='philgyford')
        results = fetcher.fetch()

    Or, for all accounts:
        fetcher = ChildTwitterFetcher()
        results = fetcher.fetch()

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

    def fetch(self, **kwargs):
        """Fetch data for one or more Accounts.

        Returns:
        A list of dicts, one dict per Account, containing data about
        success/failure.
        """
        for account in self.accounts:
            accountFetcher = self._get_account_fetcher(account)
            return_value = accountFetcher.fetch(**kwargs)
            self._add_to_return_values(return_value)

        return self.return_values

    def _get_account_fetcher(self, account):
        """Should be changed for each child class.
        Should return an instance of a child of Fetch().

        Keyword arguments:
        account -- An Account object.
        """
        return Fetch(account)

    def _add_to_return_values(self, return_value):
        """Add return_value to the list in self.return_values."""
        self.return_values.append(return_value)

    def _set_accounts(self, screen_name=None):
        """Sets self.accounts to all Accounts or just one.

        Keyword arguments:
        screen_name -- of the one Account to get, or None for all Accounts.

        Raises:
        FetchError if passed a screen_name there is no Account for, or if none
            of the requested account(s) are marked as is_active.
        """
        if screen_name is None:
            accounts = Account.objects.filter(is_active=True)
            if len(accounts) == 0:
                raise FetchError("No active Accounts were found to fetch.")
        else:
            try:
                accounts = [Account.objects.get(user__screen_name=screen_name)]
            except Account.DoesNotExist:
                raise FetchError(
                    "There is no Account in the database with a screen_name of '%s'"
                    % screen_name
                )
            else:
                if accounts[0].is_active is False:
                    raise FetchError(
                        "The '%s' Account is marked as inactive." % screen_name
                    )

        self.accounts = accounts


class VerifyFetcher(TwitterFetcher):
    """Calls verify_credentials for one/all Accounts.

    If an Account verifies OK, its Twitter User data is fetched and its User
    is created/updated in the databse.

    Usage (or omit screen_name for all Accounts):
        fetcher = VerifyFetcher(screen_name='aScreenName')
        results = fetcher.fetch()
    """

    def fetch(self):
        "No special arguments."
        return super().fetch()

    def _get_account_fetcher(self, account):
        return FetchVerify(account)


class UsersFetcher(TwitterFetcher):
    """Fetches data for a list of Twitter users, based on their ID.

    A screen_name for an Account is required, as we need to fetch the users
    using the API credentials from an Account.

    Usage:
        fetcher = UsersFetcher(screen_name='aScreenName')
        results = fetcher.fetch(ids=[123456,9876,])
    """

    def fetch(self, ids=[]):
        """
        Keyword arguments:
        ids -- A list of Twitter user IDs to fetch and store data for.
        """
        return super().fetch(ids=ids)

    def _get_account_fetcher(self, account):
        return FetchUsers(account)


class TweetsFetcher(TwitterFetcher):
    """Fetches data for a list of Tweets, based on their ID.

    A screen_name for an Account is required, as we need to fetch the Tweets
    using the API credentials from an Account.

    Usage:
        fetcher = TweetFetcher(screen_name='aScreenName')
        results = fetcher.fetch(ids=[123456,9876,])
    """

    def fetch(self, ids=[]):
        """
        Keyword arguments:
        ids -- A list of Twitter Tweet IDs to fetch and store data for.
        """
        return super().fetch(ids=ids)

    def _get_account_fetcher(self, account):
        return FetchTweets(account)


class RecentTweetsFetcher(TwitterFetcher):
    """Fetches the most recent tweets for one/all Accounts.

    Will fetch tweets since the last fetch.

    Usage (or omit screen_name for all Accounts):
        fetcher = RecentTweetsFetcher(screen_name='aScreenName')
        results = fetcher.fetch(count=200) # or count='new'
    """

    def fetch(self, count="new"):
        """
        Keyword arguments:
        count -- Either 'new' (to fetch all tweets since the last time), or a
                number (eg, 100), to fetch that many of the most recent tweets,
                per Account.
        """
        return super().fetch(count=count)

    def _get_account_fetcher(self, account):
        return FetchTweetsRecent(account)


class FavoriteTweetsFetcher(TwitterFetcher):
    """Fetches tweets favorited by one/all Accounts, and associate each one
    with the Accounts' twitter User.

    Will fetch favorites since the last fetch.

    Usage (or omit screen_name for all Accounts):
        fetcher = FavoriteTweetsFetcher(screen_name='aScreenName')
        results = fetcher.fetch(count=200) # or count='new'
    """

    def fetch(self, count="new"):
        """
        Keyword arguments:
        count -- Either 'new' (to fetch all tweets since the last time), or a
                number (eg, 100), to fetch that many of the most recent
                favorite tweets, per Account.
        """
        return super().fetch(count=count)

    def _get_account_fetcher(self, account):
        return FetchTweetsFavorite(account)


class FilesFetcher(object):
    """
    Use like:
        fetcher = FilesFetcher()
        results = fetcher.fetch()
    or:
        results = fetcher.fetch(fetch_all=True)

    Doesn't do much - simply to preserve a similar interface to the other
    *Fetcher() classes that use the API and Accounts.
    """

    def __init__(self):
        self.return_values = []

    def fetch(self, fetch_all=False):
        results = FetchFiles().fetch(fetch_all=fetch_all)

        # Return a list to behave similar to the other *Fetcher() classes that
        # can deal with multiple Accounts.
        return [results]
