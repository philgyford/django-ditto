import calendar
import datetime
import json
import os
import pytz
import tempfile
from unittest.mock import call, patch

import responses
from requests.exceptions import HTTPError
from freezegun import freeze_time
from django.test import override_settings, TestCase

from ditto.core.utils import datetime_now
from ditto.flickr.factories import AccountFactory, PhotoFactory, UserFactory
from ditto.flickr.fetch import FetchError, Fetcher, MultiAccountFetcher,\
        UserFetcher, UserIdFetcher, OriginalFilesFetcher,\
        PhotosFetcher, RecentPhotosFetcher, PhotosetsFetcher,\
        RecentPhotosMultiAccountFetcher, PhotosetsMultiAccountFetcher
from .test_fetch import FlickrFetchTestCase


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

    @patch('ditto.flickr.fetch.Fetcher._call_api')
    @patch('ditto.flickr.fetch.Fetcher._save_results')
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

    @patch('ditto.flickr.fetch.Fetcher._call_api')
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
    def test_makes_one_api_calls(self):
        "Should call people.getInfo"
        self.add_response('people.getInfo')
        result = UserFetcher(account=self.account).fetch(
                                                        nsid='35034346050@N01')
        self.assertEqual(len(responses.calls), 1)

    @responses.activate
    @patch('ditto.flickr.fetch.UserSaver.save_user')
    @freeze_time("2015-08-14 12:00:00", tz_offset=-8)
    def test_calls_save_user_correctly(self, save_user):
        "The correct data should be sent to UserSaver.save_user()"
        self.add_response('people.getInfo')
        result = UserFetcher(account=self.account).fetch(
                                                        nsid='35034346050@N01')

        user_response = self.load_fixture('people.getInfo')

        save_user.assert_called_once_with(
                                    user_response['person'], datetime_now())

    @responses.activate
    def test_returns_correct_success_result(self):
        self.add_response('people.getInfo')
        result = UserFetcher(account=self.account).fetch(
                                                        nsid='35034346050@N01')

        self.assertIn('success', result)
        self.assertTrue(result['success'])
        self.assertIn('fetched', result)
        self.assertEqual(result['fetched'], 1)


