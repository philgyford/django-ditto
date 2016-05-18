# coding: utf-8
import datetime
import json

from unittest.mock import patch
from freezegun import freeze_time
import pytz
from requests.exceptions import ConnectionError, RequestException, Timeout, TooManyRedirects
import responses

from django.test import TestCase

from ditto.pinboard.factories import AccountFactory, BookmarkFactory
from ditto.pinboard.fetch import BookmarksFetcher, AllBookmarksFetcher,\
        DateBookmarksFetcher, RecentBookmarksFetcher, UrlBookmarksFetcher,\
        FetchError
from ditto.pinboard.models import Account, Bookmark, BookmarkTag


class FetchTestCase(TestCase):

    def setUp(self):
        self.user_1 = AccountFactory(username='philgyford',
                                    url='https://pinboard.in/u:philgyford',
                                    api_token='philgyford:1234567890ABCDEFGHIJ')
        self.user_2 = AccountFactory(username='testuser',
                                    url='https://pinboard.in/u:testuser',
                                    api_token='testuser:ABCDEFGHIJ1234567890')


class FetchTypesTestRemoteCase(FetchTestCase):
    """Testing the various classes for fetching remote Bookmarks
    data: AllBookmarksFetcher, DateBookmarksFetcher, etc.
    """

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

    def make_success_body(self, method='date', num_posts=1, post_date='2015-06-18', username='philgyford'):
        """Makes JSON representing a number of bookmarks.
        `method` is 'get' or 'recent' or 'all'.
        """
        posts = []
        for n in range(0, num_posts):
            posts.append('{"href":"http:\\/\\/example%s.com\\/","description":"My description %s","extended":"My extended %s.","meta":"abcdef1234567890abcdef1234567890","hash":"1234567890abcdef1234567890abcdef","time":"%sT09:48:31Z","shared":"yes","toread":"no","tags":"tag1 tag2 tag3"}' % (n, n, n, post_date))

        posts_json = '[%s]\t\n'  % (','.join(posts))

        if method == 'all':
            return posts_json
        else:
            return '{"date":"%sT09:48:31Z","user":"%s","posts":%s}\t\n' % (post_date, username, posts_json)


    # Check that all interface methods return expected results on success.

    @responses.activate
    def test_fetch_all_success(self):
        """Successfully fetches all bookmarks"""
        self.add_response(
                method='all',
                body=self.make_success_body(method='all', num_posts=12)
            )
        result = AllBookmarksFetcher().fetch(username='philgyford')
        self.assertEqual(result[0]['account'], 'philgyford')
        self.assertTrue(result[0]['success'])
        self.assertEqual(result[0]['fetched'], 12)

    @responses.activate
    def test_fetch_date_success(self):
        """Successfully fetches bookmarks for a particular date"""
        self.add_response(body=self.make_success_body(num_posts=4))
        result = DateBookmarksFetcher().fetch(
                                post_date='2015-06-18', username='philgyford')
        self.assertEqual(result[0]['account'], 'philgyford')
        self.assertTrue(result[0]['success'])
        self.assertEqual(result[0]['fetched'], 4)

    @responses.activate
    def test_fetch_url_success(self):
        """Sucessfully fetches the one bookmark for a URL"""
        self.add_response(body=self.make_success_body(num_posts=1))
        result = UrlBookmarksFetcher().fetch(
                                url='http://foo.com', username='philgyford')
        self.assertEqual(result[0]['account'], 'philgyford')
        self.assertTrue(result[0]['success'])
        self.assertEqual(result[0]['fetched'], 1)

    @responses.activate
    def test_fetch_recent_success(self):
        """Successfully fetches recent bookmarks"""
        self.add_response(method='recent',
                                    body=self.make_success_body(num_posts=5))
        result = RecentBookmarksFetcher().fetch(num=5, username='philgyford')
        self.assertEqual(result[0]['account'], 'philgyford')
        self.assertTrue(result[0]['success'])
        self.assertEqual(result[0]['fetched'], 5)

    # Check responses when bad data is supplied to interface methods.

    @patch.object(BookmarksFetcher, '_fetch')
    def test_fetch_date_invalid(self, fetch_method):
        """Correctly reacts to an invalid date"""
        with self.assertRaises(FetchError):
            result = DateBookmarksFetcher().fetch('2015-06-99')
        assert not fetch_method.called


    # Check multiple accounts.

    @responses.activate
    def test_fetch_multiple_accounts(self):
        """Successfully fetches bookmarks when there are multiple accounts."""
        # TODO: Because the actual URL of both these requests is the same,
        # only the first is used when the two requests get made in
        # BookmarksFetcher()._send_request(). So this test isn't *really*
        # working properly. Not sure how to fix it.
        self.add_response(body=self.make_success_body(
                                        num_posts=3, username='philgyford'))
        self.add_response(body=self.make_success_body(
                                        num_posts=3, username='testuser'))
        result = DateBookmarksFetcher().fetch(post_date='2015-06-18')
        self.assertEqual(result[0]['account'], 'philgyford')
        self.assertEqual(result[0]['fetched'], 3)
        self.assertEqual(result[1]['account'], 'testuser')
        self.assertEqual(result[1]['fetched'], 3)


    # Check potential errors.

    @responses.activate
    def test_it_handles_exceptions(self):
        """Correctly handles various errors when fetching bookmarks"""
        errors = (
            (ConnectionError,   "Can't connect to domain."),
            (Timeout,           "Connection timed out."),
            (TooManyRedirects,  "Too many redirects."),
            (RequestException,  "Something went wrong with the request."),
        )
        for error, message in errors:
            exception = error(message)
            self.add_response(body=exception)
            results = DateBookmarksFetcher().fetch(post_date='2015-06-18',
                                                    username='philgyford')
            self.assertFalse(results[0]['success'])
            responses.reset()

    @responses.activate
    def test_it_handles_404s(self):
        """Correctly reacts to a 404 when fetching bookmarks"""
        self.add_response(body='<h1>Not found</h1>', status=404)
        results = DateBookmarksFetcher().fetch(post_date='2015-06-18',
                                                        username='philgyford')
        self.assertFalse(results[0]['success'])
        self.assertEqual(results[0]['messages'][0], 'HTTP Error: 404')

    @responses.activate
    def test_it_handles_429s(self):
        """Correctly reacts to a 429 when fetching bookmarks"""
        self.add_response(body='<h1>Too Many Requests</h1>', status=429)
        results = DateBookmarksFetcher().fetch(post_date='2015-06-18',
                                                        username='philgyford')
        self.assertFalse(results[0]['success'])
        self.assertEqual(results[0]['messages'][0], 'HTTP Error: 429')

    @responses.activate
    def test_it_handles_500s(self):
        """Correctly reacts to a 500 error when fetching bookmarks"""
        self.add_response(body='<h1>Error</h1>', status=500)
        results = DateBookmarksFetcher().fetch(post_date='2015-06-18',
                                                        username='philgyford')
        self.assertFalse(results[0]['success'])
        self.assertEqual(results[0]['messages'][0], 'HTTP Error: 500')


