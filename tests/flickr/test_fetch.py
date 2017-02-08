import datetime
import json
import pytz
import responses
import urllib
from six.moves.urllib.parse import parse_qs

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

    def setUp(self):
        super(FlickrFetchTestCase, self).setUp()
        self.mock = responses.RequestsMock(assert_all_requests_are_fired=True)
        self.mock.start()

    def tearDown(self):
        self.mock.stop()
        self.mock.reset()
        super(FlickrFetchTestCase, self).tearDown()

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

    def expect(self, params=None, body='', status=200,
                content_type='application/json; charset=utf-8',
                method='POST', match_querystring=True):
        """Mocks an expected HTTP query with Responses.
        Mostly copied from https://github.com/sybrenstuvel/flickrapi/blob/master/tests/test_flickrapi.py
        """
        urlbase = 'https://api.flickr.com/services/rest/'

        param_test_callback = None
        url = urlbase

        if params:
            # Parameters we'll always want:
            params.setdefault('format', 'json')
            params.setdefault('nojsoncallback', '1')

        if method == 'GET':
            # The parameters should be on the URL.
            qp = quote_plus
            qs = '&'.join('%s=%s' % (
                            qp(key), qp(six.text_type(value).encode('utf-8'))
                        )
                          for key, value in sorted(params.items())
                        )
            if qs:
                url = '%s?%s' % (urlbase, qs)

            self.mock.add(method=method, url=url,
                          body=body, status=status,
                          content_type=content_type,
                          match_querystring=match_querystring)
        else:
            # The parameters should be in the request body, not on the URL.
            if params is not None:
                expect_params = {key.encode('utf8'): [value.encode('utf8')]
                                 for key, value in params.items()}

            def param_test_callback(request):
                # This callback can only handle x-www-form-urlencoded requests.
                self.assertEqual('application/x-www-form-urlencoded',
                                 request.headers['Content-Type'].decode('utf8'))
                actual_params = parse_qs(request.body)
                if params is None:
                    self.assertFalse(actual_params)
                else:
                    self.assertEqual(actual_params, expect_params)

                headers = {'Content-Type': 'application/json; charset=utf-8'}
                return (status, headers, body)

            self.mock.add_callback(method=method, url=url,
                                   callback=param_test_callback,
                                   content_type=content_type,
                                   match_querystring=match_querystring)

    def expect_response(self, method, body=None, params=None):
        """Add a specific API response - useful for 99% of cases.
        method - API method name, like 'people.getInfo'.
        body -- Text body for the response. Otherwise, our standard fixture for
                    that method is used.
        params -- Optional keys/values for the request. Individual
                        items will override the defaults for each method below.
        """
        # Our default test params for each Flickr API method:
        method_params = {
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

        if params is None:
            params = {}

        # Use the method's default params unless we've specified otherwise:
        for k, v in method_params[method].items():
            params.setdefault(k, v)

        # Add the param specifying the API method:
        params.setdefault('method', 'flickr.{}'.format(method))

        self.expect(params=params, body=body)

