from . import FetchPhotosCommand
from ...fetch.multifetchers import RecentPhotosMultiAccountFetcher


class Command(FetchPhotosCommand):
    """Fetches photos from Flickr.

    For all accounts:
        ./manage.py fetch_flickr_photos --days=3
        ./manage.py fetch_flickr_photos --days=all

    For one account:
        ./manage.py fetch_flickr_photos --account=35034346050@N01 --days=3
        ./manage.py fetch_flickr_photos --account=35034346050@N01 --days=all

    """

    help = "Fetches recent or all photos for one or all Flickr Accounts"

    days_help = 'Fetches the most recent or all Photos, eg "3" or "all".'

    def fetch_photos(self, nsid, days):
        return RecentPhotosMultiAccountFetcher(nsid=nsid).fetch(days=days)

