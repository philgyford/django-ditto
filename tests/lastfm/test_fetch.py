import datetime
import json
import pytz
from unittest.mock import call, patch

import responses
from django.test import TestCase
from freezegun import freeze_time

from ditto.core.utils import datetime_now
from ditto.lastfm.factories import AccountFactory, AlbumFactory,\
    ArtistFactory, ScrobbleFactory, TrackFactory
from ditto.lastfm.fetch import FetchError, ScrobblesFetcher,\
    ScrobblesMultiAccountFetcher
from ditto.lastfm.models import Album, Artist, Scrobble, Track


class ScrobblesFetcherTestCase(TestCase):
    """
    Tests that don't involve sending any actual requests to the API.
    """

    def setUp(self):
        self.fetcher = ScrobblesFetcher(account=AccountFactory(
                                        username='bob', realname='Bob Ferris'))

        # Patch the _send_request() method:
        self.send_request_patch = patch.object(
                                            ScrobblesFetcher, '_send_request')
        self.send_request = self.send_request_patch.start()
        self.send_request.return_value = []
        self.sleep_patch = patch('time.sleep')
        self.sleep = self.sleep_patch.start()

    def tearDown(self):
        self.send_request_patch.stop()
        self.sleep_patch.stop()

    def test_requires_account_argument(self):
        "__init__ should throw error with no account argument."
        with self.assertRaises(TypeError):
            result = ScrobblesFetcher()

    def test_requires_valid_account_object(self):
        "__init__ should throw error with no Account object."
        with self.assertRaises(ValueError):
            result = ScrobblesFetcher(account=None)

    def test_no_credentials(self):
        "__init__ should return error if Account has no API creds."
        account = AccountFactory(api_key='')
        result = ScrobblesFetcher(account=account).fetch()
        self.assertFalse(result['success'])
        self.assertEqual(result['messages'],
                        ['Account has no API credentials'])

    def test_will_not_fetch_inactive_accounts(self):
        account = AccountFactory(is_active=False, username='terry')
        result = ScrobblesFetcher(account=account).fetch()
        self.assertFalse(result['success'])
        self.assertEqual(result['messages'],
                        ['The Account terry is currently marked as inactive.'])

    def test_raises_error_with_invalid_fetch_type(self):
        "fetch only accepts valid fetch_type's."
        with self.assertRaises(ValueError):
            self.fetcher.fetch(fetch_type='bibble')

    def test_does_not_raise_error_with_valid_fetch_type(self):
        try:
            self.fetcher.fetch(fetch_type='all')
        except ValueError:
            self.fail(
                "ScrobblesFetcher().fetch() raised ValueError unexpectedly")

    def test_raises_error_with_non_integer_days(self):
        "When fetching for a number of days"
        with self.assertRaises(ValueError):
            self.fetcher.fetch(fetch_type='days', days='oops')

    def test_no_error_with_integer_days(self):
        "When fetching for a number of days"
        try:
            self.fetcher.fetch(fetch_type='days', days=3)
        except ValueError:
            self.fail(
                "ScrobblesFetcher().fetch() raised ValueError unexpectedly")

    def test_returns_account(self):
        "Returned data should include the account name"
        results = self.fetcher.fetch()
        self.assertEqual(results['account'], 'Bob Ferris')

    def test_get_slugs_with_semicolon(self):
        """Successfully handles a URL that contains a semicolon.
        A track with a URL of 'http://www.last.fm/music/iamamiwhoami/_/;+john'
        was ending up with an empty track slug because ';' is seen as an
        alternative to '&' for separating query strings.
        """
        artist_slug, track_slug = self.fetcher._get_slugs(
                            'http://www.last.fm/music/iamamiwhoami/_/;+john')
        self.assertEqual(track_slug, ';+john')


