# coding: utf-8
from django.core.management.base import CommandError

from ....core.management.commands import DittoBaseCommand
from ...fetch import (
    AllBookmarksFetcher,
    DateBookmarksFetcher,
    RecentBookmarksFetcher,
    UrlBookmarksFetcher,
)


class Command(DittoBaseCommand):
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

    singular_noun = "Bookmark"
    plural_noun = "Bookmarks"

    help = "Fetches bookmarks from Pinboard"

    def add_arguments(self, parser):
        super().add_arguments(parser)

        parser.add_argument(
            "--all", action="store_true", default=False, help="Fetch all bookmarks."
        )
        parser.add_argument(
            "--date",
            action="store",
            default=False,
            help='Fetch bookmarks posted on one day, e.g. "2015-06-20".',
        )
        parser.add_argument(
            "--recent",
            action="store",
            default=False,
            help='Fetch the most recent bookmarks, e.g. "10".',
        )
        parser.add_argument(
            "--url",
            action="store",
            default=False,
            help='Fetch the bookmark for one URL, e.g. "http://www.foo.com".',
        )
        parser.add_argument(
            "--account",
            action="store",
            default=False,
            help="Only fetch for one Pinboard account.",
        )

    def handle(self, *args, **options):

        # We might be fetching for a specific account or all (None).
        account = options["account"] if options["account"] else None

        if options["all"]:
            results = AllBookmarksFetcher().fetch(username=account)

        elif options["date"]:
            results = DateBookmarksFetcher().fetch(
                post_date=options["date"], username=account
            )

        elif options["recent"]:
            results = RecentBookmarksFetcher().fetch(
                num=options["recent"], username=account
            )

        elif options["url"]:
            results = UrlBookmarksFetcher().fetch(url=options["url"], username=account)

        elif options["account"]:
            raise CommandError(
                "Specify --all, --recent, --date= or --url= as well as --account."
            )
        else:
            raise CommandError("Specify --all, --recent, --date= or --url=")

        self.output_results(results, options.get("verbosity", 1))
