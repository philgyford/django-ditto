from django.core.management.base import CommandError

from ....core.management.commands import DittoBaseCommand
from ...fetch import ScrobblesMultiAccountFetcher


class Command(DittoBaseCommand):

    # What we're fetching:
    singular_noun = "Scrobble"
    plural_noun = "Scrobbles"

    def add_arguments(self, parser):
        super().add_arguments(parser)

        parser.add_argument(
            "--account",
            action="store",
            default=False,
            help='The username of the Last.fm user to fetch Scrobbles for. e.g. "rj".',
        )

        parser.add_argument(
            "--days",
            action="store",
            default=False,
            help=(
                'Number of days to fetch. Or "all" for ALL scrobbles. '
                "Or omit to only fetch since the most recently fetched scrobble."
            ),
        )

    def handle(self, *args, **options):
        # We might be fetching for a specific account or all (None).
        username = options["account"] if options["account"] else None

        # Default:
        fetch_type = "recent"

        if options["days"]:
            # Will be either 'all' or a number; make the number an int.
            if options["days"].isdigit():
                options["days"] = int(options["days"])
                fetch_type = "days"

            elif options["days"] == "all":
                fetch_type = "all"

            else:
                raise CommandError("--days should be an integer or 'all'.")

        fetcher = ScrobblesMultiAccountFetcher(username=username)

        if fetch_type == "days":
            results = fetcher.fetch(fetch_type=fetch_type, days=options["days"])
        else:
            results = fetcher.fetch(fetch_type=fetch_type)

        self.output_results(results, options.get("verbosity", 1))
