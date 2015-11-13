# coding: utf-8
import argparse

from django.core.management.base import BaseCommand, CommandError

from ...fetch import UsersFetcher
from ...models import Account


class Command(BaseCommand):
    """Fetches data for all Twitter Users in the DB, updating their info.

    Specify an account to use its API credentials:
    ./manage.py fetch_users --account=philgyford

    Or, if you're not bothered which:
    ./manage.py fetch_users
    """

    help = "Fetches the latest data about each Twitter user"

    def add_arguments(self, parser):
        parser.add_argument(
            '--account',
            action='store',
            default=False,
            help='Which Twitter account to use for the API call. Otherwise we use the first one found in the DB.',
        )

    def handle(self, *args, **options):

        if options['account']:
            screen_name = options['account']
            try:
                Account.objects.get(user__screen_name=screen_name)
            except Account.DoesNotExist:
                raise CommandError("There's no Account with a screen name of '%s'" % screen_name)
        else:
            try:
                account = Account.objects.exclude(consumer_key='')[0]
            except IndexError:
                raise CommandError("There's no Account with Twitter API credentials")
            screen_name = account.user.screen_name

        results = UsersFetcher(screen_name=screen_name).fetch()
        self.output_results(results)

    def output_results(self, results):
        for result in results:
            if result['success']:
                noun = 'User' if result['fetched'] == 1 else 'Users'
                self.stdout.write('%s: Fetched %s %s' % (
                                result['account'], result['fetched'], noun))

            else:
                self.stderr.write('%s: Failed to fetch Users: %s' % (
                                        result['account'], result['message']))

