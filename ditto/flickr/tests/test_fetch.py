import datetime
import json
from unittest.mock import call, patch
import urllib

import pytz
import responses
from freezegun import freeze_time

from django.test import TestCase

from ..factories import AccountFactory, UserFactory
from ..fetch import UserMixin, UserFetcher
from ..models import User


class FetcherTestCase(TestCase):

    # A JSON file to use for the response body.
    # eg 'ditto/flickr/fixtures/api/user.json'
    api_fixture = ''

    def make_response_body(self, fixture=None):
        """Makes the JSON response to a call to the API
        fixture -- Path to a JSON fixture file. Else, self.api_fixture is used.
        Returns the JSON text.
        """
        if fixture is None:
            fixture = self.api_fixture
        json_file = open(fixture)
        json_data = json_file.read()
        json_file.close()
        return json_data

    def add_response(self, body, status=200, querystring={}, match_querystring=True):
        """Add a Flickr API response.

        Keyword arguments:
        body -- The JSON string representing the body of the response.
        status -- Int, HTTP response status.
        querystring -- eg {}
        match_querystring -- You probably want this to be True if you've set
                             a querystring.
        """
        url = 'https://api.flickr.com/services/rest/'

        if len(querystring):

            # I *think* we'll need these for all Flickr queries:
            querystring['nojsoncallback'] = '1'
            querystring['format'] = 'json'

            qs = '&'.join(
                    "%s=%s" % (key, urllib.parse.quote_plus(querystring[key]))
                                                for key in querystring.keys())
            url = '%s?%s' % (url, qs)

        responses.add(
            responses.POST,
            url,
            status=status,
            match_querystring=match_querystring,
            body=body,
            content_type='application/json; charset=utf-8'
        )


class UserFetcherTestCase(FetcherTestCase):

    api_fixture = 'ditto/flickr/fixtures/api/people_getinfo.json'

    def setUp(self):
        self.account = AccountFactory(api_key='1234', api_secret='9876')

    def add_lookupurl_response(self, body=None):
        "Wrapper for add_response() for a particular Flickr query."
        if body is None:
            body = self.make_response_body(
                            'ditto/flickr/fixtures/api/urls_lookupuser.json')
        self.add_response(
            body=body,
            querystring={
                'method': 'flickr.urls.lookupUser',
                'url': 'https://www.flickr.com/photos/test/',
            }
        )

    def add_getinfo_response(self, body=None):
        "Wrapper for add_response() for a particular Flickr query."
        if body is None:
            body = self.make_response_body()
        self.add_response(
            body=body,
            querystring={
                'method': 'flickr.people.getInfo',
                'user_id': '35034346050@N01',
            }
        )

    @responses.activate
    def test_makes_two_api_calls(self):
        "Should call urls.lookupUser and people.getInfo"
        self.add_lookupurl_response()
        self.add_getinfo_response()
        result = UserFetcher().fetch(url='https://www.flickr.com/photos/test/')
        self.assertEqual(2, len(responses.calls))

    @responses.activate
    def test_returns_correct_success_result(self):
        self.add_lookupurl_response()
        self.add_getinfo_response()
        result = UserFetcher().fetch(url='https://www.flickr.com/photos/test/')

        self.assertTrue(len(result), 1)
        self.assertIn('success', result[0])
        self.assertTrue(result[0]['success'])
        self.assertIn('fetched', result[0])
        self.assertEqual(result[0]['fetched'], 1)

    @responses.activate
    def test_returns_correct_error_result_1(self):
        "When the url.lookUp request fails."
        self.add_lookupurl_response(
            body='{"stat": "fail", "code": 1, "message": "User not found"}')
        result = UserFetcher().fetch(url='https://www.flickr.com/photos/test/')

        self.assertTrue(len(result), 1)
        self.assertIn('success', result[0])
        self.assertFalse(result[0]['success'])
        self.assertIn('message', result[0])

    @responses.activate
    def test_returns_correct_error_result_2(self):
        "When the people.getInfo request fails."
        self.add_lookupurl_response()
        self.add_getinfo_response(
            body='{"stat": "fail", "code": 1, "message": "User not found"}')
        result = UserFetcher().fetch(url='https://www.flickr.com/photos/test/')

        self.assertTrue(len(result), 1)
        self.assertIn('success', result[0])
        self.assertFalse(result[0]['success'])
        self.assertIn('message', result[0])

    @responses.activate
    @patch('ditto.flickr.fetch.UserMixin.save_user')
    @freeze_time("2015-08-14 12:00:00", tz_offset=-8)
    def test_calls_save_user_correctly(self, save_user):
        save_user.side_effect = [UserFactory()]
        self.add_lookupurl_response()
        self.add_getinfo_response()
        result = UserFetcher().fetch(url='https://www.flickr.com/photos/test/')

        user_response = json.loads(self.make_response_body())

        save_user.assert_called_once_with(user_response,
                        datetime.datetime.utcnow().replace(tzinfo=pytz.utc))


