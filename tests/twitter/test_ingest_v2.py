import json
import os
from unittest.mock import call, mock_open, patch

from django.test import TestCase

from ditto.twitter import factories
from ditto.twitter.ingest import IngestError, Version2TweetIngester
from ditto.twitter.models import Tweet, User


# e.g. /path/to/django-ditto/tests/twitter/fixtures/ingest/v2/
FIXTURES_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "fixtures", "ingest", "v2"
)
FIXTURES_DIR_NO_TWEETS = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "fixtures", "ingest", "v2_no_tweets"
)


class Version2TweetIngesterTestCase(TestCase):
    def test_saves_all_tweets(self):
        "Saves the tweets to the DB"
        ingester = Version2TweetIngester()
        ingester.ingest(directory=FIXTURES_DIR)
        self.assertEqual(Tweet.objects.count(), 2)

    def test_associates_tweets_with_user(self):
        """The tweets should be associated with the user data
        We should check, given it's all got from separate files.
        """
        ingester = Version2TweetIngester()
        ingester.ingest(directory=FIXTURES_DIR)

        tweet = Tweet.objects.first()
        user = User.objects.first()

        self.assertEqual(tweet.user, user)

    def test_saves_user_data(self):
        "Saves data about the user in each tweet's json"
        ingester = Version2TweetIngester()
        ingester.ingest(directory=FIXTURES_DIR)

        user = User.objects.get(twitter_id=12552)
        raw = json.loads(user.raw)

        self.assertEqual(
            raw,
            {
                "id": 12552,
                "id_str": "12552",
                "screen_name": "philgyford",
                "name": "Phil Gyford",
                "profile_image_url_https": "https://pbs.twimg.com/profile_images/1167616130/james_200208_300x300.jpg",  # NOQA: E501
                "verified": False,
                "protected": False,
                "ditto_note": (
                    "This user data was compiled from separate parts of a "
                    "downloaded twitter archive by Django Ditto"
                ),
            },
        )

    def test_saves_user_object(self):
        "Saves the user object correctly"
        ingester = Version2TweetIngester()
        ingester.ingest(directory=FIXTURES_DIR)

        user = User.objects.get(twitter_id=12552)
        self.assertEqual(user.screen_name, "philgyford")
        self.assertEqual(user.is_private, False)

    def test_returns_correctly_on_success(self):
        "After successfully importing tweets, returns correct data"
        ingester = Version2TweetIngester()
        result = ingester.ingest(directory=FIXTURES_DIR)
        self.assertTrue(result["success"])
        self.assertEqual(result["tweets"], 2)
        self.assertEqual(result["files"], 1)

    def test_returns_correctly_on_success_no_tweets(self):
        "No exceptions, but no tweets were imported; is correct data returned?"
        ingester = Version2TweetIngester()
        result = ingester.ingest(directory=FIXTURES_DIR_NO_TWEETS)
        self.assertFalse(result["success"])
        self.assertEqual(result["tweets"], 0)
        self.assertEqual(result["files"], 1)
        self.assertEqual(result["messages"][0], "No tweets were found")
