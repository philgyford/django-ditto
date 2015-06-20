# coding: utf-8
import argparse

from django.core.management.base import BaseCommand, CommandError

from ...fetch import FetchBookmarks


class Command(BaseCommand):
    """
    Fetches bookmarks from Pinboard

    Fetch all bookmarks, from all accounts:
    ./manage.py fetch_pinboard --all

    Fetch bookmarks posted on one date:
    ./manage.py fetch_pinboard --date=2015-06-20

    Fetch the 20 most recent bookmarks:
    ./manage.py fetch_pinboard --recent=20

    Fetch the bookmark for one URL:
    ./manage.py fetch_pinboard --url=http://new-aesthetic.tumblr.com/

    Restrict any of the above to one account by adding the account's username:
    ./manage.py fetch_pinboard --all --account=philgyford
    """
    help = "Fetches bookmarks from Pinboard"


    def add_arguments(self, parser):
        parser.add_argument(
            '--all',
            action='store_true',
            default=False,
            help='Fetch all bookmarks.'
        )
        parser.add_argument(
            '--date',
            action='store_true',
            default=False,
            help='Fetch bookmarks posted on one day, e.g. "2015-06-20".'
        )
        parser.add_argument(
            '--recent',
            action='store_true',
            default=False,
            help='Fetch the most recent bookmarks, e.g. "10".'
        )
        parser.add_argument(
            '--url',
            action='store_true',
            default=False,
            help='Fetch the bookmark for one URL, e.g. "http://www.foo.com".',
        )
        parser.add_argument(
            '--account',
            action='store_true',
            default=False,
            help='Only fetch for one Pinboard account.',
        )

    def handle(self, *args, **options):

        # We might be fetching for a specific account or all (None).
        account = options['account'] if options['account'] else None;

        if options['all']:
            results = FetchBookmarks.fetch_all(account=account)

        elif options['date']:
            results = FetchBookmarks.fetch_date(post_date=options['date'],
                                                            account=account)

        elif options['recent']:
            results = FetchBookmarks.fetch_recent(num=options['recent'],
                                                            account=account)

        elif options['url']:
            results = FetchBookmarks.fetch_url(url=options['url'],
                                                            account=account)

        elif options['account']:
            raise CommandError("Specify --all, --recent, --date= or --url= as well as --account.")
        else:
            raise CommandError("Specify --all, --recent, --date= or --url=")

        # We should get 'success' or 'failure' in results['result']
        # If 'success', we should also get 'fetched' (an int).
        # If 'failure', we should get 'message' (a string).
        if results['result'] == 'success':
            noun = 'bookmark' if results['fetched'] == 1 else 'bookmarks'
            self.stdout.write('Fetched %s %s' % (results['fetched'], noun))

        elif results['result'] == 'failure':
            self.stderr.write('Failed to fetch bookmarks: %s' %
                                                            results['message'])