class FilesFetcherTestCase(TestCase):

    def setUp(self):
        user = UserFactory()
        account = AccountFactory(user=user)
        self.fetcher = OriginalFilesFetcher(account=account)

        self.photo_1 = PhotoFactory(original_file='p1.jpg', user=user)
        # Needs a post_time for testing file save path:
        self.photo_2 = PhotoFactory(original_file=None, user=user,
                post_time=datetime.datetime.strptime('2015-08-14', '%Y-%m-%d').replace(tzinfo=pytz.utc))
        self.video_1 = PhotoFactory(media='video', original_file='v1.jpg',
                                video_original_file='v1.mov', user=user)
        self.video_2 = PhotoFactory(media='video', original_file=None,
                                video_original_file=None, user=user,
                                flickr_id='1234567890', original_secret='7777')
        # And one by someone else:
        self.photo_3 = PhotoFactory(original_file=None, user=UserFactory())

    def test_fails_with_no_account(self):
        with self.assertRaises(TypeError):
            fetcher = OriginalFilesFetcher()

    def test_fails_with_no_flickr_user(self):
        fetcher = OriginalFilesFetcher(account=AccountFactory(user=None))
        results = fetcher.fetch()
        self.assertFalse(results['success'])
        self.assertIn(
                    'This account has no Flickr User', results['messages'][0])

    # This all feels too much like I'm testing internal behaviour, but not
    # sure what else to do...

    @patch.object(OriginalFilesFetcher, '_fetch_and_save_file')
    def test_calls_fetch_and_save_missing(self, fetch_and_save_file):
        "Goes to fetch for photos without files already."
        results = self.fetcher.fetch()
        calls = [
                    call(photo=self.video_2, media_type='photo'),
                    call(photo=self.video_2, media_type='video'),
                    call(photo=self.photo_2, media_type='photo'),
                ]
        fetch_and_save_file.assert_has_calls(calls)

    @patch.object(OriginalFilesFetcher, '_fetch_and_save_file')
    def test_calls_fetch_and_save_all(self, fetch_and_save_file):
        "Goes to fetch for ALL photos."
        results = self.fetcher.fetch(fetch_all=True)
        calls = [
                    call(photo=self.photo_1, media_type='photo'),
                    call(photo=self.video_1, media_type='photo'),
                    call(photo=self.video_1, media_type='video'),
                    call(photo=self.video_2, media_type='photo'),
                    call(photo=self.video_2, media_type='video'),
                    call(photo=self.photo_2, media_type='photo'),
                ]
        fetch_and_save_file.assert_has_calls(calls)

    @patch.object(OriginalFilesFetcher, '_fetch_and_save_file')
    def test_results_for_fetch_missing(self, fetch_and_save_file):
        "Results values should be OK when fetching only missing photos/videos."
        results = self.fetcher.fetch()
        self.assertTrue(results['success'])
        self.assertEqual(results['fetched'], 3)

    @patch.object(OriginalFilesFetcher, '_fetch_and_save_file')
    def test_results_for_fetch_all(self, fetch_and_save_file):
        "Results values should be OK when fetching ALL photos/videos."
        results = self.fetcher.fetch(fetch_all=True)
        self.assertTrue(results['success'])
        self.assertEqual(results['fetched'], 6)

    @patch.object(OriginalFilesFetcher, '_fetch_and_save_file')
    def test_error_results(self, fetch_and_save_file):
        "Sets the correct error values if things go wrong."
        fetch_and_save_file.side_effect = FetchError('Oh dear')
        results = self.fetcher.fetch()
        self.assertFalse(results['success'])
        self.assertEqual(results['fetched'], 0)
        self.assertEqual(len(results['messages']), 3)
        self.assertEqual(results['messages'][0], 'Oh dear')

    @patch.object(OriginalFilesFetcher, '_download_file')
    def test_downloads_photo(self, download_file):
        "Calls the download method correctly for photos."
        download_file.return_value = False
        self.fetcher._fetch_and_save_file(self.photo_2, 'photo')
        download_file.assert_has_calls( [ call(
                    self.photo_2.original_url,
                    ['image/jpeg', 'image/jpg', 'image/png', 'image/gif',],
                    self.photo_2
                ) ] )

    @patch.object(OriginalFilesFetcher, '_download_file')
    def test_downloads_video(self, download_file):
        "Calls the download method correctly for videos."
        download_file.return_value = False
        self.fetcher._fetch_and_save_file(self.video_2, 'video')
        download_file.assert_has_calls( [ call(
                    self.video_2.video_original_url,
                    ['video/mp4',],
                    self.video_2
                ) ] )

    @override_settings(MEDIA_ROOT=tempfile.gettempdir())
    @patch.object(OriginalFilesFetcher, '_download_file')
    def test_saves_downloaded_file(self, download_file):
        # Make a temporary file, like _download_file() would make:
        jpg = tempfile.NamedTemporaryFile()
        temp_filepath = jpg.name
        download_file.return_value = temp_filepath

        self.fetcher._fetch_and_save_file(self.photo_2, 'photo')
        self.assertEqual(
            self.photo_2.original_file.name,
            'flickr/%s/2015/08/14/%s' % (
                self.photo_2.user.nsid,
                os.path.basename(temp_filepath)
            )
        )

    def test_make_filename_photo(self):
        "Should use the original photo's filename."
        filename = self.fetcher._make_filename(
            'https://c2.staticflickr.com/8/7019/27006033235_caa438b3b8_o.jpg',
            {},
            self.photo_2
        )
        self.assertEqual(filename, '27006033235_caa438b3b8_o.jpg')

    def test_make_filename_video(self):
        "Should use the Content-Disposition filename."
        filename = self.fetcher._make_filename(
            'https://www.flickr.com/photos/philgyford/26348530105/play/orig/2b5f3e0919/',
            {'Content-Disposition': 'attachment; filename=26348530105.mov'},
            self.video_2
        )
        self.assertEqual(filename, '26348530105.mov')

    def test_make_filename_fallback(self):
        "It should make a filename based on Photo's id and secret"
        filename = self.fetcher._make_filename(
            'https://www.flickr.com/photos/philgyford/26348530105/play/orig/2b5f3e0919/',
            {},
            self.video_2
        )
        self.assertEqual(filename, '1234567890_7777_o')


