import argparse

from django.core.management.base import BaseCommand, CommandError

from ...models import Account


class UpdateTwitterCommand(BaseCommand):
    """Parent class for commands which update Tweets/Users already in the DB.

    Child classes probably only need a fetch() method and an updated_noun.
    """

    # In child classes should be like 'User' or 'Tweet':
    updated_noun = 'None'

    def add_arguments(self, parser):
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
        self.output_results(results)

    def fetch(self, screen_name):
        """Child classes should override this method to call a method that
        fetches Tweets/Users and returns results, eg:
            return TweetsFetcher(screen_name=screen_name).fetch()
        """
        return {}

    def output_results(self, results):
        for result in results:
            if result['success']:
                noun = self.updated_noun if result['fetched'] == 1 else self.plural_noun()
                self.stdout.write('%s: Fetched %s %s' % (
                                result['account'], result['fetched'], noun))

            else:
                self.stderr.write('%s: Failed to fetch %s: %s' % (
                    result['account'], self.plural_noun(), result['message']))

    def plural_noun(self):
        return '%s%s' % (self.updated_noun, 's')

