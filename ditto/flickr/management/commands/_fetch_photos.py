import argparse

from django.core.management.base import BaseCommand, CommandError

from ...models import Account, User


class FetchPhotosCommand(BaseCommand):

    # Child classes should supply some help text for the --days argument:
    recent_help = ""

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            action='store',
            default=False,
            help=self.days_help
        )
        parser.add_argument(
            '--account',
            action='store',
            default=False,
            help='The NSID of the Flickr User associated with the one Account to fetch for.',
        )

    def handle(self, *args, **options):

        # We might be fetching for a specific account or all (None).
        nsid = options['account'] if options['account'] else None;

        if options['days']:
            # Will be either 'all' or a number; make the number an int.
            if options['days'].isdigit():
                options['days'] = int(options['days'])
            elif options['days'] != 'all':
                raise CommandError("--days should be an integer or 'all'.")

            results = self.fetch_photos(nsid, options['days'])
            self.output_results(results)
        elif options['account']:
            raise CommandError("Specify --days as well as --account.")
        else:
            raise CommandError("Specify --days , eg --days=3 or --days=all.")

    def fetch_photos(self, nsid, days):
        """Child classes should override this method to call a method that
        fetches photos and returns results, eg:
            return RecentPhotosMultiAccountFetcher(nsid=nsid).fetch(days=days)
        """
        return {}

    def output_results(self, results):
        """results should be a list of dicts.

        Each dict is for one account.
        Each dict will look like either:

          { 'account': 'Phil Gyford',
            'success': True,
            'fetched': 200, # The number of Photos fetched
          }

        or:

          { 'account': 'Phil Gyford',
            'success': False,
            'message': 'There was an error fetching data because blah',
          }
        """
        for result in results:
            if result['success']:
                noun = 'Photo' if result['fetched'] == 1 else 'Photos'
                self.stdout.write('%s: Fetched %s %s' % (
                                result['account'], result['fetched'], noun))
            else:
                self.stderr.write('%s: Failed to fetch Photos: %s' % (
                                        result['account'], result['message']))

