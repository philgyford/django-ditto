import datetime
import os
import pytz
import tempfile
from unittest.mock import call, patch

from django.test import override_settings, TestCase

from ditto.core.utils.downloader import DownloadException, filedownloader
from ditto.flickr.factories import AccountFactory, PhotoFactory, UserFactory
from ditto.flickr.fetch import FetchError
from ditto.flickr.fetch.filesfetchers import OriginalFilesFetcher


class FilesFetcherTestCase(TestCase):

    def setUp(self):
        user = UserFactory()
        account = AccountFactory(user=user)
        self.fetcher = OriginalFilesFetcher(account=account)

        self.photo_1 = PhotoFactory(title='p1',
                                            original_file='p1.jpg', user=user)

        the_time = datetime.datetime.strptime('2015-08-14', '%Y-%m-%d').replace(tzinfo=pytz.utc)

        # Needs a taken_time for testing file save path:
        # post_time will put them in order.
        self.photo_2 = PhotoFactory(title='p2',
                                    original_file=None,
                                    user=user,
                                    post_time=the_time,
                                    taken_time=the_time)
        self.video_1 = PhotoFactory(title='v1',
                                media='video', original_file='v1.jpg',
                                video_original_file='v1.mov', user=user)
        self.video_2 = PhotoFactory(title='v2',
                                media='video', original_file=None,
                                video_original_file=None, user=user,
                                flickr_id='1234567890', original_secret='7777',
                                post_time=the_time,
                                taken_time=the_time)
        # And one by someone else:
        self.photo_3 = PhotoFactory(title='p3',
                                        original_file=None, user=UserFactory())

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
                    call(photo=self.photo_2, media_type='photo'),
                    call(photo=self.video_2, media_type='photo'),
                    call(photo=self.video_2, media_type='video'),
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
                    call(photo=self.photo_2, media_type='photo'),
                    call(photo=self.video_2, media_type='photo'),
                    call(photo=self.video_2, media_type='video'),
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

    @patch.object(filedownloader, 'download')
    def test_downloads_photo(self, download):
        "Calls the download method correctly for photos."
        download.return_value = False
        self.fetcher._fetch_and_save_file(self.photo_2, 'photo')
        download.assert_has_calls( [ call(
                    self.photo_2.remote_original_url,
                    ['image/jpeg', 'image/jpg', 'image/png', 'image/gif',]
                ) ] )

    @patch.object(filedownloader, 'download')
    def test_downloads_video(self, download):
        "Calls the download method correctly for videos."
        download.return_value = False
        self.fetcher._fetch_and_save_file(self.video_2, 'video')
        download.assert_has_calls( [ call(
                    self.video_2.video_original_url,
                    ['video/mp4',]
                ) ] )

    @patch.object(filedownloader, 'download')
    def test_raises_error_if_download_fails(self, download):
        "If download() raises an error, so does _fetch_and_save_file()"
        download.side_effect = DownloadException("Ooops")
        with self.assertRaises(FetchError):
            self.fetcher._fetch_and_save_file(self.photo_2, 'photo')

    @override_settings(MEDIA_ROOT=tempfile.gettempdir())
    @patch.object(filedownloader, 'download')
    def test_saves_downloaded_photo_file(self, download):
        # Make a temporary file, like download() would make:
        jpg = tempfile.NamedTemporaryFile()
        temp_filepath = jpg.name
        download.return_value = temp_filepath

        self.fetcher._fetch_and_save_file(self.photo_2, 'photo')
        nsid = self.photo_2.user.nsid
        nsid = nsid[ :nsid.index('@') ]
        self.assertEqual(
            self.photo_2.original_file.name,
            'flickr/%s/%s/%s/photos/2015/08/14/%s' % (
                nsid[-4:-2],
                nsid[-2:],
                self.photo_2.user.nsid.replace('@',''),
                os.path.basename(temp_filepath)
            )
        )

    @override_settings(MEDIA_ROOT=tempfile.gettempdir())
    @patch.object(filedownloader, 'download')
    def test_saves_downloaded_video_file(self, download):
        # Make a temporary file, like download() would make:
        video = tempfile.NamedTemporaryFile()
        temp_filepath = video.name
        download.return_value = temp_filepath

        self.fetcher._fetch_and_save_file(self.video_2, 'video')
        nsid = self.video_2.user.nsid
        nsid = nsid[ :nsid.index('@') ]
        self.assertEqual(
            self.video_2.video_original_file.name,
            'flickr/%s/%s/%s/photos/2015/08/14/%s' % (
                nsid[-4:-2],
                nsid[-2:],
                self.video_2.user.nsid.replace('@',''),
                os.path.basename(temp_filepath)
            )
        )
