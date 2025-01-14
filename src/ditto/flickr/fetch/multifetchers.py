from ditto.flickr.models import Account, User

from . import FetchError
from .fetchers import PhotosetsFetcher, RecentPhotosFetcher
from .filesfetchers import OriginalFilesFetcher

# Classes for fetching data from the API for ONE OR MORE Accounts.
# These are wrappers for other classes which do the heavy lifting.
# These call those Fetcher classes for each Account, and pass the results
# back.

# CLASSES HERE:
#
# MultiAccountFetcher
#   RecentPhotosMultiAccountFetcher
#   PhotosetsMultiAccountFetcher
#   OriginalFilesMultiAccountFetcher


class MultiAccountFetcher:
    """Parent class for fetching things from Flickr for ALL or ONE Account(s).

    Its child classes are useful for:
        * Fetching from all accounts.
        * Fetching from a single account with identical interface and response
          as when fetching from all accounts (otherwise you could use the
          single account fetcher, like RecentPhotosFetcher()).
        * Fetching from a single account when you only have the user's NSID.

    Use something like:

        results = ChildMultiAccountFetcher().fetch(foo=3)

    or:

        results = ChildMultiAccountFetcher(nsid='35034346050@N01').fetch(foo=3)
    """

    # Will be a list of Account objects.
    accounts = []

    def __init__(self, nsid=None):
        """Gets all of the Accounts that child classes will loop through.

        nsid -- If nsid is set, we use only the Account associated with the
                User with that nsid (if it's active). Otherwise, we use all
                active Accounts.
        """
        self.return_value = []

        if nsid is None:
            # Get all active Accounts.
            self.accounts = list(Account.objects.filter(is_active=True))
            if len(self.accounts) == 0:
                msg = "No active Accounts were found to fetch."
                raise FetchError(msg)
        else:
            # Find the Account associated with nsid.
            try:
                user = User.objects.get(nsid=nsid)
            except User.DoesNotExist as err:
                msg = f"There is no User with the NSID '{nsid}'"
                raise FetchError(msg) from err
            try:
                account = Account.objects.get(user=user)
            except Account.DoesNotExist as err:
                msg = "There is no Account associated with the User with NSID '{nsid}'"
                raise FetchError(msg) from err
            if account.is_active is False:
                msg = (
                    "The Account associated with the User with NSID "
                    f"'{nsid}' is marked as inactive."
                )
                raise FetchError(msg)

            self.accounts = [account]
        return super().__init__()

    def fetch(self, **kwargs):
        msg = "Subclasess of MultiAccountFetcher should define their own fetch()."
        raise FetchError(msg)


class RecentPhotosMultiAccountFetcher(MultiAccountFetcher):
    """For fetching recent photos for ALL or ONE account(s).

    Usage:

        results = RecentPhotosMultiAccountFetcher().fetch(days=7)

    Or omit the `days` to fetch ALL photos for ALL accounts.

    results will be a list of dicts containing info about what was fetched (or
    went wrong) for each account.
    """

    def fetch(self, days=None, start=None, end=None):
        for account in self.accounts:
            self.return_value.append(
                RecentPhotosFetcher(account).fetch(days=days, start=start, end=end)
            )

        return self.return_value


class PhotosetsMultiAccountFetcher(MultiAccountFetcher):
    """For fetching ALL photosets for ALL or ONE account(s).

    Usage:

        results = PhotosetsMultiAccountFetcher().fetch()

    results will be a list of dicts containing info about what was fetched (or
    went wrong) for each account.
    """

    def fetch(self):
        for account in self.accounts:
            self.return_value.append(PhotosetsFetcher(account).fetch())

        return self.return_value


class OriginalFilesMultiAccountFetcher(MultiAccountFetcher):
    """For fetching original photo files for ALL or ONE account(s).

    Usage:

        results = OriginalFilesMultiAccountFetcher().fetch(fetch_all=True)

    results will be a list of dicts containing info about what was fetched(or
    went wrong) for each account.
    """

    def fetch(self, *, fetch_all=False):
        for account in self.accounts:
            self.return_value.append(
                OriginalFilesFetcher(account).fetch(fetch_all=fetch_all)
            )

        return self.return_value
