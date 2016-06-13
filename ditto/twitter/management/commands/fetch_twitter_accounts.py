# coding: utf-8
import argparse

from django.core.management.base import BaseCommand, CommandError

from ...fetch.fetchers import VerifyFetcher


class Command(BaseCommand):
    """Updates the stored data about the Twitter user for one or all Accounts.

    For one account:
    ./manage.py fetch_accounts --account=philgyford

    For all accounts:
    ./manage.py fetch_accounts
    """

    help = "Fetches and updates data about Accounts' Twitter Users"

    def add_arguments(self, parser):
        parser.add_argument(
            '--account',
            action='store',
            default=False,
            help='Only fetch for one Twitter account.',
        )

    def handle(self, *args, **options):
        # We might be fetching for a specific account or all (None).
        account = options['account'] if options['account'] else None;

        results = VerifyFetcher(screen_name=account).fetch()

        # results should be a list of dicts, either:
        # { 'account': 'thescreenname',
        #   'success': True
        # }
        # or:
        # { 'account': 'thescreenname',
        #   'success': False,
        #   'messages': ["This screen_name doesn't exist"]
        # }
        if options.get('verbosity', 1) > 0:
            for result in results:
                if result['success']:
                    self.stdout.write('Fetched @%s' % result['account'])
                else:
                    self.stderr.write('Could not fetch @%s: %s' % (
                                    result['account'], result['messages'][0]
                                ))

