import calendar
import datetime
import json
import os
import pytz
import tempfile
from unittest.mock import call, patch

import responses
from flickrapi.exceptions import FlickrError
from freezegun import freeze_time
from django.test import override_settings, TestCase

from .test_fetch import FlickrFetchTestCase
from ditto.core.utils import datetime_now
from ditto.core.utils.downloader import filedownloader
from ditto.flickr.factories import AccountFactory, PhotoFactory, UserFactory
from ditto.flickr.fetch import FetchError
from ditto.flickr.fetch.fetchers import Fetcher, PhotosFetcher,\
    PhotosetsFetcher, RecentPhotosFetcher, UserFetcher, UserIdFetcher
from ditto.flickr.fetch.savers import UserSaver, PhotoSaver, PhotosetSaver
from ditto.flickr.models import User


class FetcherTestCase(FlickrFetchTestCase):

    def test_account_with_no_user(self):
        """If Account has no user should set 'account' value appropriately."""
        account = AccountFactory(user=None)
        result = Fetcher(account=account).fetch()
        self.assertFalse(result['success'])
        self.assertIn('messages', result)
        self.assertEqual(result['account'], 'Account: 1')

    def test_with_unsaved_account(self):
        """If Account is unsaved, should set 'account' value appropriately."""
        account = AccountFactory.build(user=None)
        result = Fetcher(account=account).fetch()
        self.assertFalse(result['success'])
        self.assertIn('messages', result)
        self.assertEqual(result['account'], 'Unsaved Account')

    def test_returns_false_with_no_creds(self):
        """Success is false if Account has no API credentials"""
        account = AccountFactory(user=UserFactory(username='bob'))
        result = Fetcher(account=account).fetch()
        self.assertFalse(result['success'])
        self.assertIn('messages', result)
        self.assertEqual(result['account'], 'bob')

    def test_requires_an_account_argument(self):
        with self.assertRaises(TypeError):
            result = Fetcher()

    def test_requires_valid_account_object(self):
        with self.assertRaises(ValueError):
            result = Fetcher(account=None)

    @patch.object(Fetcher, '_fetch_extra')
    @patch.object(Fetcher, '_call_api')
    def test_returns_false_when_extra_data_fetching_fails(self, call_api, fetch_extra):
        fetch_extra.side_effect = FetchError('Oh dear')
        account = AccountFactory(user=UserFactory(username='terry'),
                                            api_key='1234', api_secret='9876')
        result = Fetcher(account=account).fetch()
        self.assertFalse(result['success'])
        self.assertIn('Oh dear', result['messages'][0])

    @patch.object(Fetcher, '_call_api')
    @patch.object(Fetcher, '_save_results')
    def test_returns_true_with_creds(self, save_results, call_api):
        """Success is true if Account has API credentials"""
        account = AccountFactory(user=UserFactory(username='terry'),
                                            api_key='1234', api_secret='9876')
        result = Fetcher(account=account).fetch()
        self.assertEqual(result['account'], 'terry')
        self.assertTrue(result['success'])
        self.assertEqual(result['fetched'], 0)

    def test_failure_with_no_child_call_api(self):
        """Requires a child class to set its own _call_api()."""
        account = AccountFactory(user=UserFactory(username='terry'),
                                            api_key='1234', api_secret='9876')
        result = Fetcher(account=account).fetch()
        self.assertFalse(result['success'])
        self.assertIn('messages', result)

    @patch.object(Fetcher, '_call_api')
    def test_failure_with_no_child_save_results(self, call_api):
        """Requires a child class to set its own _call_api()."""
        account = AccountFactory(user=UserFactory(username='terry'),
                                            api_key='1234', api_secret='9876')
        result = Fetcher(account=account).fetch()
        self.assertFalse(result['success'])
        self.assertIn('messages', result)


class UserIdFetcherTestCase(FlickrFetchTestCase):

    def setUp(self):
        self.account = AccountFactory(api_key='1234', api_secret='9876')

    def test_inherits_from_fetcher(self):
        self.assertTrue( issubclass(UserFetcher, Fetcher) )

    @responses.activate
    def test_failure_if_api_call_fails(self):
        self.add_response('test.login',
            body='{"stat": "fail", "code": 99, "message": "Insufficient permissions. Method requires read privileges; none granted."}')
        result = UserIdFetcher(account=self.account).fetch()
        self.assertFalse(result['success'])
        self.assertIn('messages', result)

    @responses.activate
    def test_returns_id(self):
        self.add_response('test.login')
        result = UserIdFetcher(account=self.account).fetch()
        self.assertTrue(result['success'])
        self.assertIn('id', result)
        self.assertEqual(result['id'], '35034346050@N01')


