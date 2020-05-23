# coding: utf-8
import json
import os

from .fetch.savers import TweetSaver
from ..core.utils import datetime_now


class IngestError(Exception):
    pass


class TweetIngester(object):
    """For importing a downloaded archive of tweets.
    Request yours from https://twitter.com/settings/account

    Use like:

    results = TweetIngester.ingest(
        '/Users/phil/Downloads/12552_dbeb4be9b8ff5f76d7d486c005cc21c9faa61f66/data/js/tweets'
    )

    Where that's the path to the directory containing the *.js files holding
    tweet data.

    results will be a dict of data about what happened, including
    results['success'] which is boolean.
    """

    def __init__(self):
        # Used as the 'fetch_time' for each tweet.
        self.fetch_time = datetime_now()

        # How many .js files we loaded the tweets from:
        self.file_count = 0

        # How mnay tweets we found in all the files:
        self.tweet_count = 0

        # Stores all the imported data from the files before saving.
        # So that we know we've got through all the files within JSON errors
        # etc before we begin touching the DB.
        self.tweets_data = []

    def ingest(self, directory):
        """Import all the tweet data and create/update the tweets."""

        self._load_data(directory)
        self._save_tweets()
        if self.tweet_count > 0:
            return {
                "success": True,
                "tweets": self.tweet_count,
                "files": self.file_count,
            }
        else:
            return {
                "success": False,
                "tweets": 0,
                "files": self.file_count,
                "messages": ["No tweets were found"],
            }

    def _load_data(self, directory):
        """Goes through all the *.js files in `directory` and puts the tweet
        data inside into self.tweets_data.

        No data is saved to the database until we've successfully loaded JSON
        from all of the files.

        Keyword arguments:
        directory -- The directory to load the files from.

        Raises:
        FetchError -- If the directory is invalid, or there are no .js files,
            or we can't load JSON from one of the files.
        """
        try:
            for file in os.listdir(directory):
                if file.endswith(".js"):
                    filepath = "%s/%s" % (directory, file)
                    self._get_data_from_file(filepath)
                    self.file_count += 1
        except OSError as e:
            raise IngestError(e)

        if self.file_count == 0:
            raise IngestError("No .js files found in %s" % directory)

    def _get_data_from_file(self, filepath):
        """Looks in a file, parses its JSON, and adds a dict of data about
        each tweet found to self.tweets_data.

        Arguments:
        filespath -- Absolute path to the file.
        """
        f = open(filepath, "r")
        lines = f.readlines()
        # Remove first line, that contains JavaScript:
        lines = lines[1:]
        try:
            tweets_data = json.loads("".join(lines))
        except ValueError:
            raise IngestError("Could not load JSON from %s" % filepath)
        else:
            self.tweets_data.extend(tweets_data)
        f.close()

    def _save_tweets(self):
        """Go through the list of dicts that is self.tweets_data and
        create/update each tweet in the DB.
        """
        if len(self.tweets_data) == 0:
            return

        for tweet in self.tweets_data:
            TweetSaver().save_tweet(tweet, self.fetch_time)
            self.tweet_count += 1
