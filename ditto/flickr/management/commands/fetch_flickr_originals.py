from django.core.management.base import BaseCommand, CommandError

from . import FetchCommand
from ...fetch.multifetchers import OriginalFilesMultiAccountFetcher


class Command(FetchCommand):
    """Fetches original photo files from Flickr.

    For all accounts:
        ./manage.py fetch_flickr_originals
        ./manage.py fetch_flickr_originals --all

    For one account:
        ./manage.py fetch_flickr_originals --account=35034346050@N01
        ./manage.py fetch_flickr_originals --account=35034346050@N01 --all
    """

    help = "Fetches the original image files for one or all Flickr Accounts"

    singular_noun = 'File'
    plural_noun = 'Files'

    def add_arguments(self, parser):
        super().add_arguments(parser)

        parser.add_argument(
            '--all',
            action='store_true',
            default=False,
            help="Fetch ALL files, even if they've been downloaded before. Otherwise, only fetch files that haven't already been downloaded."
        )

    def handle(self, *args, **options):
        # We might be fetching for a specific account or all (None).
        nsid = options['account'] if options['account'] else None;

        results = self.fetch_files(nsid, options['all'])
        self.output_results(results, options.get('verbosity', 1))

    def fetch_files(self, nsid, fetch_all=False):
        return OriginalFilesMultiAccountFetcher(nsid=nsid).fetch(
                                                        fetch_all=fetch_all)

