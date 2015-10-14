# coding: utf-8
import json
from django.test import TestCase

from ..utils import htmlify_tweet


class UtilsTestCase(TestCase):

    api_fixture = 'ditto/twitter/fixtures/api/tweet_with_entities.json'

    def setUp(self):
        json_file = open(self.api_fixture)
        self.json_data = json.loads(json_file.read())
        json_file.close()

    def test_links_users(self):
        tweet_html = htmlify_tweet(self.json_data)
        self.assertTrue('with <a href="http://www.bbc.co.uk/news/business-34505593" rel="external">bbc.co.uk/news/business-…</a>' in tweet_html)
        self.assertTrue('and <a href="http://www.wired.com/2015/10/meet-walking-dead-hp-cisco-dell-emc-ibm-oracle/" rel="external">wired.com/2015/10/meet-w…</a>' in tweet_html)

    def test_links_urls(self):
        tweet_html = htmlify_tweet(self.json_data)
        self.assertTrue('for <a href="https://twitter.com/philgyford" rel="external">@philgyford</a>' in tweet_html)
        self.assertTrue('and <a href="https://twitter.com/samuelpepys" rel="external">@samuelpepys</a>' in tweet_html)

    def test_links_hashtags(self):
        tweet_html = htmlify_tweet(self.json_data)
        self.assertTrue(' <a href="https://twitter.com/hashtag/testing" rel="external">#testing</a> and' in tweet_html)
        self.assertTrue(' <a href="https://twitter.com/hashtag/hashtag" rel="external">#hashtag</a> ' in tweet_html)

    def test_linebreaks(self):
        tweet_html = htmlify_tweet(self.json_data)
        self.assertTrue("""A<br>test for""" in tweet_html)