class FetchInactiveAccountsTestCase(TestCase):

    def test_only_inactive_account(self):
        "Correctly reacts if only an inactive Account is tried"
        account = AccountFactory(username='philgyford', is_active=False)
        with self.assertRaises(FetchError):
            result = RecentBookmarksFetcher().fetch(username='philgyford')

    def test_inactive_accounts(self):
        "Correctly reacts fetching all accounts but all are inactive"
        account_1 = AccountFactory(username='philgyford', is_active=False)
        account_2 = AccountFactory(username='testuser', is_active=False)
        with self.assertRaises(FetchError):
            result = RecentBookmarksFetcher().fetch()


class FetchTypesSaveTestCase(FetchTestCase):
    """Ignoring the stuff for fetching remote data, given some successfully-
    fetched JSON, does parsing and saving work OK?
    """

    # Path to the file we'll use as a mock response from Pinboard.
    api_fixture = 'tests/pinboard/fixtures/api/bookmarks_2015-06-24.json'


    def get_bookmarks_from_json(self):
        """Parse our dummy JSON API response and return the raw JSON data and
        what should be a list of correctly-parsed data about Bookmarks, ready
        to make Bookmark objects out of.
        """
        json_file = open(self.api_fixture)
        json_data = json_file.read()
        bookmarks_data = BookmarksFetcher()._parse_response('date', json_data)
        json_file.close()

        return {'json': json_data,
                'bookmarks': bookmarks_data}

    # Check parsing of JSON.

    def test_fetch_json_parsing(self):
        """Ensure this method takes a piece of JSON and does the correct
        munging, returning the result.
        """
        bookmarks_from_json = self.get_bookmarks_from_json()
        bookmarks_data = bookmarks_from_json['bookmarks']

        # Check time has been turned into an object.
        self.assertEqual(bookmarks_data[0]['time'],
                            datetime.datetime.strptime(
                                '2015-06-18T09:48:31Z',
                                '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=pytz.utc))

        # Check 'yes'/'no' have been turned into booleans:
        self.assertTrue(bookmarks_data[0]['shared'])
        self.assertFalse(bookmarks_data[0]['toread'])
        self.assertFalse(bookmarks_data[1]['shared'])
        self.assertTrue(bookmarks_data[1]['toread'])

        self.assertEqual(bookmarks_data[0]['tags'],
                            ['fonts', 'icons', 'webdevelopment', 'webdesign'])
        self.assertEqual(bookmarks_data[1]['tags'], ['mattwebb', 'chatbots'])

        # Check it has a 'json' element that is the JSON version of the
        # bookmark:
        raw = json.loads(bookmarks_data[0]['json'])
        self.assertEqual(raw['description'], "Fontello - icon fonts generator")


    # Check Bookmarks are created/updated.

    @freeze_time("2015-07-01 12:00:00", tz_offset=-8)
    def test_save_bookmarks(self):
        """Ensure this method takes some parsed JSON and creates saved
        Bookmark objects.
        """
        account = Account.objects.get(pk=1)
        fetch_time = datetime.datetime.utcnow().replace(tzinfo=pytz.utc)

        bookmarks_from_json = self.get_bookmarks_from_json()
        bookmarks_data = bookmarks_from_json['bookmarks']
        json_data = bookmarks_from_json['json']

        raw_bookmark = json.dumps(json.loads(json_data)['posts'][0])

        BookmarksFetcher()._save_bookmarks(
                            account=account,
                            bookmarks_data=bookmarks_data,
                            fetch_time=fetch_time)

        self.assertEqual(Bookmark.objects.all().count(), 2)

        # Note: they're returned with most recent post_time first:
        bookmarks = Bookmark.objects.all()

        self.assertEqual(bookmarks[1].title, 'Fontello - icon fonts generator')

        self.assertEqual(bookmarks[1].fetch_time, datetime.datetime.strptime(
                            '2015-07-01 12:00:00',
                            '%Y-%m-%d %H:%M:%S').replace(tzinfo=pytz.utc))
        self.assertEqual(bookmarks[1].summary, 'Create your own icon font using only the icons you need, select from Font Awesome and other free libraries.')
        self.assertEqual(bookmarks[1].raw, raw_bookmark)
        self.assertEqual(bookmarks[1].account, account)
        self.assertEqual(bookmarks[1].url, 'http://fontello.com/')
        self.assertEqual(bookmarks[1].post_time, datetime.datetime.strptime(
                                '2015-06-18T09:48:31Z',
                                '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=pytz.utc))
        self.assertEqual(bookmarks[1].description, 'Create your own icon font using only the icons you need, select from Font Awesome and other free libraries.')

        self.assertFalse(bookmarks[1].is_private)
        self.assertFalse(bookmarks[1].to_read)
        self.assertTrue(bookmarks[0].is_private)
        self.assertTrue(bookmarks[0].to_read)

        self.assertEqual(len(bookmarks[1].tags.all()), 4)
        self.assertEqual(len(bookmarks[0].tags.all()), 2)
        self.assertIsInstance(bookmarks[1].tags.first(), BookmarkTag)
        self.assertEqual(sorted(list(bookmarks[1].tags.slugs()))[0], 'fonts')

    @freeze_time("2015-07-01 12:00:00", tz_offset=-8)
    def test_update_bookmarks(self):
        """Ensure that when saving a Bookmark that already exists, we update
        it."""
        account = Account.objects.get(pk=1)
        fetch_time = datetime.datetime.utcnow().replace(tzinfo=pytz.utc)

        # Add a Bookmark into the DB before we fetch anything.
        bookmark = BookmarkFactory(
                        account=account,
                        title='My initial title',
                        is_private=True,
                        to_read=True,
                        description='My initial description',
                        url='http://fontello.com/')
        bookmark.tags.set('initial', 'tags')

        bookmarks_from_json = self.get_bookmarks_from_json()
        bookmarks_data = bookmarks_from_json['bookmarks']

        BookmarksFetcher()._save_bookmarks(
                            account=account,
                            bookmarks_data=bookmarks_data,
                            fetch_time=fetch_time)

        self.assertEqual(Bookmark.objects.all().count(), 2)

        bookmarks = Bookmark.objects.all()

        self.assertEqual(bookmarks[1].title, 'Fontello - icon fonts generator')
        self.assertFalse(bookmarks[1].is_private)
        self.assertFalse(bookmarks[1].to_read)
        self.assertEqual(bookmarks[1].description, 'Create your own icon font using only the icons you need, select from Font Awesome and other free libraries.')
        # This should be updated to now, as we've changed things:
        self.assertEqual(bookmarks[1].fetch_time, datetime.datetime.strptime(
                            '2015-07-01 12:00:00',
                            '%Y-%m-%d %H:%M:%S').replace(tzinfo=pytz.utc))

        self.assertEqual(len(bookmarks[1].tags.all()), 4)
        self.assertIsInstance(bookmarks[1].tags.first(), BookmarkTag)
        self.assertEqual(sorted(list(bookmarks[1].tags.slugs()))[0], 'fonts')

    @freeze_time("2015-07-01 12:00:00", tz_offset=-8)
    def test_no_update_bookmarks(self):
        """Ensure that if no values have changed, we don't update a bookmark.
        """
        account = Account.objects.get(pk=1)
        fetch_time = datetime.datetime.utcnow().replace(tzinfo=pytz.utc)

        # Add a Bookmark into the DB before we fetch anything.
        bookmark = BookmarkFactory(
                        account=account,
                        title='Fontello - icon fonts generator',
                        is_private=False,
                        to_read=False,
                        description='Create your own icon font using only the icons you need, select from Font Awesome and other free libraries.',
                        url='http://fontello.com/',
                        raw='{"extended": "Create your own icon font using only the icons you need, select from Font Awesome and other free libraries.", "hash": "df25b37a14ed631a0111a647e53fc24e", "description": "Fontello - icon fonts generator", "tags": "fonts icons webdevelopment webdesign", "href": "http://fontello.com/", "meta": "20e8a3c17e9424c7fb6121d0c6961861", "time": "2015-06-18T09:48:31Z", "shared": "yes", "toread": "no"}',
                        fetch_time=fetch_time)

        bookmarks_from_json = self.get_bookmarks_from_json()
        bookmarks_data = bookmarks_from_json['bookmarks']

        BookmarksFetcher()._save_bookmarks(
                            account=account,
                            bookmarks_data=bookmarks_data,
                            fetch_time=fetch_time)

        self.assertEqual(Bookmark.objects.all().count(), 2)

        bookmarks = Bookmark.objects.all()

        # Nothing has changed, and so the fetch_time should be the original:
        self.assertEqual(bookmarks[0].fetch_time, fetch_time)

