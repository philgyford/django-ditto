from unittest.mock import call, patch

from .test_fetch import FlickrFetchTestCase
from ditto.flickr.fetch import FetchError
from ditto.flickr.fetch.fetchers import PhotosetsFetcher, RecentPhotosFetcher
from ditto.flickr.fetch.filesfetchers import OriginalFilesFetcher
from ditto.flickr.fetch.multifetchers import MultiAccountFetcher,\
    OriginalFilesMultiAccountFetcher, PhotosetsMultiAccountFetcher,\
    RecentPhotosMultiAccountFetcher
from ditto.flickr.factories import AccountFactory, UserFactory


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

    def test_fetch_throws_exception(self):
        "Throws an exception if its own fetch() method is called."
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


class RecentPhotosMultiAccountFetcherTestCase(MultiAccountFetcherTestCase):

    @patch.object(RecentPhotosFetcher, '__init__')
    @patch.object(RecentPhotosFetcher, 'fetch')
    def test_inits_fetcher_with_active_accounts(self, fetch, init):
        "RecentPhotosFetcher should be called with 2 active accounts."
        init.return_value = None
        RecentPhotosMultiAccountFetcher().fetch()
        init.assert_has_calls([call(self.account_1), call(self.account_2)])

    @patch.object(RecentPhotosFetcher, 'fetch')
    def test_calls_fetch_for_active_accounts(self, fetch):
        "RecentPhotosFetcher.fetch() should be called twice."
        RecentPhotosMultiAccountFetcher().fetch(days=3)
        fetch.assert_has_calls([call(days=3), call(days=3)])

    @patch.object(RecentPhotosFetcher, 'fetch')
    def test_returns_list_of_return_values(self, fetch):
        "Should return a list of the dicts that RecentPhotosFetcher.fetch() returns"
        ret = {'success': True, 'account': 'bob', 'fetched': 7}
        fetch.side_effect = [ret, ret]

        return_value = RecentPhotosMultiAccountFetcher().fetch(days=3)

        self.assertEqual(len(return_value), 2)
        self.assertEqual(return_value[0]['account'], 'bob')


class PhotosetsMultiAccountFetcherTestCase(MultiAccountFetcherTestCase):

    @patch.object(PhotosetsFetcher, '__init__')
    @patch.object(PhotosetsFetcher, 'fetch')
    def test_inits_fetcher_with_active_accounts(self, fetch, init):
        "PhotosetsFetcher should be called with 2 active accounts."
        init.return_value = None
        PhotosetsMultiAccountFetcher().fetch()
        init.assert_has_calls([call(self.account_1), call(self.account_2)])

    @patch.object(PhotosetsFetcher, 'fetch')
    def test_calls_fetch_for_active_accounts(self, fetch):
        "PhotosetsFetcher.fetch() should be called twice."
        PhotosetsMultiAccountFetcher().fetch()
        fetch.assert_has_calls([call(), call()])

    @patch.object(PhotosetsFetcher, 'fetch')
    def test_returns_list_of_return_values(self, fetch):
        "Should return a list of the dicts that PhotosetsFetcher.fetch() returns"
        ret = {'success': True, 'account': 'bob', 'fetched': 7}
        fetch.side_effect = [ret, ret]

        return_value = PhotosetsMultiAccountFetcher().fetch()

        self.assertEqual(len(return_value), 2)
        self.assertEqual(return_value[0]['account'], 'bob')


class OriginalFilesMultiAccountFetcherTestCase(MultiAccountFetcherTestCase):

    @patch.object(OriginalFilesFetcher, '__init__')
    @patch.object(OriginalFilesFetcher, 'fetch')
    def test_inits_fetcher_with_active_accounts(self, fetch, init):
        "OriginalFilesFetcher should be called with 2 active accounts."
        init.return_value = None
        OriginalFilesMultiAccountFetcher().fetch()
        init.assert_has_calls([call(self.account_1), call(self.account_2)])

    @patch.object(OriginalFilesFetcher, 'fetch')
    def test_calls_fetch_for_active_accounts(self, fetch):
        "OriginalFilesFetcher.fetch() should be called twice."
        OriginalFilesMultiAccountFetcher().fetch()
        fetch.assert_has_calls([call(fetch_all=False), call(fetch_all=False)])

    @patch.object(OriginalFilesFetcher, 'fetch')
    def test_calls_fetch_with_fetch_all_param(self, fetch):
        "fetch() should pass on the fetch_all param"
        OriginalFilesMultiAccountFetcher().fetch(fetch_all=True)
        fetch.assert_has_calls([call(fetch_all=True), call(fetch_all=True)])

    @patch.object(OriginalFilesFetcher, 'fetch')
    def test_returns_list_of_return_values(self, fetch):
        "Should return a list of the dicts that OriginalFilesFetcher.fetch() returns"
        ret = {'success': True, 'account': 'bob', 'fetched': 7}
        fetch.side_effect = [ret, ret]

        return_value = OriginalFilesMultiAccountFetcher().fetch()

        self.assertEqual(len(return_value), 2)
        self.assertEqual(return_value[0]['account'], 'bob')

