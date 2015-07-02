# coding: utf-8
import argparse

from django.core.management.base import BaseCommand, CommandError

from ...fetch import FetchBookmarks


class Command(BaseCommand):
    """Fetches bookmarks from Pinboard

    Fetch all bookmarks, from all accounts:
    ./manage.py fetch_pinboard_bookmarks --all

    Fetch bookmarks posted on one date:
    ./manage.py fetch_pinboard_bookmarks --date=2015-06-20

    Fetch the 20 most recent bookmarks:
    ./manage.py fetch_pinboard_bookmarks --recent=20

    Fetch the bookmark for one URL:
    ./manage.py fetch_pinboard_bookmarks --url=http://new-aesthetic.tumblr.com/

    Restrict any of the above to one account by adding the account's username:
    ./manage.py fetch_pinboardbookmarks --all --account=philgyford
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
            action='store',
            default=False,
            help='Fetch bookmarks posted on one day, e.g. "2015-06-20".'
        )
        parser.add_argument(
            '--recent',
            action='store',
            default=False,
            help='Fetch the most recent bookmarks, e.g. "10".'
        )
        parser.add_argument(
            '--url',
            action='store',
            default=False,
            help='Fetch the bookmark for one URL, e.g. "http://www.foo.com".',
        )
        parser.add_argument(
            '--account',
            action='store',
            default=False,
            help='Only fetch for one Pinboard account.',
        )

    def handle(self, *args, **options):

        # We might be fetching for a specific account or all (None).
        account = options['account'] if options['account'] else None;

        if options['all']:
            results = FetchBookmarks().fetch_all(username=account)

        elif options['date']:
            results = FetchBookmarks().fetch_date(post_date=options['date'],
                                                            username=account)

        elif options['recent']:
            results = FetchBookmarks().fetch_recent(num=options['recent'],
                                                            username=account)

        elif options['url']:
            results = FetchBookmarks().fetch_url(url=options['url'],
                                                            username=account)

        elif options['account']:
            raise CommandError("Specify --all, --recent, --date= or --url= as well as --account.")
        else:
            raise CommandError("Specify --all, --recent, --date= or --url=")

        # results should be a list of dicts.
        # If a result dict is for one account it'll have an 'account' element.
        # Each result dict will have:
        #   'success': True or False.
        #   'fetched': integer, the number of Bookmarks fetched.
        # If it failed, we should also get 'message' (a string).
        for result in results:
            account = result['account'] if 'account' in result else 'all'
            if result['success']:
                noun = 'bookmark' if result['fetched'] == 1 else 'bookmarks'
                self.stdout.write('%s: Fetched %s %s' % (
                                            account, result['fetched'], noun))

            else:
                self.stderr.write('%s: Failed to fetch bookmarks: %s' %
                                                (account, result['message']))

