import argparse

from django.core.management.base import BaseCommand, CommandError

from ...fetch import UserFetcher


class Command(BaseCommand):
    """For fetching data about a single Flickr user, based on their Flickr URL.

    Should create/update them in our DB.

        ./manage.py fetch_flickr_user --url=https://www.flickr.com/photos/philgyford/8102921/
    """

    help = "Fetches data for a single Flickr User"

    def add_arguments(self, parser):
        parser.add_argument(
            '--url',
            action='store',
            default=False,
            help='The URL of a flickr.com page belonging to the user.',
        )

    def handle(self, *args, **options):
        if options['url']:
            if not options['url'].startswith('https://www.flickr.com/'):
                raise CommandError("This doesn't look like a flickr.com URL: '%s'" % options['url'])
            else:
                results = UserFetcher().fetch(url=options['url'])
        else:
            raise CommandError("Specify a URL with --url=https://www.flickr.com/...")

        for result in results:
            if result['success']:
                self.stdout.write("Fetched user '%s'" % result['user']['name'])

            else:
                self.stderr.write("Failed to fetch a user using URL '%s': %s" %
                                            (options['url'], result['message']))
