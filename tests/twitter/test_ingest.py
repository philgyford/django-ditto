# coding: utf-8
from unittest.mock import call, mock_open, patch

from django.test import TestCase

from ditto.twitter import factories
from ditto.twitter.ingest import IngestError, TweetIngester
from ditto.twitter.models import Tweet


class TweetIngesterTestCase(TestCase):

    # A sample file of the format we'd get in a Twitter archive.
    ingest_fixture = 'tests/twitter/fixtures/ingest/2015_08.js'

    def get_tweet_data(self):
        "Returns the JSON tweet data, as text, from the fixture."
        file = open(self.ingest_fixture)
        tweet_data = file.read()
        file.close()
        return tweet_data

    def test_raises_error_with_invalid_dir(self):
        with patch('os.path.isdir', return_value=False):
            with self.assertRaises(IngestError):
                TweetIngester().ingest(directory='/bad/dir')

    def test_raises_error_with_empty_dir(self):
        "If no .js files are found, raises IngestError"
        with patch('os.path.isdir', return_value=True):
            with patch('ditto.twitter.ingest.TweetIngester', file_count=0):
                with self.assertRaises(IngestError):
                    TweetIngester().ingest(directory='/bad/dir')

    # All the below have a similar structure to mock out file-related functions.
    # Here's what's happening:

    # We create a list of dummy filenames:
    #   files = ['2015_01.js', '2015_02.js', '2015_03.js',]

    # We get the content of our fixture:
    #   file_content = self.get_tweet_data()

    # Patch listdir() so it returns our fake list of files:
    #   with patch('os.listdir', return_value=files):

    # Create a mock open() function that returns our fixture content:
    #       m = mock_open(read_data=file_content)

    # Patch open() with our mocked version:
    #       with patch('builtins.open', m):

    # Set the return of readlines() on our mocked open() to be a list of
    # lines from our fixture content:
    #           m.return_value.readlines.return_value = file_content.splitlines()

    # Ingest! This will save Tweets using our fixture data, and imagine it's
    # loaded data from our fake files:
    #           result = TweetIngester().ingest(directory='/good/dir')

    def test_opens_all_files(self):
        "All the .js files in the directory are opened."
        user = factories.UserFactory(twitter_id=12552, screen_name='philgyford')
        files = ['2015_01.js', '2015_02.js', '2015_03.js',]
        file_content = self.get_tweet_data()
        with patch('os.listdir', return_value=files):
            m = mock_open(read_data=file_content)
            with patch('builtins.open', m):
                m.return_value.readlines.return_value = file_content.splitlines()
                ingester = TweetIngester()
                result = ingester.ingest(directory='/good/dir')
        m.assert_has_calls([
            call('/good/dir/2015_01.js', 'r'),
            call('/good/dir/2015_02.js', 'r'),
            call('/good/dir/2015_03.js', 'r'),
            ], any_order=True)
        self.assertEqual(ingester.tweet_count, 9)

    def test_saves_all_tweets(self):
        "Saves the tweets to the DB."
        files = ['2015_01.js']
        file_content = self.get_tweet_data()
        with patch('os.listdir', return_value=files):
            m = mock_open(read_data=file_content)
            with patch('builtins.open', m):
                m.return_value.readlines.return_value = file_content.splitlines()
                result = TweetIngester().ingest(directory='/good/dir')
        # We load three dummy files; our results have three tweets in each:
        self.assertEqual(Tweet.objects.count(), 3)

    def test_returns_correctly_on_success(self):
        "After successfully importing tweets, returns correct data"
        files = ['2015_01.js']
        file_content = self.get_tweet_data()
        with patch('os.listdir', return_value=files):
            m = mock_open(read_data=file_content)
            with patch('builtins.open', m):
                m.return_value.readlines.return_value = file_content.splitlines()
                result = TweetIngester().ingest(directory='/good/dir')
        self.assertTrue(result['success'])
        self.assertEqual(result['tweets'], 3)
        self.assertEqual(result['files'], 1)

    def test_returns_correctly_on_success(self):
        "No exceptions, but no tweets were imported; is correct data returned?"
        files = ['2015_01.js']
        file_content = "Dummy line\n[]\n"
        with patch('os.listdir', return_value=files):
            m = mock_open(read_data=file_content)
            with patch('builtins.open', m):
                m.return_value.readlines.return_value = file_content.splitlines()
                result = TweetIngester().ingest(directory='/good/dir')
        self.assertFalse(result['success'])
        self.assertEqual(result['tweets'], 0)
        self.assertEqual(result['files'], 1)
        self.assertEqual(result['messages'][0], 'No tweets were found')