class UserMixinTestCase(FetcherTestCase):

    api_fixture = 'ditto/flickr/fixtures/api/people_getinfo.json'

    def make_user_object(self, user_data):
        """"Creates/updates a User from API data, then fetches that User from
        the DB and returns it.
        """
        fetch_time = datetime.datetime.utcnow().replace(tzinfo=pytz.utc)
        saved_user = UserMixin().save_user(user_data, fetch_time)
        return User.objects.get(nsid="35034346050@N01")

    @freeze_time("2015-08-14 12:00:00", tz_offset=-8)
    def test_saves_correct_user_data(self):
        """Passing save_user() data from the API should create a new User."""
        user_data = json.loads(self.make_response_body())
        user = self.make_user_object(user_data)

        self.assertEqual(user.fetch_time,
                            datetime.datetime.utcnow().replace(tzinfo=pytz.utc))
        self.assertEqual(user.raw, json.dumps(user_data))
        self.assertEqual(user.nsid, "35034346050@N01")
        self.assertTrue(user.is_pro)
        self.assertEqual(user.iconserver, '7420')
        self.assertEqual(user.iconfarm, 8)
        self.assertEqual(user.username, 'Phil Gyford')
        self.assertEqual(user.realname, 'Phil Gyford')
        self.assertEqual(user.location, 'London, UK')
        self.assertEqual(user.description, 'A test description.')
        self.assertEqual(user.photos_url, 'https://www.flickr.com/photos/philgyford/')
        self.assertEqual(user.profile_url, 'https://www.flickr.com/people/philgyford/')
        self.assertEqual(user.photos_count, 2876)
        self.assertEqual(user.photos_first_date, datetime.datetime.utcfromtimestamp(1093459273).replace(tzinfo=pytz.utc))
        self.assertEqual(user.photos_first_date_taken,
                                datetime.datetime.strptime(
                                    '1956-01-01 00:00:00', '%Y-%m-%d %H:%M:%S'
                                ).replace(tzinfo=pytz.utc))
        self.assertEqual(user.photos_views, 227227)

    @freeze_time("2015-08-14 12:00:00", tz_offset=-8)
    def test_updates_existing_user(self):
        """Passing save_user() data from the API should update an existing
        User.
        """
        # Some data that will be updated:
        existing_user = User(nsid="35034346050@N01",
                            iconfarm=3,
                            is_pro=False,
                            username="Bob",
                            location="San Francisco",
                            photos_count=3,
                            photos_views=3)
        existing_user.save()

        user_data = json.loads(self.make_response_body())
        user = self.make_user_object(user_data)

        self.assertTrue(user.is_pro)
        self.assertEqual(user.username, 'Phil Gyford')
        self.assertEqual(user.location, 'London, UK')
        self.assertEqual(user.photos_count, 2876)
        self.assertEqual(user.photos_views, 227227)

