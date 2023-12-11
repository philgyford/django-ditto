from django.core.management.base import CommandError

from ditto.core.management.commands import DittoBaseCommand


class FetchCommand(DittoBaseCommand):
    """
    Parent for all classes that fetch some things from Flickr. Photos,
    Photosets, Files, etc.
    """

    def add_arguments(self, parser):
        "All children will have the --account option."
        super().add_arguments(parser)

        parser.add_argument(
            "--account",
            action="store",
            default=False,
            help=(
                "The NSID of the Flickr User associated with the one "
                "Account to fetch for."
            ),
        )


class FetchPhotosCommand(FetchCommand):
    # What we're fetching:
    singular_noun = "Photo"
    plural_noun = "Photos"

    # Child classes should supply some help text for the --days and
    # --start/--end arguments:
    days_help = ""
    start_help = ""
    end_help = ""

    def add_arguments(self, parser):
        super().add_arguments(parser)

        parser.add_argument("--days", action="store", default=None, help=self.days_help)

        parser.add_argument(
            "--start", action="store", default=None, help=self.start_help
        )
        parser.add_argument("--end", action="store", default=None, help=self.end_help)

    def handle(self, *args, **options):
        # We might be fetching for a specific account or all (None).
        nsid = options["account"] if options["account"] else None

        if options["days"] and (options["start"] or options["end"]):
            msg = "You can't use --days with --start or --end"
            raise CommandError(msg)

        if options["days"]:
            # Will be either 'all' or a number; make the number an int.
            if options["days"].isdigit():
                options["days"] = int(options["days"])
            elif options["days"] != "all":
                msg = "--days should be an integer or 'all'."
                raise CommandError(msg)

            results = self.fetch_photos(nsid=nsid, days=options["days"])
            self.output_results(results, options.get("verbosity", 1))

        elif options["start"] or options["end"]:
            results = self.fetch_photos(
                nsid=nsid, start=options["start"], end=options["end"]
            )
            self.output_results(results, options.get("verbosity", 1))

        elif options["account"]:
            msg = "Specify --days, or --start and/or --end as well as --account."
            raise CommandError(msg)

        else:
            msg = "Specify --days, or --start and/or --end."
            raise CommandError(msg)

    def fetch_photos(self, nsid, days=None, start=None, end=None):
        """Child classes should override this method to call a method that
        fetches photos and returns results, eg:
            return RecentPhotosMultiAccountFetcher(nsid=nsid).fetch(days=days)
        """
        return {}
