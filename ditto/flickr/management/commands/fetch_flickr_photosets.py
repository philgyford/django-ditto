from ._fetch_photos import FetchPhotosCommand
from ...fetch import PhotosetsFetcher, PhotosetsMultiAccountFetcher


class Command(FetchPhotosCommand):
    """Fetches photosets from Flickr

    For all accounts:
        ./manage.py fetch_flickr_photosets

    For one account:
        ./manage.py fetch_flickr_photosets --account=35034346050@N01

    """

    help = "Fetches all photosets for one or all Flickr Accounts (photo data must already be fetched)."

    def add_arguments(self, parser):
        parser.add_argument(
            '--account',
            action='store',
            default=False,
            help='The NSID of the Flickr User associated with the one Account to fetch for.',
        )

    def handle(self, *args, **options):
        # We might be fetching for a specific account or all (None).
        nsid = options['account'] if options['account'] else None;

        results = PhotosetsMultiAccountFetcher(nsid=nsid).fetch()

        for result in results:
            if result['success']:
                noun = 'Photoset' if result['fetched'] == 1 else 'Photosets'
                self.stdout.write('%s: Fetched %s %s' % (
                                result['account'], result['fetched'], noun))
            else:
                self.stderr.write('%s: Failed to fetch Photosets: %s' % (
                                        result['account'], result['message']))

