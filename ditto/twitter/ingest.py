import json
import os
from urllib.parse import urlparse

from django.core.files import File

from ditto.core.utils import datetime_now

from .fetch.savers import TweetSaver
from .models import Media


class IngestError(Exception):
    pass


class TweetIngester:
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

        # How many media files we imported:
        self.media_count = 0

        # Stores all the imported data from the files before saving.
        # So that we know we've got through all the files within JSON errors
        # etc before we begin touching the DB.
        self.tweets_data = []

    def ingest(self, directory):
        """Import all the tweet data and create/update the tweets."""

        self._load_data(directory)

        self._save_tweets(directory)

        self._save_media(directory)

        if self.tweet_count > 0:
            return {
                "success": True,
                "tweets": self.tweet_count,
                "files": self.file_count,
                "media": self.media_count,
            }
        else:
            return {
                "success": False,
                "tweets": 0,
                "files": self.file_count,
                "media": self.media_count,
                "messages": ["No tweets were found"],
            }

    def _load_data(self, directory):
        """
        Child classes must implement their own _load_data() method.

        It should populate self.tweets_data with a list of dicts, each
        one being data about a single tweet.

        And it should set self.file_count to be the number of JS files
        we import the data from.
        """
        msg = (
            "Child classes of TweetImporter must implement their own "
            "_load_data() method."
        )
        raise NotImplementedError(msg)

    def _save_tweets(self, directory):
        """Go through the list of dicts that is self.tweets_data and
        create/update each tweet in the DB.
        """
        if len(self.tweets_data) == 0:
            return

        for tweet in self.tweets_data:
            TweetSaver().save_tweet(tweet, self.fetch_time)
            self.tweet_count += 1

    def _save_media(self, directory):
        """Save media files.
        Not doing anything by default.
        """


class Version1TweetIngester(TweetIngester):
    """
    Used for the old (original?) format of twitter archives, which contained
    three files and five folders, including data/js/tweets/ which contained
    a .js file for every month, like 2016_02.js. This is what we import
    the tweet data from.

    Sometime in 2019, between January and May, the format changed to
    what we call version 2.
    """

    def _load_data(self, directory):
        """Goes through all the *.js files in `directory` and puts the tweet
        data inside into self.tweets_data.

        No data is saved to the database until we've successfully loaded JSON
        from all of the files.

        Keyword arguments:
        directory -- The directory to load the files from.

        Raises:
        IngestError -- If the directory is invalid, or there are no .js files,
            or we can't load JSON from one of the files.
        """
        try:
            for file in os.listdir(directory):
                if file.endswith(".js"):
                    filepath = f"{directory}/{file}"
                    self._get_data_from_file(filepath)
                    self.file_count += 1
        except OSError as err:
            raise IngestError(err) from err

        if self.file_count == 0:
            raise IngestError("No .js files found in %s" % directory)

    def _get_data_from_file(self, filepath):
        """Looks in a file, parses its JSON, and adds a dict of data about
        each tweet found to self.tweets_data.

        Arguments:
        filespath -- Absolute path to the file.
        """
        with open(filepath) as f:
            lines = f.readlines()
            # Remove first line, that contains JavaScript:
            lines = lines[1:]
            try:
                tweets_data = json.loads("".join(lines))
            except ValueError as err:
                msg = f"Could not load JSON from {filepath}: {err}"
                raise IngestError(msg) from err
            else:
                self.tweets_data.extend(tweets_data)