class ScrobblesFetcherSendTestCase(TestCase):
    """
    Tests that DO involve sending requests to the API, and so we need to
    mock the requests.
    """

    fixture_path = 'tests/lastfm/fixtures/api/'

    def setUp(self):
        self.account = AccountFactory(username='bob', api_key='1234')
        self.fetcher = ScrobblesFetcher(account=self.account)
        self.sleep_patch = patch('time.sleep')
        self.sleep = self.sleep_patch.start()

    def tearDown(self):
        self.sleep_patch.stop()

    def load_raw_fixture(self, fixture_name):
        """
        Makes the JSON response to a call to the API.
        fixture_name -- eg 'messages' to load 'messages.json'.
        Returns the JSON text.
        """
        json_file = open('%s%s.json' % (self.fixture_path, fixture_name))
        json_data = json_file.read()
        json_file.close()
        return json_data

    def load_fixture(self, fixture_name):
        """
        Returns the json.loads() version of the JSON fixture.
        ie, a python list or dict, not plain text.
        fixture_name -- eg 'messages' to load 'messages.json'.
        """
        return json.loads(self.load_raw_fixture(fixture_name))

    def add_response(self, body, url, status=200):
        """
        Add a mocked response.

        Keyword arguments:
        body -- The JSON string representing the body of the response.
        url -- The request URL.
        status -- Int, HTTP response status.
        """
        responses.add(
            responses.GET,
            url,
            status=status,
            body=body,
            match_querystring=True,
            content_type='application/json; charset=utf-8'
        )

    def add_recent_tracks_response(self, body=None, page=1, status=200, from_time=None):
        """
        Add a mocked response to the get recent tracks API method.

        body -- Alternate JSON text response to the default success response.
        from_time -- A UTC unixtime value.
        """

        url = 'http://ws.audioscrobbler.com/2.0/?method=user.getrecenttracks&user=bob&api_key=1234&format=json&page=%s&limit=200' % page

        if from_time is not None:
            url += '&from=%s' % from_time

        if body is None:
            # Default success response
            body = self.load_raw_fixture('user_getrecenttracks')

        self.add_response(body=body, url=url, status=status)

    @responses.activate
    def test_returns_error_when_request_fails(self):
        "If the API request fails, fetch() should return an error."
        self.add_recent_tracks_response(status=500)
        results = self.fetcher.fetch()
        self.assertFalse(results['success'])
        self.assertIn(
                'Error when fetching Scrobbles (page 1): 500 Server Error',
                results['messages'][0])

    @responses.activate
    def test_returns_error_when_request_contains_error(self):
        "If API response contains an error message, fetch() should return it."
        self.add_recent_tracks_response(
                            body='{"error": 10, "message": "Invalid API Key"}')
        results = self.fetcher.fetch()
        self.assertFalse(results['success'])
        self.assertIn(
                'Error 10 when fetching Scrobbles (page 1): Invalid API Key',
                results['messages'][0])

    @responses.activate
    def test_sends_from_time_correctly_for_recent(self):
        "Sends the correct min time to API if we only want recent results."
        # We should fetch results from this scrobble's post_time onwards:
        scrobble = ScrobbleFactory(
            post_time=datetime.datetime.strptime(
                '2015-08-11 12:00:00', '%Y-%m-%d %H:%M:%S').replace(
                                                            tzinfo=pytz.utc))
        # Timestamp for 2015-08-11 12:00:00 UTC:
        self.add_recent_tracks_response(from_time=1439294400)
        self.fetcher.fetch(fetch_type='recent')
        self.assertIn('from=1439294400', responses.calls[0].request.url)

    @responses.activate
    @freeze_time("2015-08-14 12:00:00", tz_offset=0)
    def test_sends_from_time_correctly_for_days(self):
        "Sends the correct min time to API if we only want n days' results."
        # Timestamp for 2015-08-11 12:00:00 UTC:
        self.add_recent_tracks_response(from_time=1439294400)
        self.fetcher.fetch(fetch_type='days', days=3)
        self.assertIn('from=1439294400', responses.calls[0].request.url)

    @responses.activate
    def test_requests_multiple_pages(self):
        "Fetches multiple pages of results if there are multiple."
        body = self.load_fixture('user_getrecenttracks')
        body['recenttracks']['@attr']['totalPages'] = "2"
        self.add_recent_tracks_response(body=json.dumps(body))
        body['recenttracks']['@attr']['page'] = "2"
        self.add_recent_tracks_response(body=json.dumps(body), page=2)
        self.fetcher.fetch()
        self.assertEqual(len(responses.calls), 2)
        self.assertIn('page=1', responses.calls[0].request.url)
        self.assertIn('page=2', responses.calls[1].request.url)

    @responses.activate
    def test_returns_correct_scrobble_count(self):
        "Should return the number of scrobbles fetched."
        self.add_recent_tracks_response()
        results = self.fetcher.fetch()
        # We have this many finished scrobbles in our JSON fixture:
        self.assertEqual(results['fetched'], 3)

    @responses.activate
    def test_doesnt_add_nowplaying_track(self):
        "Doesn't save data from a currently-playing scrobble."
        self.add_recent_tracks_response()
        results = self.fetcher.fetch()
        artists = Artist.objects.filter(name='K.Flay')
        self.assertEqual(len(artists), 0)

    @responses.activate
    def test_creates_new_artist(self):
        "Creates a new Artist if it doesn't exist"
        self.add_recent_tracks_response()
        results = self.fetcher.fetch()
        artists = Artist.objects.filter(slug='lou+reed')
        self.assertEqual(len(artists), 1)
        self.assertEqual(artists[0].slug, 'lou+reed')
        self.assertEqual(artists[0].original_slug, 'Lou+Reed')
        self.assertEqual(artists[0].name, 'Lou Reed')
        self.assertEqual(artists[0].mbid,
                        '9d1ebcfe-4c15-4d18-95d3-d919898638a1')

    @responses.activate
    def test_updates_existing_artist(self):
        "Doesn't create a new Artist if it already exists"
        ArtistFactory(slug='lou+reed', mbid='')
        self.add_recent_tracks_response()
        results = self.fetcher.fetch()
        artists = Artist.objects.filter(slug='lou+reed')
        self.assertEqual(len(artists), 1)
        self.assertEqual(artists[0].slug, 'lou+reed')
        self.assertEqual(artists[0].original_slug, 'Lou+Reed')
        self.assertEqual(artists[0].name, 'Lou Reed')
        self.assertEqual(artists[0].mbid,
                        '9d1ebcfe-4c15-4d18-95d3-d919898638a1')

    @responses.activate
    def test_ignores_case_when_finding_artist(self):
        "Should match an Artist with slug 'Lou+Reed' with 'lou+reed'."
        ArtistFactory(slug='lou+reed', name='Lou Reed', mbid='')
        self.add_recent_tracks_response()
        results = self.fetcher.fetch()
        artists = Artist.objects.filter(name='Lou Reed')
        self.assertEqual(len(artists), 1)

    @responses.activate
    def test_creates_new_track(self):
        "Creates a new Track if it doesn't exist"
        self.add_recent_tracks_response()
        results = self.fetcher.fetch()
        loureed = Artist.objects.get(slug='lou+reed')
        tracks = Track.objects.filter(name='Make Up', slug='make+up')
        self.assertEqual(len(tracks), 1)
        self.assertEqual(tracks[0].name,'Make Up')
        self.assertEqual(tracks[0].slug,'make+up')
        self.assertEqual(tracks[0].original_slug,'Make+Up')
        self.assertEqual(tracks[0].mbid,'8e73b23a-6a01-4743-b414-047974f66e22')
        self.assertEqual(tracks[0].artist, loureed)

    @responses.activate
    def test_updates_existing_track(self):
        "Doesn't create a new Track if it already exists"
        loureed = ArtistFactory(slug='lou+reed')
        TrackFactory(artist=loureed, slug='make+up')
        self.add_recent_tracks_response()
        results = self.fetcher.fetch()
        tracks = Track.objects.filter(slug='make+up')
        self.assertEqual(len(tracks), 1)
        self.assertEqual(tracks[0].name,'Make Up')
        self.assertEqual(tracks[0].slug,'make+up')
        self.assertEqual(tracks[0].original_slug,'Make+Up')
        self.assertEqual(tracks[0].mbid,'8e73b23a-6a01-4743-b414-047974f66e22')
        self.assertEqual(tracks[0].artist, loureed)

    @responses.activate
    def test_creates_new_album(self):
        "Creates a new Album if it doesn't exist"
        self.add_recent_tracks_response()
        results = self.fetcher.fetch()
        loureed = Artist.objects.get(slug='lou+reed')
        albums = Album.objects.filter(slug='transformer')
        self.assertEqual(len(albums), 1)
        self.assertEqual(albums[0].slug,'transformer')
        self.assertEqual(albums[0].original_slug,'Transformer')
        self.assertEqual(albums[0].name,'Transformer')
        self.assertEqual(albums[0].mbid,'4ee40d97-630c-3f0d-9ea2-d49fa253c354')
        self.assertEqual(albums[0].artist, loureed)

    @responses.activate
    def test_updates_existing_album(self):
        "Doesn't create a new Album if it already exists"
        loureed = ArtistFactory(slug='lou+reed')
        AlbumFactory(artist=loureed, slug='transformer')
        self.add_recent_tracks_response()
        results = self.fetcher.fetch()
        albums = Album.objects.filter(slug='transformer')
        self.assertEqual(len(albums), 1)
        self.assertEqual(albums[0].name,'Transformer')
        self.assertEqual(albums[0].slug,'transformer')
        self.assertEqual(albums[0].original_slug,'Transformer')
        self.assertEqual(albums[0].mbid,'4ee40d97-630c-3f0d-9ea2-d49fa253c354')
        self.assertEqual(albums[0].artist, loureed)

    @responses.activate
    def test_does_not_create_album_if_it_has_no_name(self):
        "Doesn't create a new Album if the scrobble has none"
        self.add_recent_tracks_response()
        results = self.fetcher.fetch()
        artist = Artist.objects.get(slug='%5bunknown%5d')
        albums = Album.objects.filter(artist=artist)
        self.assertEqual(len(albums), 0)

    @responses.activate
    @patch('ditto.lastfm.fetch.slugify_name')
    def test_slugifies_album_name(self, slugify_name):
        "It should call slugify_name for each scrobbled Album name."
        slugify_name.side_effect = ['Spotify+Session', 'Transformer',]
        self.add_recent_tracks_response()
        results = self.fetcher.fetch()
        slugify_name.assert_has_calls([
            call('Spotify Session'),
            call('Transformer'),
        ])

    @responses.activate
    def test_creates_scrobbles(self):
        "Creates new scrobble objects"
        self.add_recent_tracks_response()
        results = self.fetcher.fetch()
        scrobbles = Scrobble.objects.all()
        # We have this many finished scrobbles in our JSON fixture:
        self.assertEqual(len(scrobbles), 3)

    @responses.activate
    def test_updates_existing_scrobbles(self):
        "Updates existing scrobble objects"
        # Make our existing scrobble:
        artist = ArtistFactory(slug='lou+reed')
        track = TrackFactory(artist=artist, slug='make+up')
        post_time = datetime.datetime.strptime(
                        '2016-09-22 09:23:33', '%Y-%m-%d %H:%M:%S'
                    ).replace(tzinfo=pytz.utc)
        scrobble = ScrobbleFactory(account=self.account,
                                   track=track,
                                   post_time=post_time)

        self.add_recent_tracks_response()
        results = self.fetcher.fetch(fetch_type='all')

        scrobbles = Scrobble.objects.all()
        # We have this many finished scrobbles in our JSON fixture:
        self.assertEqual(len(scrobbles), 3)
        scrobble_reloaded = Scrobble.objects.get(artist=artist)
        self.assertEqual(scrobble.pk, scrobble_reloaded.pk)

    @responses.activate
    @freeze_time("2015-08-14 12:00:00", tz_offset=0)
    def test_sets_scrobble_data(self):
        "Sets all the scrobble data correctly"
        self.add_recent_tracks_response()
        results = self.fetcher.fetch(fetch_type='all')
        scrobble = Scrobble.objects.get(artist__slug='lou+reed')
        self.assertEqual(scrobble.account, self.account)
        self.assertEqual(scrobble.track.slug, 'make+up')
        self.assertEqual(scrobble.album.slug, 'transformer')
        self.assertEqual(scrobble.post_time,
                            datetime.datetime.strptime(
                                    '2016-09-22 09:23:33', '%Y-%m-%d %H:%M:%S'
                                ).replace(tzinfo=pytz.utc))
        json_data = self.load_fixture('user_getrecenttracks')
        scrobble_json = json_data['recenttracks']['track'][2]
        self.assertEqual(scrobble.raw, json.dumps(scrobble_json))
        self.assertEqual(scrobble.fetch_time, datetime_now())

    @responses.activate
    def test_leaves_album_blank(self):
        "If scrobble has no album, leaves its fields empty"
        self.add_recent_tracks_response()
        results = self.fetcher.fetch(fetch_type='all')
        scrobble = Scrobble.objects.get(artist__slug='%5bunknown%5d')
        self.assertEqual(scrobble.album, None)


