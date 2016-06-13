# coding: utf-8
import argparse

from django.core.management.base import BaseCommand, CommandError

from ...models import Account, Tweet


class Command(BaseCommand):
    """Generates the HTML version of all the Tweets.
    Does this by re-saving every Tweet, one-by-one.

    For one account:
    ./manage.py generate_tweet_html --account=philgyford

    For all accounts:
    ./manage.py generate_tweet_html
    """

    help = "Generates the HTML version of all the Tweets."

    def add_arguments(self, parser):
        parser.add_argument(
            '--account',
            action='store',
            default=False,
            help='Only generate for one Twitter account.',
        )

    def handle(self, *args, **options):
        tweets = Tweet.objects.all()

        # If a screen name is provided, only get the Tweets for that:
        if options['account']:
            screen_name = options['account']
            try:
                Account.objects.get(user__screen_name=screen_name)
            except Account.DoesNotExist:
                raise CommandError("There's no Account with a screen name of '%s'" % screen_name)
            tweets = tweets.filter(user__screen_name=screen_name)

        for tweet in tweets:
            tweet.save()

        if options.get('verbosity', 1) > 0:
            self.stdout.write('Generated HTML for %d Tweets' % tweets.count())