class Version2TweetIngester(TweetIngester):
    """
    Used for what we call the version 2 format of twitter archive, which
    was introduced sometime between January and May of 2019.

    It contains two directories - assets and data - and a "Your archive.html" file.

    This not only saves the Tweet objects but also imports media from the
    tweet_media directory, saving it as Media files .
    """

    def __init__(self):
        super().__init__()

        # Tweets in this format don't contain data about the user.
        # So we create and store that once, in this separate field.
        self.user_data = {}

    def _load_data(self, directory):
        """
        Generate the user data and load all the tweets' data
        In this archive format, the tweets contain no data about the user.
        So we create a user data dict to use when saving the tweets.
        """

        self.user_data = self._construct_user_data(directory)

        self.tweets_data = self._get_json_from_file(directory, "tweet.js")

        self.file_count = 1

    def _save_tweets(self, directory):
        """
        Save the tweets with our constructed user data.
        """
        if len(self.tweets_data) == 0:
            return

        for tweet in self.tweets_data:
            # Here we pass in our user_data too, so save_tweet() can use
            # that in lieu of the data that is usually within each tweet's data.
            TweetSaver().save_tweet(tweet["tweet"], self.fetch_time, self.user_data)
            self.tweet_count += 1

    def _save_media(self, directory):
        """
        Save any animated gif's mp4 or an image's file for the saved tweets.
        """

        for t in self.tweets_data:
            tweet = t["tweet"]

            if "extended_entities" in tweet and "media" in tweet["extended_entities"]:
                for item in tweet["extended_entities"]["media"]:
                    try:
                        media_obj = Media.objects.get(twitter_id=int(item["id"]))
                    except Media.DoesNotExist:
                        pass
                    else:
                        if (
                            media_obj.media_type != "video"
                            and media_obj.has_file is False
                        ):
                            # We don't save video files - only image files, and mp4s
                            # for # GIFs - and only want to do this if we don't already
                            # have a file.

                            if (
                                media_obj.media_type == "animated_gif"
                                and media_obj.mp4_url
                            ):
                                url = media_obj.mp4_url
                            elif (
                                media_obj.media_type == "photo" and media_obj.image_url
                            ):
                                url = media_obj.image_url

                            if url:
                                # Work out name of file in the tweet_media directory:
                                parsed_url = urlparse(url)
                                filename = os.path.basename(parsed_url.path)
                                local_filename = f"{tweet['id_str']}-{filename}"
                                filepath = os.path.join(
                                    directory, "tweet_media", local_filename
                                )

                                with open(filepath, "rb") as f:
                                    django_file = File(f)
                                    if media_obj.media_type == "animated_gif":
                                        # When we fetch GIFs we also fetch an image file
                                        # for them. But their images aren't included in
                                        # the downloaded archive so we'll make do
                                        # without here.
                                        media_obj.mp4_file.save(filename, django_file)
                                        self.media_count += 1
                                    elif media_obj.media_type == "photo":
                                        media_obj.image_file.save(filename, django_file)
                                        self.media_count += 1

    def _construct_user_data(self, directory):
        """
        Make a single dict of data about a user like we'd get from the API.
        This data is in several separate files in the download so we need to
        piece it together from those.
        """

        account_data = self._get_json_from_file(directory, "account.js")

        profile_data = self._get_json_from_file(directory, "profile.js")

        verified_data = self._get_json_from_file(directory, "verified.js")

        try:
            user_data = {
                "id": int(account_data[0]["account"]["accountId"]),
                "id_str": account_data[0]["account"]["accountId"],
                "screen_name": account_data[0]["account"]["username"],
                "name": account_data[0]["account"]["accountDisplayName"],
                "profile_image_url_https": profile_data[0]["profile"]["avatarMediaUrl"],
                "verified": verified_data[0]["verified"]["verified"],
                # So that we don't mistake this for coming from the API when
                # we save the JSON:
                "ditto_note": (
                    "This user data was compiled from separate parts of a "
                    "downloaded twitter archive by Django Ditto"
                ),
            }
        except KeyError as err:
            msg = f"Error creating user data: {err}"
            raise ImportError(msg) from err

        return user_data

    def _get_json_from_file(self, directory, filepath):
        filepath = os.path.join(directory, filepath)
        try:
            f = open(filepath)  # noqa: SIM115
        except OSError as err:
            raise ImportError(err) from err

        lines = f.readlines()
        # Remove first line, that contains JavaScript:
        lines = ["["] + lines[1:]

        try:
            data = json.loads("".join(lines))
        except ValueError as err:
            msg = f"Could not load JSON from {filepath}: {err}"
            raise IngestError(msg) from err
        else:
            f.close()
            return data
