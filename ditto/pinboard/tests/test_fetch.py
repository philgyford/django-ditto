# coding: utf-8
import datetime

from mock import patch
import requests
from requests.exceptions import ConnectionError, RequestException, Timeout, TooManyRedirects
import responses

from django.test import TestCase

from ..fetch import FetchBookmarks


class FetchTypesTestCase(TestCase):
    """Testing the various interface methods for fetching Bookmarks:
    fetch_all(), fetch_date(), fetch_recent() and fetch_url()
    """

    # ./demo/manage.py dumpdata pinboard.Account --indent 4 > ditto/pinboard/fixtures/fetch_bookmarks_test.json
    fixtures = ['fetch_bookmarks_test.json']

    def add_response(self, body, method='get', status=200):
        """If the URL given here is called, then the request is faked, and
        `body` is what will be returned from the request to the URL.
        `method` is 'get' or 'recent' or 'all'.
        """
        responses.add(
            responses.GET,
            'https://api.pinboard.in/v1/posts/%s' % method,
            status=status,
            match_querystring=False,
            body=body
        )

    def make_success_body(self, num_posts=1, post_date='2015-06-18', username='philgyford'):
        posts = []
        for n in range(0, num_posts):
            posts.append('{"href":"http:\\/\\/example%s.com\\/","description":"My description %s","extended":"My extended %s.","meta":"abcdef1234567890abcdef1234567890","hash":"1234567890abcdef1234567890abcdef","time":"%sT09:48:31Z","shared":"yes","toread":"no","tags":"tag1 tag2 tag3"}' % (n, n, n, post_date))

        return '{"date":"%sT09:48:31Z","user":"%s","posts":[%s]}\t\n' % (post_date, username, ','.join(posts))
        

    # Check that all interface methods return expected results on success.

    @responses.activate
    def test_fetch_all_success(self):
        self.add_response(method='all',
                                    body=self.make_success_body(num_posts=12))
        result = FetchBookmarks().fetch_all(username='philgyford')
        self.assertEqual(result[0]['account'], 'philgyford')
        self.assertTrue(result[0]['success'])
        self.assertEqual(result[0]['fetched'], 12)

    @responses.activate
    def test_fetch_date_success(self):
        self.add_response(body=self.make_success_body(num_posts=4))
        result = FetchBookmarks().fetch_date(
                                post_date='2015-06-18', username='philgyford')
        self.assertEqual(result[0]['account'], 'philgyford')
        self.assertTrue(result[0]['success'])
        self.assertEqual(result[0]['fetched'], 4)

    @responses.activate
    def test_fetch_url_success(self):
        self.add_response(body=self.make_success_body(num_posts=1))
        result = FetchBookmarks().fetch_url(
                                url='http://foo.com', username='philgyford')
        self.assertEqual(result[0]['account'], 'philgyford')
        self.assertTrue(result[0]['success'])
        self.assertEqual(result[0]['fetched'], 1)

    @responses.activate
    def test_fetch_recent_success(self):
        self.add_response(method='recent',
                                    body=self.make_success_body(num_posts=5))
        result = FetchBookmarks().fetch_recent(num=5, username='philgyford')
        self.assertEqual(result[0]['account'], 'philgyford')
        self.assertTrue(result[0]['success'])
        self.assertEqual(result[0]['fetched'], 5)


    # Check responses when bad data is supplied to interface methods.

    @patch('ditto.pinboard.fetch.FetchBookmarks._fetch')
    def test_fetch_date_invalid(self, fetch_method):
        result = FetchBookmarks().fetch_date('2015-06-99')
        assert not fetch_method.called
        self.assertFalse(result[0]['success'])
        self.assertEqual(result[0]['message'],
                                        "Invalid date format ('2015-06-99')")


    # Check multiple accounts.

    @responses.activate
    def test_fetch_multiple_accounts(self):
        # TODO: Because the actual URL of both these requests is the same,
        # only the first is used when the two requests get made in
        # FetchBookmarks()._send_request(). So this test isn't *really*
        # working properly. Not sure how to fix it.
        self.add_response(body=self.make_success_body(
                                        num_posts=3, username='philgyford'))
        self.add_response(body=self.make_success_body(
                                        num_posts=3, username='testuser'))
        result = FetchBookmarks().fetch_date(post_date='2015-06-18')
        self.assertEqual(result[0]['account'], 'philgyford')
        self.assertEqual(result[0]['fetched'], 3)
        self.assertEqual(result[1]['account'], 'testuser')
        self.assertEqual(result[1]['fetched'], 3)


    # Check parsing of JSON.
    # TODO


    # Check Bookmarks are created.
    # TODO


    # Check potential errors.

    @responses.activate
    def test_it_handles_exceptions(self):
        errors = ( 
            (ConnectionError,   "Can't connect to domain."),
            (Timeout,           "Connection timed out."),
            (TooManyRedirects,  "Too many redirects."),
            (RequestException,  "Something went wrong with the request."),
        ) 
        for error, message in errors:
            exception = error(message)
            self.add_response(body=exception)
            result = FetchBookmarks().fetch_date(post_date='2015-06-18',
                                                    username='philgyford')
            self.assertFalse(result[0]['success'])
            self.assertEqual(result[0]['message'], message)
            responses.reset()

    @responses.activate
    def test_it_handles_404s(self):
        self.add_response(body='<h1>Not found</h1>', status=404)
        result = FetchBookmarks().fetch_date(post_date='2015-06-18',
                                                username='philgyford')
        self.assertFalse(result[0]['success'])
        self.assertEqual(result[0]['message'], 'HTTP Error: 404')

    @responses.activate
    def test_it_handles_500s(self):
        self.add_response(body='<h1>Error</h1>', status=500)
        result = FetchBookmarks().fetch_date(post_date='2015-06-18',
                                                username='philgyford')
        self.assertFalse(result[0]['success'])
        self.assertEqual(result[0]['message'], 'HTTP Error: 500')

