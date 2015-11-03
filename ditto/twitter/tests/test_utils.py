# coding: utf-8
import json
from django.test import TestCase

from ..utils import htmlify_tweet


class UtilsHtmlifyTestCase(TestCase):

    # Define in child classes.
    api_fixture = None

    def setUp(self):
        json_file = open(self.api_fixture)
        self.json_data = json.loads(json_file.read())
        json_file.close()


class UtilsHtmlifyEntitiesTestCase(UtilsHtmlifyTestCase):
    "Linkify URLs from entities, screen_names, hashtags."

    api_fixture = 'ditto/twitter/fixtures/api/tweet_with_entities.json'

    def test_links_urls(self):
        "Makes 'urls' entities into clickable links."
        tweet_html = htmlify_tweet(self.json_data)
        self.assertTrue('with <a href="http://www.bbc.co.uk/news/business-34505593" rel="external">bbc.co.uk/news/business-…</a>' in tweet_html)
        self.assertTrue('and <a href="http://www.wired.com/2015/10/meet-walking-dead-hp-cisco-dell-emc-ibm-oracle/" rel="external">wired.com/2015/10/meet-w…</a>' in tweet_html)

    def test_links_users(self):
        "Makes 'user_mentions' entities into clickable @links."
        tweet_html = htmlify_tweet(self.json_data)
        self.assertTrue('for <a href="https://twitter.com/philgyford" rel="external">@philgyford</a>' in tweet_html)
        self.assertTrue('and <a href="https://twitter.com/samuelpepys" rel="external">@samuelpepys</a>' in tweet_html)

    def test_links_hashtags(self):
        "Makes 'hashtags' entities into clickable #links."
        tweet_html = htmlify_tweet(self.json_data)
        self.assertTrue(' <a href="https://twitter.com/hashtag/testing" rel="external">#testing</a> and' in tweet_html)
        self.assertTrue(' <a href="https://twitter.com/hashtag/hashtag" rel="external">#hashtag</a>' in tweet_html)


class UtilsHtmlifyFormattingTestCase(UtilsHtmlifyTestCase):

    api_fixture = 'ditto/twitter/fixtures/api/tweet_with_entities.json'

    def test_linebreaks(self):
        "Turns linebreaks into <br>s"
        tweet_html = htmlify_tweet(self.json_data)
        self.assertTrue("""A<br>test for""" in tweet_html)

    def test_strip(self):
        "Strips whitespace at start and end"
        tweet = self.json_data
        tweet['text'] = ' X' + tweet['text'] + 'Y '
        tweet_html = htmlify_tweet(tweet)
        self.assertEqual('X', tweet_html[0])
        self.assertEqual('Y', tweet_html[-1])


class UtilsHtmlifyLinksTestCase(UtilsHtmlifyTestCase): 
    """Old Tweets included in the downloaded archive files don't have 'entities'
    elements, so we need to manually link any URLs in their tweets.
    """

    api_fixture = 'ditto/twitter/fixtures/api/tweet_from_archive_2006.json'

    def test_links_old_urls(self):
        tweet_html = htmlify_tweet(self.json_data)
        self.assertEqual(tweet_html,
            'Made a little Twitter thing: <a href="http://www.gyford.com/phil/writing/2006/12/02/quick_twitter.php">http://www.gyford.com/phil/writing/2006/12/02/quick_twitter.php</a>')


class UtilsHtmlifyPhotosTestCase(UtilsHtmlifyTestCase): 
    "Remove links to photos in the tweet text."

    api_fixture = 'ditto/twitter/fixtures/api/tweet_with_photos.json'

    def test_removes_photo_links(self):
        tweet_html = htmlify_tweet(self.json_data)
        self.assertEqual('Testing multiple images.', tweet_html)