class FilesFetcherDownloadTestCase(TestCase):
    "Testing the file downloading part of the FilesFetcher."

    def setUp(self):
        user = UserFactory()
        account = AccountFactory(user=user)
        self.fetcher = OriginalFilesFetcher(account=account)
        self.photo = PhotoFactory(original_file=None, user=user)

    def do_download(self, status=200, content_type='image/jpg'):
        "Mocks requests and calls _download_file()"
        # Open the image we're going to pretend we're fetching from the URL:
        with open('tests/flickr/fixtures/images/marmite.jpg', 'rb') as img1:

            responses.add(responses.GET, self.photo.original_url,
                            body=img1.read(),
                            status=status,
                            content_type=content_type,
                            adding_headers={'Transfer-Encoding': 'chunked'})

            return self.fetcher._download_file(
                        self.photo.original_url, ['image/jpg'], self.photo )

    @responses.activate
    @patch.object(OriginalFilesFetcher, '_make_filename')
    def test_downloads_file(self, make_filename):
        "Streams a jpg, saves it to /tmp/, returns the path, calls _make_filename()."
        make_filename.return_value = 'marmite.jpg'

        filepath = self.do_download()

        self.assertTrue(os.path.isfile(filepath))
        self.assertEqual(len(responses.calls), 1)
        self.assertEqual(filepath, '/tmp/marmite.jpg')
        make_filename.assert_called_once_with(
                self.photo.original_url, {'Content-Type': 'image/jpg', 'Transfer-Encoding': 'chunked'}, self.photo)

    @responses.activate
    def test_raises_error_on_get_failure(self):
        "If the requests.get() call raises an error."
        responses.add(responses.GET, self.photo.original_url,
                        body=HTTPError('Something went wrong'))
        with self.assertRaises(FetchError):
            filepath = self.fetcher._download_file(
                        self.photo.original_url, ['image/jpg'], self.photo )

    @responses.activate
    def test_raises_error_on_bad_status_code(self):
        with self.assertRaises(FetchError):
            filepath = self.do_download(status=500)

    @responses.activate
    def test_raises_error_with_invalid_content_type(self):
        "If downloaded file has content type different to what we ask for."
        with self.assertRaises(FetchError):
            filepath = self.do_download(content_type='text/html')


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
    @patch('ditto.flickr.fetch.PhotosFetcher._fetch_photo_info')
    @patch('ditto.flickr.fetch.PhotosFetcher._fetch_photo_sizes')
    @patch('ditto.flickr.fetch.PhotosFetcher._fetch_photo_exif')
    def test_fetches_extra_photo_data(self, fetch_photo_exif, fetch_photo_sizes, fetch_photo_info):
        """For each photo in results, all the fetch_photo_* methods should be
        called."""
        self.add_response('people.getInfo')
        # Set results, as if we'd used a subclasse's _call_api() method:
        self.fetcher.results = self.load_fixture('people.getPhotos')['photos']['photo']
        self.fetcher._fetch_extra()
        # Each method is called once per photo_id:
        calls = [call('25822158530'), call('26069027966'), call('25822102530')]
        fetch_photo_info.assert_has_calls(calls)
        fetch_photo_sizes.assert_has_calls(calls)
        fetch_photo_exif.assert_has_calls(calls)

    @freeze_time("2015-08-14 12:00:00", tz_offset=-8)
    @responses.activate
    @patch('ditto.flickr.fetch.UserSaver.save_user')
    def test_fetch_user_if_missing_fetches(self, save_user):
        """If the user isn't in fetched_users, it is fetched and saved."""
        self.add_response('people.getInfo')
        user_data = self.load_fixture('people.getInfo')['person']
        self.fetcher._fetch_user_if_missing('35034346050@N01')
        self.assertEqual(1, len(responses.calls))
        save_user.assert_called_once_with(user_data, datetime_now())

    @responses.activate
    @patch('ditto.flickr.fetch.UserSaver.save_user')
    def test_fetch_user_if_missing_doesnt_fetch(self, save_user):
        """If the user is in fetched_users, it doesn't fetch the data again."""
        self.add_response('people.getInfo')
        user_data = self.load_fixture('people.getInfo')['person']
        self.fetcher.fetched_users = {'35034346050@N01': UserFactory()}
        self.fetcher._fetch_user_if_missing('35034346050@N01')
        self.assertEqual(0, len(responses.calls))
        self.assertFalse(save_user.called)

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
    def test_fetches_photo_info_and_tag_user(self):
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
    def test_fetches_multiple_pages(self):
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
            self.fetcher._fetch_pages()

            self.assertEqual(len(responses.calls), 3)
            # Our fixture has 3 photos, so we should now have 9:
            self.assertEqual(len(self.fetcher.results), 9)

    @patch('ditto.flickr.fetch.PhotosFetcher._fetch_pages')
    def test_calls_fetch_pages(self, fetch_pages):
        """Check that it uses the _fetch_pages() method we tested above,
        rather than the singular _fetch_page()."""

        self.fetcher.fetch(days=3)
        fetch_pages.assert_called_once_with()

    @responses.activate
    @freeze_time("2015-08-14 12:00:00", tz_offset=-8)
    @patch('ditto.flickr.fetch.PhotoSaver.save_photo')
    @patch('ditto.flickr.fetch.PhotosFetcher._fetch_extra')
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
    @patch('ditto.flickr.fetch.PhotoSaver.save_photo')
    @patch('ditto.flickr.fetch.PhotosFetcher._fetch_photo_info')
    @patch('ditto.flickr.fetch.PhotosFetcher._fetch_photo_sizes')
    @patch('ditto.flickr.fetch.PhotosFetcher._fetch_photo_exif')
    def test_saves_photos(self, fetch_photo_info, fetch_photo_sizes, fetch_photo_exif, save_photo):
        """It should call save_photos() for each photo it fetches."""
        self.add_response('people.getPhotos')
        self.add_response('people.getInfo')
        with patch('time.sleep'):
            results = self.fetcher.fetch(days='all')
            self.assertEqual(save_photo.call_count, 3)
            self.assertTrue(results['success'])
            self.assertEqual(results['fetched'], 3)


