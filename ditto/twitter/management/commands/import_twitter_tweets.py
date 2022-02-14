# coding: utf-8
import os

from django.core.management.base import BaseCommand, CommandError

from ...ingest import Version1TweetIngester, Version2TweetIngester


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

        ingester_class = None

        # For v2, the default:
        # Where the JS files are:
        subpath = "/data"
        ingester_class = Version2TweetIngester

        if options["archive_version"]:
            if options["archive_version"] == "v1":
                # Where the JS files are:
                subpath = "/data/js/tweets"
                ingester_class = Version1TweetIngester

            elif options["archive_version"] != "v2":
                raise CommandError(
                    f"version should be v1 or v2, not '{options['archive_version']}"
                )

        if options["path"]:
            if os.path.isdir(options["path"]):
                js_dir = "%s%s" % (options["path"], subpath)
                if os.path.isdir(js_dir):
                    result = ingester_class().ingest(directory=js_dir)
                else:
                    raise CommandError(
                        f"Expected to find a directory at '{js_dir}' "
                        "containing .js file(s)"
                    )
            else:
                raise CommandError(f"Can't find a directory at '{options['path']}'")
        else:
            raise CommandError(
                (
                    "Specify the location of the archive directory, "
                    "e.g. --path=/path/to/twitter-2022-01-31-abcdef123456"
                )
            )

        if options.get("verbosity", 1) > 0:
            if result["success"]:
                tweetnoun = "tweet" if result["tweets"] == 1 else "tweets"
                filenoun = "file" if result["files"] == 1 else "files"
                mediafilenoun = "file" if result["media"] == 1 else "files"

                self.stdout.write(
                    f"Imported {result['tweets']} {tweetnoun} from "
                    f"{result['files']} {filenoun}, "
                    f"and {result['media']} media {mediafilenoun}"
                )
            else:

                self.stderr.write(f"Failed to import tweets: {result['messages'][0]}")
