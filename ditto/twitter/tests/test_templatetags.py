from django.test import TestCase

from .. templatetags import twitter_tags


class TemplateTagTests(TestCase):

    def test_tweet_usernames(self):
        "Should turn @names into links."
        tweet = 'Hello @bob, OK?'
        self.assertEqual(twitter_tags.tweet(tweet),
            'Hello <a href="https://twitter.com/bob" rel="external">@bob</a>, OK?')

    def test_tweet_hashtags(self):
        "Should turn #hashtags into links."
        tweet = 'This #thingy, OK?'
        self.assertEqual(twitter_tags.tweet(tweet),
            'This <a href="https://twitter.com/hashtag/thingy?src=hash" rel="external">#thingy</a>, OK?')

    def test_tweet_links(self):
        "Should turn URLs into links"
        tweet = 'This http://example.org/blah here'
        self.assertEqual(twitter_tags.tweet(tweet),
            'This <a href="http://example.org/blah" rel="external nofollow">http://example.org/blah</a> here')

    def test_tweet_linebreaks(self):
        "Should replace <br> tags with linebreaks"
        tweet = """   First line.
Second line.
Final line.
"""
        self.assertEqual(twitter_tags.tweet(tweet),
            'First line.<br>Second line.<br>Final line.')

