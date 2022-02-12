# coding: utf-8
import os

from django.core.management.base import BaseCommand, CommandError

from ...ingest import Version1TweetIngester


class Command(BaseCommand):
    """Imports tweets from a downloaded archive of Tweets.
    Request your archive from https://twitter.com/settings/account

    Usage:
    ./manage.py import_tweets --path=/Users/phil/Downloads/12552_dbeb4be9b8ff5f76d7d486c005cc21c9faa61f66  # noqa: E501
    """

    help = "Imports a complete history of tweets from a downloaded archive"

    def add_arguments(self, parser):
        parser.add_argument(
            "--path",
            action="store",
            default=False,
            help="Path to the directory that is the archive",
        )

        parser.add_argument(
            "--archive-version",
            action="store",
            default=None,
            help="v1 or v2 (default). Which format of archives to import from.",
        )

    def handle(self, *args, **options):
        # Location of the directory holding the tweet JSON files within the
        # archive:
        subpath = "/data/js/tweets"

        ingester_class = None

        if options["archive_version"]:
            if options["archive_version"] == "v1":
                ingester_class = Version1TweetIngester
            else:
                raise CommandError(
                    f"version should be v1 or v2, not '{options['archive_version']}"
                )
        if options["path"]:
            if os.path.isdir(options["path"]):
                tweets_dir = "%s%s" % (options["path"], subpath)
                if os.path.isdir(tweets_dir):
                    result = ingester_class().ingest(directory=tweets_dir)
                else:
                    raise CommandError(
                        f"Expected to find a directory at '{tweets_dir}' "
                        "containing JSON files"
                    )
            else:
                raise CommandError(f"Can't find a directory at '{options['path']}'")
        else:
            raise CommandError(
                (
                    "Specify the location of the archive, "
                    "e.g. --path=/Path/To/1234567890_abcdefg12345"
                )
            )

        if options.get("verbosity", 1) > 0:
            if result["success"]:
                tweetnoun = "tweet" if result["tweets"] == 1 else "tweets"
                filenoun = "file" if result["files"] == 1 else "files"

                self.stdout.write(
                    f"Imported {result['tweets']} {tweetnoun} from "
                    f"{result['files']} {filenoun}"
                )
            else:

                self.stderr.write(f"Failed to import tweets: {result['messages'][0]}")
