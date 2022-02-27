from . import FetchPhotosCommand
from ...fetch.multifetchers import RecentPhotosMultiAccountFetcher


class Command(FetchPhotosCommand):
    """Fetches photos from Flickr.

    For all accounts:
        ./manage.py fetch_flickr_photos --days=3
        ./manage.py fetch_flickr_photos --days=all
        ./manage.py fetch_flickr_photos --start=2001-01-17
        ./manage.py fetch_flickr_photos --end=2003-11-10
        ./manage.py fetch_flickr_photos --start=2001-01-17 --end=2003-11-10

    For one account:
        ./manage.py fetch_flickr_photos --account=35034346050@N01 --days=3
        ./manage.py fetch_flickr_photos --account=35034346050@N01 --days=all
        ./manage.py fetch_flickr_photos --account=35034346050@N01
            --start=2001-01-17 --end=2003-11-10
    """

    help = "Fetches recent or all photos for one or all Flickr Accounts"

    days_help = 'Fetches the most recent or all Photos, eg "3" or "all".'

    start_help = (
        "Fetch photos taken on or after a date in YYYY-MM-DD format. "
        "Cannot be used with --days, can be combined with --end."
    )

    end_help = (
        "Fetch photos on or before a date in YYYY-MM-DD format. "
        "Cannot be used with --days, can be combined with --start."
    )

    def fetch_photos(self, nsid, days=None, start=None, end=None):
        return RecentPhotosMultiAccountFetcher(nsid=nsid).fetch(
            days=days, start=start, end=end
        )
