# coding: utf-8
import argparse

from django.core.management.base import CommandError

from ....core.management.commands import DittoBaseCommand
from ...models import Account


class FetchTwitterCommand(DittoBaseCommand):

    # What we're fetching:
    singular_noun = 'Tweet'
    plural_noun = 'Tweets'

    # Child classes should supply some help text for the --recent argument:
    recent_help = ""

    def add_arguments(self, parser):
        super().add_arguments(parser)

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
            self.output_results(results, options.get('verbosity', 1))
        elif options['account']:
            raise CommandError("Specify --recent as well as --account.")
        else:
            raise CommandError(
                        "Specify --recent, eg --recent=100 or --recent=new.")

    def fetch_tweets(self, screen_name, count):
        """Child classes should override this method to call a method that
        fetches tweets and returns results, eg:
            return RecentTweetsFetcher(screen_name=screen_name).fetch(count=count)
        """
        return {}


class UpdateTwitterCommand(DittoBaseCommand):
    """Parent class for commands which update Tweets/Users already in the DB.

    Child classes probably only need a fetch() method.
    """

    def add_arguments(self, parser):
        super().add_arguments(parser)

        parser.add_argument(
            '--account',
            action='store',
            default=False,
            help='Which Twitter account to use for the API call.',
        )

    def handle(self, *args, **options):
        if options['account']:
            screen_name = options['account']
            try:
                Account.objects.get(user__screen_name=screen_name)
            except Account.DoesNotExist:
                raise CommandError("There's no Account with a screen name of '%s'" % screen_name)
        else:
            raise CommandError("Specify --account, eg --account=philgyford.")

        results = self.fetch(screen_name)
        self.output_results(results, options.get('verbosity', 1))

    def fetch(self, screen_name):
        """Child classes should override this method to call a method that
        fetches Tweets/Users and returns results, eg:
            return TweetsFetcher(screen_name=screen_name).fetch()
        """
        return {}

