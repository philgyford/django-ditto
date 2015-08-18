# coding: utf-8
import argparse

from django.core.management.base import BaseCommand, CommandError

from ...fetch import FavoriteTweetsFetcher, RecentTweetsFetcher


class Command(BaseCommand):
    """Fetches tweets from Twitter.

    Fetch recent tweets since the last fetch, from all accounts:
    ./manage.py fetch_twitter_tweets --recent

    Fetch recent tweets, from all accounts:
    ./manage.py fetch_twitter_tweets --recent

    Fetch recent tweets since the last fetch, from one account:
    ./manage.py fetch_twitter_tweets --recent --account=philgyford

    Fetch recent tweets favorited by all accounts:
    ./manage.py fetch_twitter_tweets --favorites

    Fetch recent tweets favorited by one account:
    ./manage.py fetch_twitter_tweets --favorites --account=philgyford
    """
    help = "Fetches recent and favorited tweets from Twitter"

    def add_arguments(self, parser):
        parser.add_argument(
            '--favorites',
            action='store_true',
            default=False,
            help='Fetch the most recent favorited tweets.'
        )
        parser.add_argument(
            '--recent',
            action='store_true',
            default=False,
            help='Fetch the most recent tweets.'
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

        if options['favorites']:
            results = FavoriteTweetsFetcher(screen_name=account).fetch()
        elif options['recent']:
            results = RecentTweetsFetcher(screen_name=account).fetch()
        elif options['account']:
            raise CommandError("Specify --recent or --favorites as well as --account.")
        else:
            raise CommandError("Specify --recent or --favorites.")

        # results should be a list of dicts.
        # Each dict is for one account.
        # Each dict will look like either:
        # { 'account': 'thescreename',
        #   'success': True,
        #   'fetched': 200, # The number of tweets fetched
        # }
        # or:
        # { 'account': 'thescreename',
        #   'success': False,
        #   'message': 'There was an error fetching data because blah',
        #}
        for result in results:
            if result['success']:
                noun = 'tweet' if result['fetched'] == 1 else 'tweets'
                self.stdout.write('%s: Fetched %s %s' % (
                                result['account'], result['fetched'], noun))

            else:
                self.stderr.write('%s: Failed to fetch tweets: %s' % (
                                        result['account'], result['message']))

