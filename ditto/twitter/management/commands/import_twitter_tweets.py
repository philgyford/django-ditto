# coding: utf-8
import os

from django.core.management.base import BaseCommand, CommandError

from ...ingest import TweetIngester


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

    def handle(self, *args, **options):
        # Location of the directory holding the tweet JSON files within the
        # archive:
        subpath = "/data/js/tweets"

        if options["path"]:
            if os.path.isdir(options["path"]):
                tweets_dir = "%s%s" % (options["path"], subpath)
                if os.path.isdir(tweets_dir):
                    result = TweetIngester().ingest(directory=tweets_dir)
                else:
                    raise CommandError(
                        "Expected to find a directory at '%s' containing JSON files"
                        % tweets_dir
                    )
            else:
                raise CommandError("Can't find a directory at '%s'" % options["path"])
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
                    "Imported %s %s from %s %s"
                    % (result["tweets"], tweetnoun, result["files"], filenoun)
                )
            else:

                self.stderr.write(
                    "Failed to import tweets: %s" % (result["messages"][0])
                )
