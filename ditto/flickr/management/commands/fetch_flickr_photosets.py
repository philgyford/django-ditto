from . import FetchCommand
from ...fetch.multifetchers import PhotosetsMultiAccountFetcher


class Command(FetchCommand):
    """Fetches photosets from Flickr

    For all accounts:
        ./manage.py fetch_flickr_photosets

    For one account:
        ./manage.py fetch_flickr_photosets --account=35034346050@N01
    """

    # What we're fetching:
    singular_noun = 'Photoset'
    plural_noun = 'Photosets'

    help = "Fetches all photosets for one or all Flickr Accounts (photo data must already be fetched)."

    def handle(self, *args, **options):
        # We might be fetching for a specific account or all (None).
        nsid = options['account'] if options['account'] else None;

        results = PhotosetsMultiAccountFetcher(nsid=nsid).fetch()

        self.output_results(results, options.get('verbosity', 1))