class UserFetcherTestCase(FlickrFetchTestCase):

    def setUp(self):
        self.account = AccountFactory(api_key='1234', api_secret='9876')

    def test_inherits_from_fetcher(self):
        self.assertTrue( issubclass(UserFetcher, Fetcher) )

    def test_failure_with_no_id(self):
        """Raises FetchError if we don't pass an ID to fetch()"""
        with self.assertRaises(FetchError):
            result = UserFetcher(account=self.account).fetch()

    @responses.activate
    def test_failure_if_getinfo_fails(self):
        "Fails correctly if the call to people.getInfo fails"
        self.add_response('people.getInfo',
                body='{"stat": "fail", "code": 1, "message": "User not found"}')
        result = UserFetcher(account=self.account).fetch(
                                                        nsid='35034346050@N01')

        self.assertFalse(result['success'])
        self.assertIn('messages', result)

    @responses.activate
    @patch.object(UserFetcher, '_fetch_and_save_avatar')
    def test_makes_one_api_call(self, fetch_avatar):
        "Should call people.getInfo"
        self.add_response('people.getInfo')
        result = UserFetcher(account=self.account).fetch(
                                                        nsid='35034346050@N01')
        self.assertEqual(len(responses.calls), 1)

    @responses.activate
    @freeze_time("2015-08-14 12:00:00", tz_offset=-8)
    @patch.object(UserFetcher, '_fetch_and_save_avatar')
    @patch.object(UserSaver, 'save_user')
    def test_calls_save_user_correctly(self, save_user, fetch_avatar):
        "The correct data should be sent to UserSaver.save_user()"
        self.add_response('people.getInfo')
        result = UserFetcher(account=self.account).fetch(
                                                        nsid='35034346050@N01')
        user_response = self.load_fixture('people.getInfo')

        save_user.assert_called_once_with(
                                    user_response['person'], datetime_now())

    @responses.activate
    @override_settings(MEDIA_ROOT=tempfile.gettempdir())
    @patch.object(filedownloader, 'download')
    def test_downloads_and_saves_avatar(self, download):
        "Should call download() and save avatar when fetching user."
        # Make a temporary file, like download() would make:
        jpg = tempfile.NamedTemporaryFile()
        temp_filepath = jpg.name
        download.return_value = temp_filepath

        self.add_response('people.getInfo')
        result = UserFetcher(account=self.account).fetch(
                                                        nsid='35034346050@N01')

        user = User.objects.get(nsid='35034346050@N01')

        download.assert_called_once_with(user.original_icon_url,
                        ['image/jpeg', 'image/jpg', 'image/png', 'image/gif'])

        self.assertEqual(user.avatar,
            'flickr/60/50/35034346050N01/avatars/%s' %
                                            os.path.basename(temp_filepath))

    @responses.activate
    def test_returns_correct_success_result(self):
        self.add_response('people.getInfo')
        result = UserFetcher(account=self.account).fetch(
                                                        nsid='35034346050@N01')

        self.assertIn('success', result)
        self.assertTrue(result['success'])
        self.assertIn('fetched', result)
        self.assertEqual(result['fetched'], 1)


