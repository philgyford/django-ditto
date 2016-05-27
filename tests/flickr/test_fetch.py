import datetime
import json
import pytz
import responses
import urllib

from django.test import TestCase

from ditto.flickr.fetch.savers import SaveUtilsMixin


class SaveUtilsMixinTestCase(TestCase):
    """Not sure these tests are that useful, but still."""

    def test_api_datetime_to_datetime_default_tz(self):
        api_time = '1998-07-22 13:15:23'
        time1 = SaveUtilsMixin()._api_datetime_to_datetime(api_time)
        time2 = datetime.datetime.strptime(api_time, '%Y-%m-%d %H:%M:%S').replace(tzinfo=pytz.timezone('Etc/UTC'))
        self.assertEqual(time1, time2)

    def test_api_datetime_to_datetime_custom_tz(self):
        api_time = '1998-07-22 13:15:23'
        time1 = SaveUtilsMixin()._api_datetime_to_datetime(
                                            api_time, 'America/Los_Angeles')
        time2 = datetime.datetime.strptime(api_time, '%Y-%m-%d %H:%M:%S').replace(tzinfo=pytz.timezone('America/Los_Angeles'))
        self.assertEqual(time1, time2)

    def test_unixtime_to_datetime(self):
        api_time = '1093459273'
        time1 = SaveUtilsMixin()._unixtime_to_datetime(api_time)
        time2 = datetime.datetime.utcfromtimestamp(int(api_time))\
                                                    .replace(tzinfo=pytz.utc)
        self.assertEqual(time1, time2)


class FlickrFetchTestCase(TestCase):
    """Useful things used by subsequent test cases."""

    fixture_path = 'tests/flickr/fixtures/api/'

    flickr_fixtures = {
        'people.getPhotos':         'people_getphotos.json',
        'people.getInfo':           'people_getinfo.json',
        'photos.getInfo':           'photos_getinfo.json',
        'photos.getSizes':          'photos_getsizes.json',
        'photos.getExif':           'photos_getexif.json',
        'test.login':               'test_login.json',
        # Variation including video sizes:
        'photos.getSizes_video':    'photos_getsizes_video.json',
        'photosets.getList':        'photosets_getlist.json',
        'photosets.getPhotos':      'photosets_getphotos.json',
    }

    def load_raw_fixture(self, method):
        """Makes the JSON response to a call to the API.
        method -- Method name used in self.flickr_fixtures.
        Returns the JSON text.
        """
        json_file = open('%s%s' % (
                            self.fixture_path, self.flickr_fixtures[method]))
        json_data = json_file.read()
        json_file.close()
        return json_data

    def load_fixture(self, method):
        """Returns the json.loads() version of the JSON fixture. ie, a python
        list or dict, not plain text."""
        return json.loads(self.load_raw_fixture(method))

    def add_flickr_response(self, body, status=200, querystring={}, match_querystring=True):
        """Add a generic Flickr API response.

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

    def add_response(self, method, body=None, querystring={}):
        """Add a specific API response - useful for 99% of cases.
        method - API method name, like 'people.getInfo'.
        body -- Text body for the response. Otherwise, our standard fixture for
                    that method is used.
        querystring -- Optional keys/values for the querystring. Individual
                        items will override the defaults for each method below.
        """
        querystrings = {
            'people.getInfo':       {'user_id': '35034346050@N01', },
            'people.getPhotos':     {'user_id': '35034346050@N01',
                                    'min_upload_date': '946684800',
                                    'page': '1',
                                    'per_page': '500',},
            'photos.getInfo':       {'photo_id': '26069027966', },
            'photos.getSizes':      {'photo_id': '26069027966', },
            'photos.getExif':       {'photo_id': '26069027966', },
            'photosets.getList':    {'user_id': '35034346050@N01',
                                    'page': '1',
                                    'per_page': '500',},
            'photosets.getPhotos':  {'user_id': '35034346050@N01',
                                    'photoset_id': '72157665648859705',
                                    'page': '1',
                                    'per_page': '500',},
            'test.login':           {},
        }
        if body is None:
            body = self.load_raw_fixture(method)

        qs = querystrings[method]
        qs['method'] = 'flickr.'+method

        # Override or add to the defaults if other options are supplied.
        for k, v in querystring.items():
            qs[k] = v

        self.add_flickr_response(querystring=qs, body=body)