class MultiAccountFetcherTestCase(FlickrFetchTestCase):

    def setUp(self):
        self.account_1 = AccountFactory(api_key='1234', api_secret='9876',
                                    user=UserFactory(nsid='35034346050@N01') )
        self.inactive_account = AccountFactory(
                            api_key='2345', api_secret='8765', is_active=False,
                            user=UserFactory(nsid='12345678901@N01') )
        self.account_2 = AccountFactory(api_key='3456', api_secret='7654',
                                    user=UserFactory(nsid='98765432101@N01') )

    def test_fetch_throws_exception(self):
        "Throws an except if its own fetch() method is called."
        with self.assertRaises(FetchError):
            MultiAccountFetcher().fetch()

    def test_uses_all_accounts_by_default(self):
        fetcher = MultiAccountFetcher()
        self.assertEqual(len(fetcher.accounts), 2)

    def test_throws_exception_with_no_active_accounts(self):
        self.account_1.is_active = False
        self.account_2.is_active = False
        self.account_1.save()
        self.account_2.save()
        with self.assertRaises(FetchError):
            MultiAccountFetcher()

    def test_throws_exception_with_invalid_nsid(self):
        with self.assertRaises(FetchError):
            MultiAccountFetcher(nsid='nope')

    def test_throws_exception_with_no_account(self):
        "If the NSID is not attached to an Account."
        user = UserFactory(nsid='99999999999@N01')
        with self.assertRaises(FetchError):
            MultiAccountFetcher(nsid='99999999999@N01')

    def test_throws_exception_with_inactive_account(self):
        with self.assertRaises(FetchError):
            MultiAccountFetcher(nsid='12345678901@N01')

    def test_works_with_valid_nsid(self):
        fetcher = MultiAccountFetcher(nsid='35034346050@N01')
        self.assertEqual(len(fetcher.accounts), 1)
        self.assertEqual(fetcher.accounts[0], self.account_1)


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
    @patch('ditto.flickr.fetch.PhotosetsFetcher._fetch_extra')
    def test_fetches_multiple_pages(self, fetch_extra):
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

        with patch('time.sleep'):
            self.fetcher._fetch_pages()

            self.assertEqual(len(responses.calls), 3)
            # Our fixture has 3 photosets, so we should now have 9:
            self.assertEqual(len(self.fetcher.results), 9)

    @patch('ditto.flickr.fetch.PhotosetsFetcher._fetch_pages')
    @patch('ditto.flickr.fetch.PhotosetsFetcher._fetch_extra')
    def test_calls_fetch_pages(self, fetch_extra, fetch_pages):
        """Check that it uses the _fetch_pages() method we tested above,
        rather than the singular _fetch_page()."""

        self.fetcher.fetch()
        fetch_pages.assert_called_once_with()

    @responses.activate
    @patch('ditto.flickr.fetch.PhotosetSaver.save_photoset')
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
    @patch('ditto.flickr.fetch.PhotosetSaver.save_photoset')
    @patch('ditto.flickr.fetch.PhotosetsFetcher._fetch_photos_in_photoset')
    def test_saves_photosets(self, fetch_photos, save_photoset):
        """It should call save_photoset() for each photoset it fetches."""
        self.add_response('photosets.getList')
        with patch('time.sleep'):
            results = self.fetcher.fetch()
            self.assertEqual(save_photoset.call_count, 3)
            self.assertTrue(results['success'])
            self.assertEqual(results['fetched'], 3)