class PhotosFetcherTestCase(FlickrFetchTestCase):
    """Testing the parent class that's used for all kinds of fetching lists of
    photos."""

    def setUp(self):
        account = AccountFactory(api_key='1234', api_secret='9876')
        self.fetcher = PhotosFetcher(account=account)

    def test_inherits_from_fetcher(self):
        self.assertTrue( issubclass(PhotosFetcher, Fetcher) )

    def test_failure_with_no_child_call_api(self):
        """Requires a child class to set its own _call_api()."""
        with patch('time.sleep'):
            result = self.fetcher.fetch()
            self.assertFalse(result['success'])
            self.assertIn('messages', result)

    @responses.activate
    @patch.object(PhotosFetcher, '_fetch_photo_info')
    @patch.object(PhotosFetcher, '_fetch_photo_sizes')
    @patch.object(PhotosFetcher, '_fetch_photo_exif')
    def test_fetches_extra_photo_data(self, fetch_photo_exif, fetch_photo_sizes, fetch_photo_info):
        """For each photo in results, all the fetch_photo_* methods should be
        called."""
        self.add_response('people.getInfo')
        # Set results, as if we'd used a subclass's _call_api() method:
        self.fetcher.results = self.load_fixture(
                                        'people.getPhotos')['photos']['photo']
        self.fetcher._fetch_extra()
        # Each method is called once per photo_id:
        calls = [call('25822158530'), call('26069027966'), call('25822102530')]
        fetch_photo_info.assert_has_calls(calls)
        fetch_photo_sizes.assert_has_calls(calls)
        fetch_photo_exif.assert_has_calls(calls)

    @freeze_time("2015-08-14 12:00:00", tz_offset=-8)
    @responses.activate
    @patch.object(UserFetcher, '_fetch_and_save_avatar')
    @patch.object(UserSaver, 'save_user')
    def test_fetch_user_if_missing_fetches(self, save_user, fetch_avatar):
        """If the user isn't in fetched_users, it is fetched and saved."""

        save_user.return_value = UserFactory.create(nsid='35034346050@N01')

        self.add_response('people.getInfo')
        user_data = self.load_fixture('people.getInfo')['person']

        self.fetcher._fetch_user_if_missing('35034346050@N01')
        self.assertEqual(1, len(responses.calls))
        save_user.assert_called_once_with(user_data, datetime_now())
        self.assertEqual(1, len(self.fetcher.fetched_users))
        self.assertEqual(self.fetcher.fetched_users['35034346050@N01'].nsid,
                        '35034346050@N01')

    @responses.activate
    @patch.object(UserSaver, 'save_user')
    def test_fetch_user_if_missing_doesnt_fetch(self, save_user):
        """If the user is in fetched_users, it doesn't fetch the data again."""
        self.add_response('people.getInfo')
        user_data = self.load_fixture('people.getInfo')['person']
        self.fetcher.fetched_users = {'35034346050@N01': UserFactory()}
        self.fetcher._fetch_user_if_missing('35034346050@N01')
        self.assertEqual(0, len(responses.calls))
        self.assertFalse(save_user.called)

    @responses.activate
    def test_fetch_user_if_missing_raises_error(self):
        "If there was an error fetching the user's Info"
        self.add_response('people.getInfo',
                                    body=FlickrError('Something went wrong'))
        with self.assertRaises(FetchError):
            self.fetcher._fetch_user_if_missing('35034346050@N01')

    @responses.activate
    def test_fetches_photo_info(self):
        """Fetches info for a photo, and no user info if they're all in
        fetched_users"""
        self.add_response('photos.getInfo')
        photo_data = self.load_fixture('photos.getInfo')['photo']
        # Both users listed as authors of the tags in the fixture:
        self.fetcher.fetched_users = {'12345678901@N01': UserFactory(),
                                        '35034346050@N01': UserFactory(), }
        results = self.fetcher._fetch_photo_info('26069027966')
        self.assertEqual(1, len(responses.calls))
        self.assertEqual(results, photo_data)

    @responses.activate
    @patch.object(UserFetcher, '_fetch_and_save_avatar')
    def test_fetches_photo_info_and_tag_user(self, fetch_avatar):
        """Fetches info for a photo and any tag authors who aren't in
        fetched_users."""
        self.add_response('photos.getInfo')
        self.add_response('people.getInfo')
        photo_data = self.load_fixture('photos.getInfo')['photo']
        # One user listed as a tag author isn't in fetched_users:
        self.fetcher.fetched_users = { '12345678901@N01': UserFactory(), }
        results = self.fetcher._fetch_photo_info('26069027966')
        self.assertEqual(2, len(responses.calls))
        self.assertEqual(results, photo_data)

    @responses.activate
    def test_fetch_photo_info_throws_exception(self):
        """If there's a Flickr API error, it throws FetchError."""
        self.add_response('photos.getInfo',
            body='{"stat": "fail", "code": 1, "message": "Photo not found"}')

        with self.assertRaises(FetchError):
            self.fetcher._fetch_photo_info('26069027966')

    @responses.activate
    def test_fetches_photo_sizes(self):
        """Fetches sizes for a photo."""
        self.add_response('photos.getSizes')
        photo_data = self.load_fixture('photos.getSizes')['sizes']
        results = self.fetcher._fetch_photo_sizes('26069027966')
        self.assertEqual(1, len(responses.calls))
        self.assertEqual(results, photo_data)

    @responses.activate
    def test_fetch_photo_sizes_throws_exception(self):
        """If there's a Flickr API error, it throws FetchError."""
        self.add_response('photos.getSizes',
            body='{"stat": "fail", "code": 1, "message": "Photo not found"}')

        with self.assertRaises(FetchError):
            self.fetcher._fetch_photo_sizes('26069027966')

    @responses.activate
    def test_fetches_photo_exif(self):
        """Fetches EXIF for a photo."""
        self.add_response('photos.getExif')
        photo_data = self.load_fixture('photos.getExif')['photo']
        results = self.fetcher._fetch_photo_exif('26069027966')
        self.assertEqual(1, len(responses.calls))
        self.assertEqual(results, photo_data)

    @responses.activate
    def test_fetch_photo_exif_throws_exception(self):
        """If there's a Flickr API error, it throws FetchError."""
        self.add_response('photos.getExif',
            body='{"stat": "fail", "code": 1, "message": "Photo not found"}')

        with self.assertRaises(FetchError):
            self.fetcher._fetch_photo_exif('26069027966')


