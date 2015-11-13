# coding: utf-8
import argparse

from django.core.management.base import BaseCommand, CommandError


class FetchTwitterCommand(BaseCommand):

    # Child classes should supply some help text for the --recent argument:
    recent_help = ""

    def add_arguments(self, parser):
        parser.add_argument(
            '--recent',
            action='store',
            default=False,
            help=self.recent_help
        )
        parser.add_argument(
            '--account',
            action='store',
            default=False,
            help='Only fetch for one Twitter account.',
        )

    def handle(self, *args, **options):

        # We might be fetching for a specific account or all (None).
        account = options['account'] if options['account'] else None;

        if options['recent']:
            # Will be either 'new' or a number; make the number an int.
            if options['recent'].isdigit():
                options['recent'] = int(options['recent'])

            results = self.fetch_tweets(account, options['recent'])
            self.output_results(results)
        elif options['account']:
            raise CommandError("Specify --recent as well as --account.")
        else:
            raise CommandError("Specify --recent, eg --recent=100 or --recent=new.")

    def fetch_tweets(self, account, count):
        """Child classes should override this method to call a method that
        fetches tweets and returns results, eg:
            return RecentTweetsFetcher(screen_name=account).fetch(count=count)
        """
        return {}

    def output_results(self, results):
        """results should be a list of dicts.

        Each dict is for one account.
        Each dict will look like either:

          { 'account': 'thescreename',
            'success': True,
            'fetched': 200, # The number of Tweets fetched
          }

        or:

          { 'account': 'thescreename',
            'success': False,
            'message': 'There was an error fetching data because blah',
          }
        """
        for result in results:
            if result['success']:
                noun = 'Tweet' if result['fetched'] == 1 else 'Tweets'
                self.stdout.write('%s: Fetched %s %s' % (
                                result['account'], result['fetched'], noun))

            else:
                self.stderr.write('%s: Failed to fetch Tweets: %s' % (
                                        result['account'], result['message']))