class MultiAccountFetcherTestCase(FlickrFetchTestCase):

    def setUp(self):
        self.account_1 = AccountFactory(api_key='1234', api_secret='9876',
                                    user=UserFactory(nsid='35034346050@N01') )
        self.inactive_account = AccountFactory(
                            api_key='2345', api_secret='8765', is_active=False,
                            user=UserFactory(nsid='12345678901@N01') )
        self.account_2 = AccountFactory(api_key='3456', api_secret='7654',
                                    user=UserFactory(nsid='98765432101@N01') )

    def test_inherits_from_multi_account_fetcher(self):
        self.assertTrue(
            issubclass(RecentPhotosMultiAccountFetcher, MultiAccountFetcher)
        )


class RecentPhotosMultiAccountFetcherTestCase(MultiAccountFetcherTestCase):

    @patch('ditto.flickr.fetch.RecentPhotosFetcher.__init__')
    @patch('ditto.flickr.fetch.RecentPhotosFetcher.fetch')
    def test_inits_fetcher_with_active_accounts(self, fetch, init):
        "RecentPhotosFetcher should be called with 2 active accounts."
        init.return_value = None
        RecentPhotosMultiAccountFetcher().fetch()
        init.assert_has_calls([call(self.account_1), call(self.account_2)])

    @patch('ditto.flickr.fetch.RecentPhotosFetcher.fetch')
    def test_calls_fetch_for_active_accounts(self, fetch):
        "RecentPhotosFetcher.fetch() should be called twice."
        RecentPhotosMultiAccountFetcher().fetch(days=3)
        fetch.assert_has_calls([call(days=3), call(days=3)])

    @patch('ditto.flickr.fetch.RecentPhotosFetcher.fetch')
    def test_returns_list_of_return_values(self, fetch):
        "Should return a list of the dicts that RecentPhotosFetcher.fetch() returns"
        ret = {'success': True, 'account': 'bob', 'fetched': 7}
        fetch.side_effect = [ret, ret]

        return_value = RecentPhotosMultiAccountFetcher().fetch(days=3)

        self.assertEqual(len(return_value), 2)
        self.assertEqual(return_value[0]['account'], 'bob')


class PhotosetsMultiAccountFetcherTestCase(MultiAccountFetcherTestCase):

    @patch('ditto.flickr.fetch.PhotosetsFetcher.__init__')
    @patch('ditto.flickr.fetch.PhotosetsFetcher.fetch')
    def test_inits_fetcher_with_active_accounts(self, fetch, init):
        "PhotosetsFetcher should be called with 2 active accounts."
        init.return_value = None
        PhotosetsMultiAccountFetcher().fetch()
        init.assert_has_calls([call(self.account_1), call(self.account_2)])

    @patch('ditto.flickr.fetch.PhotosetsFetcher.fetch')
    def test_calls_fetch_for_active_accounts(self, fetch):
        "PhotosetsFetcher.fetch() should be called twice."
        PhotosetsMultiAccountFetcher().fetch()
        fetch.assert_has_calls([call(), call()])

    @patch('ditto.flickr.fetch.PhotosetsFetcher.fetch')
    def test_returns_list_of_return_values(self, fetch):
        "Should return a list of the dicts that PhotosetsFetcher.fetch() returns"
        ret = {'success': True, 'account': 'bob', 'fetched': 7}
        fetch.side_effect = [ret, ret]

        return_value = PhotosetsMultiAccountFetcher().fetch()

        self.assertEqual(len(return_value), 2)
        self.assertEqual(return_value[0]['account'], 'bob')