class RecentPhotosFetcherTestCase(FlickrFetchTestCase):

    def setUp(self):
        account = AccountFactory(api_key='1234', api_secret='9876',
                                    user=UserFactory(nsid='35034346050@N01') )
        self.fetcher = RecentPhotosFetcher(account=account)

    def test_inherits_from_fetcher(self):
        self.assertTrue( issubclass(RecentPhotosFetcher, PhotosFetcher) )

    def test_raises_error_with_invalid_days(self):
        "days should be an int or 'all'."
        with self.assertRaises(FetchError):
            self.fetcher.fetch(days='bibble')

    def test_raises_error_with_no_days(self):
        "days should be an int or 'all'."
        with self.assertRaises(FetchError):
            self.fetcher.fetch()

    @responses.activate
    def test_call_api_error(self):
        "_call_api() should throw an error if there's an API error."
        self.add_response('people.getPhotos',
            body='{"stat": "fail", "code": 2, "message": "Unknown user"}')

        with self.assertRaises(FetchError):
            self.fetcher._call_api()

    @responses.activate
    @patch.object(PhotosFetcher, '_fetch_extra')
    @patch.object(PhotoSaver, 'save_photo')
    def test_fetches_multiple_pages(self, save_photo, fetch_extra):
        """If the response from the API says there's more than 1 page of
        results _fetch_pages() should fetch them all."""
        # Alter our default response fixture to set the number of pages to 3:
        body = self.load_fixture('people.getPhotos')
        body['photos']['pages'] = 3
        body = json.dumps(body)

        # Responses after the first should be for the subsequent pages:
        self.add_response('people.getPhotos', body=body)
        self.add_response('people.getPhotos', body=body, querystring={'page': '2'})
        self.add_response('people.getPhotos', body=body, querystring={'page': '3'})

        with patch('time.sleep'):
            results = self.fetcher.fetch(days='all')

            self.assertEqual(len(responses.calls), 3)
            # Our fixture has 3 photos, so we should now have 9:
            self.assertEqual(results['fetched'], 9)

    @patch.object(PhotosFetcher, '_fetch_pages')
    def test_calls_fetch_pages(self, fetch_pages):
        """Check that it uses the _fetch_pages() method we tested above,
        rather than the singular _fetch_page()."""

        self.fetcher.fetch(days=3)
        fetch_pages.assert_called_once_with()

    @responses.activate
    @freeze_time("2015-08-14 12:00:00", tz_offset=-8)
    @patch.object(PhotoSaver, 'save_photo')
    @patch.object(PhotosFetcher, '_fetch_extra')
    def test_fetches_recent_days(self, save_photo, fetch_extra):
        """Should only ask for photos from recent days, if number of days is set."""
        # '1439294400' is 2015-08-11 12:00:00 (ie, 3 days ago)
        self.add_response('people.getPhotos',
                                querystring={'min_upload_date': '1439294400'})
        with patch('time.sleep'):
            self.fetcher.fetch(days=3)
            self.assertEqual(len(responses.calls), 1)

    @responses.activate
    @freeze_time("2015-08-14 12:00:00", tz_offset=-8)
    @patch.object(PhotoSaver, 'save_photo')
    @patch.object(PhotosFetcher, '_fetch_photo_info')
    @patch.object(PhotosFetcher, '_fetch_photo_sizes')
    @patch.object(PhotosFetcher, '_fetch_photo_exif')
    def test_saves_photos(self, fetch_photo_info, fetch_photo_sizes, fetch_photo_exif, save_photo):
        """It should call save_photos() for each photo it fetches."""
        self.add_response('people.getPhotos')
        self.add_response('people.getInfo')
        with patch('time.sleep'):
            results = self.fetcher.fetch(days='all')
            self.assertEqual(save_photo.call_count, 3)
            self.assertTrue(results['success'])
            self.assertEqual(results['fetched'], 3)


