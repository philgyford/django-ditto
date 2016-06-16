# coding: utf-8
from ....core.management.commands import DittoBaseCommand
from ...fetch.fetchers import FilesFetcher


class Command(DittoBaseCommand):
    """Fetches images and Animated GIFs' video files from Twitter.

    eg:
    ./manage.py fetch_twitter_files
    ./manage.py fetch_twitter_files --all

    """

    help = "Fetches images and Animated GIFs' video files from Twitter"

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
        results = FilesFetcher().fetch(fetch_all=options['all'])
        self.output_results(results, options.get('verbosity', 1))

