from . import FetchPhotosCommand
from ...fetch.multifetchers import RecentPhotosMultiAccountFetcher


class Command(FetchPhotosCommand):
    """Fetches photos from Flickr.

    For all accounts:
        ./manage.py fetch_flickr_photos --days=3
        ./manage.py fetch_flickr_photos --days=all
        ./manage.py fetch_flickr_photos --range=2001-01-17,2003-11-10

    For one account:
        ./manage.py fetch_flickr_photos --account=35034346050@N01 --days=3
        ./manage.py fetch_flickr_photos --account=35034346050@N01 --days=all
        ./manage.py fetch_flickr_photos --account=35034346050@N01 --range=2001-01-17,2003-11-10
    """

    help = "Fetches recent or all photos for one or all Flickr Accounts"

    days_help = 'Fetches the most recent or all Photos, eg "3" or "all".'

    range_help = "Fetch photos taken between a range of dates in YYYY-MM-DD,YYYY-MM-DD format. Mutually exclusive with --days"

    def fetch_photos(self, nsid, days, range):
        return RecentPhotosMultiAccountFetcher(nsid=nsid).fetch(days=days,range=range)
