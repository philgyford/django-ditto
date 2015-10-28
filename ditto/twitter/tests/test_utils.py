# coding: utf-8
import json
from django.test import TestCase

from ..utils import htmlify_tweet


class UtilsHtmlifyTestCase(TestCase):

    api_fixture = 'ditto/twitter/fixtures/api/tweet_with_entities.json'

    def setUp(self):
        json_file = open(self.api_fixture)
        self.json_data = json.loads(json_file.read())
        json_file.close()

    def test_links_urls(self):
        "Makes 'urls' entities into clickable links."
        tweet_html = htmlify_tweet(self.json_data)
        self.assertTrue('with <a href="http://www.bbc.co.uk/news/business-34505593" rel="external">bbc.co.uk/news/business-…</a>' in tweet_html)
        self.assertTrue('and <a href="http://www.wired.com/2015/10/meet-walking-dead-hp-cisco-dell-emc-ibm-oracle/" rel="external">wired.com/2015/10/meet-w…</a>' in tweet_html)

    def test_links_old_urls(self):
        """If a tweet contians a URL but there are no 'urls' entities, like old
        Tweets, still turn the URL into a clickable link.
        """
        self.json_data['entities']['urls'] = []
        tweet_html = htmlify_tweet(self.json_data)
        self.assertTrue('with <a href="http://t.co/cOu05x0Chi">http://t.co/cOu05x0Chi</a>' in tweet_html)
        self.assertTrue('and <a href="http://t.co/S9fH3CkgV4">http://t.co/S9fH3CkgV4</a>' in tweet_html)

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

    def test_linebreaks(self):
        "Turns linebreaks into <br>s"
        tweet_html = htmlify_tweet(self.json_data)
        self.assertTrue("""A<br>test for""" in tweet_html)