class PhotosetsFetcherTestCase(FlickrFetchTestCase):

    def setUp(self):
        account = AccountFactory(api_key='1234', api_secret='9876',
                                    user=UserFactory(nsid='35034346050@N01'))
        self.fetcher = PhotosetsFetcher(account=account)

    def test_inherits_from_fetcher(self):
        self.assertTrue( issubclass(PhotosetsFetcher, Fetcher) )

    @responses.activate
    def test_call_api_error(self):
        "_call_api() should throw an error if there's an API error."
        self.add_response('photosets.getList',
            body='{"stat": "fail", "code": 1, "message": "User not found"}')

        with self.assertRaises(FetchError):
            self.fetcher._call_api()

    @responses.activate
    def test_fetches_multiple_pages(self):
        """If the response from the API says there's more than 1 page of
        results _fetch_pages() should fetch them all."""
        # Alter our default response fixture to set the number of pages to 3:
        body = self.load_fixture('photosets.getList')
        body['photosets']['pages'] = 3
        body = json.dumps(body)

        # Responses after the first should be for the subsequent pages:
        self.add_response('photosets.getList', body=body)
        self.add_response(
                    'photosets.getList', body=body, querystring={'page': '2'})
        self.add_response(
                    'photosets.getList', body=body, querystring={'page': '3'})

        # We need to mock all the calls to fetch the photosets' photos too:
        body_2 = json.dumps(self.load_fixture('photosets.getPhotos'))
        self.add_response('photosets.getPhotos', body=body_2,
                            querystring={'photoset_id':'72157665648859705'})
        self.add_response('photosets.getPhotos', body=body_2,
                            querystring={'photoset_id':'72157662491524213'})
        self.add_response('photosets.getPhotos', body=body_2,
                            querystring={'photoset_id':'72157645155015916'})

        with patch('time.sleep'):
            results = self.fetcher.fetch()

            # 3 Photosets x 3 pages each, plus one getPhotos per photoset:
            self.assertEqual(len(responses.calls), 12)
            # Our fixture has 3 photosets, and we get 3 pages for each
            # photoset, so we should now have 9:
            self.assertEqual(results['fetched'], 9)

    @patch.object(PhotosetsFetcher, '_fetch_pages')
    @patch.object(PhotosetsFetcher, '_fetch_extra')
    def test_calls_fetch_pages(self, fetch_extra, fetch_pages):
        """Check that it uses the _fetch_pages() method we tested above,
        rather than the singular _fetch_page()."""

        self.fetcher.fetch()
        fetch_pages.assert_called_once_with()

    @responses.activate
    @patch.object(PhotosetSaver, 'save_photoset')
    def test_fetches_photos(self, save_photoset):
        """Should fetch the list of photos in each photoset."""
        self.add_response('photosets.getList',
                    body=json.dumps( self.load_fixture('photosets.getList') ))

        body = json.dumps(self.load_fixture('photosets.getPhotos'))
        # Should be called for each of the photosets in the getList fixture.
        self.add_response('photosets.getPhotos', body=body,
                            querystring={'photoset_id':'72157665648859705'})
        self.add_response('photosets.getPhotos', body=body,
                            querystring={'photoset_id':'72157662491524213'})
        self.add_response('photosets.getPhotos', body=body,
                            querystring={'photoset_id':'72157645155015916'})

        with patch('time.sleep'):
            self.fetcher.fetch()
            self.assertEqual(len(responses.calls), 4)

    @responses.activate
    @freeze_time("2015-08-14 12:00:00", tz_offset=-8)
    @patch.object(PhotosetSaver, 'save_photoset')
    @patch.object(PhotosetsFetcher, '_fetch_photos_in_photoset')
    def test_saves_photosets(self, fetch_photos, save_photoset):
        """It should call save_photoset() for each photoset it fetches."""
        self.add_response('photosets.getList')
        with patch('time.sleep'):
            results = self.fetcher.fetch()
            self.assertEqual(save_photoset.call_count, 3)
            self.assertTrue(results['success'])
            self.assertEqual(results['fetched'], 3)

    @responses.activate
    def test_raises_error_if_fails_getting_photos(self):
        self.add_response('photosets.getPhotos',
                                    body=FlickrError('Something went wrong'))
        with self.assertRaises(FetchError):
            self.fetcher._fetch_photos_in_photoset(72157665648859705)