class ScrobblesMultiAccountFetcherTestCase(TestCase):
    """
    Testing the MultiAccount version by completely patching the standard
    Fetcher that it calls.
    """

    def setUp(self):
        self.account_1 = AccountFactory(api_key='1234', username='bob')
        self.inactive_account = AccountFactory(api_key='2345', username='terry',
                                                            is_active=False)
        self.account_2 = AccountFactory(api_key='3456', username='thelma')

        self.ScrobblesFetcher_patch = patch(
                                        'ditto.lastfm.fetch.ScrobblesFetcher')
        self.ScrobblesFetcher = self.ScrobblesFetcher_patch.start()

    def tearDown(self):
        self.ScrobblesFetcher_patch.stop()

    def test_uses_all_active_accounts_by_default(self):
        ScrobblesMultiAccountFetcher().fetch()
        self.ScrobblesFetcher.assert_has_calls([
            call(self.account_1),
            call().fetch(),
            call(self.account_2),
            call().fetch(),
        ])

    def test_uses_one_account(self):
        "If an account is supplied, only uses that."
        ScrobblesMultiAccountFetcher(username='thelma').fetch()
        self.ScrobblesFetcher.assert_has_calls([
            call(self.account_2),
            call().fetch(),
        ])

    def test_passes_kwargs_to_fetch(self):
        "Passes kwargs to the ScrobbleFetcher.fetch() method"
        ScrobblesMultiAccountFetcher(username='bob').fetch(
                                                    fetch_type='days', days=3)
        self.ScrobblesFetcher.assert_has_calls([
            call(self.account_1),
            call().fetch(fetch_type='days', days=3),
        ])

    def test_raises_error_if_no_accounts_are_active(self):
        self.account_1.is_active = False
        self.account_1.save()
        self.account_2.is_active = False
        self.account_2.save()
        with self.assertRaises(FetchError):
            ScrobblesMultiAccountFetcher().fetch()

    def test_raises_error_if_supplied_account_does_not_exist(self):
        with self.assertRaises(FetchError):
            ScrobblesMultiAccountFetcher(username='audrey').fetch()

    def test_raises_error_if_supplied_account_is_inactive(self):
        with self.assertRaises(FetchError):
            ScrobblesMultiAccountFetcher(username='terry').fetch()


class ScrobblesMultiAccountFetcherResultsTestCase(TestCase):
    """
    Testing the return value from ScrobblesMultiAccountFetcher().fetch()
    and only need to patch ScrobblesFetcher().fetch().
    """
    def setUp(self):
        self.account_1 = AccountFactory(api_key='1234', username='bob')
        self.account_2 = AccountFactory(api_key='3456', username='thelma')

    @patch.object(ScrobblesFetcher, 'fetch')
    def test_return_value(self, fetch):
        "Return should be a list of return values from ScrobbleFetcher.fetch()"
        ret = {'success': True, 'account': 'bob', 'fetched': 7,}
        fetch.side_effect = [ret, ret,]

        results = ScrobblesMultiAccountFetcher().fetch()
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]['account'], 'bob')

