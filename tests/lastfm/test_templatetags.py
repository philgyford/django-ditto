from django.test import TestCase

from ditto.core.utils import datetime_from_str
from ditto.lastfm.templatetags import ditto_lastfm
from ditto.lastfm.factories import AccountFactory, AlbumFactory,\
        ArtistFactory, ScrobbleFactory, TrackFactory


class TopAlbumsTestCase(TestCase):

    def setUp(self):
        self.artist1 = ArtistFactory()
        self.tracks = TrackFactory.create_batch(11, artist=self.artist1)
        self.albums = AlbumFactory.create_batch(11, artist=self.artist1)
        # Scrobble each album/track once:
        for idx, track in enumerate(self.tracks):
            ScrobbleFactory(artist=self.artist1,
                            track=track,
                            album=self.albums[idx])

        # Extra scrobbles.
        # For artist1, tracks[1] will be 1st, tracks[2] will be 2nd:
        ScrobbleFactory.create_batch(2, artist=self.artist1,
                                    track=self.tracks[1], album=self.albums[1])
        ScrobbleFactory.create_batch(1, artist=self.artist1,
                                    track=self.tracks[2], album=self.albums[2])

        # But artist2 has a more scrobbled album:
        self.artist2 = ArtistFactory()
        self.track2 = TrackFactory(artist=self.artist2)
        self.album2 = AlbumFactory(artist=self.artist2)
        ScrobbleFactory.create_batch(4, artist=self.artist2,
                                track=self.track2, album=self.album2)

    def test_order(self):
        "The most scrobbled albums should be first."
        albums = ditto_lastfm.top_albums()
        self.assertEqual(albums[0], self.album2)
        self.assertEqual(albums[1], self.albums[1])
        self.assertEqual(albums[2], self.albums[2])

    def test_default_limit(self):
        "By default should return 10 albums."
        albums = ditto_lastfm.top_albums()
        self.assertEqual(len(albums), 10)

    def test_limit(self):
        "Should return `limit` albums."
        albums = ditto_lastfm.top_albums(limit=3)
        self.assertEqual(len(albums), 3)

    def test_limit_all(self):
        "Should return all albums if `limit` is 'all'."
        albums = ditto_lastfm.top_albums(limit='all')
        self.assertEqual(len(albums), 12)

    def test_for_artist(self):
        "Should only return the artist's albums"
        albums = ditto_lastfm.top_albums(artist=self.artist1, limit='all')
        self.assertEqual(len(albums), 11)
        self.assertEqual(albums[0], self.albums[1])
        self.assertEqual(albums[1], self.albums[2])

    def test_for_day_with_datetime(self):
        "Should return only albums from the requested day, using datetime."
        # 2 scrobbles on this day:
        ScrobbleFactory(track=self.tracks[1], album=self.albums[1],
                        post_time=datetime_from_str('2016-10-01 00:00:00'))
        ScrobbleFactory(track=self.tracks[1], album=self.albums[1],
                        post_time=datetime_from_str('2016-10-01 23:59:59'))
        # 1 scrobble on this day:
        ScrobbleFactory(track=self.tracks[2], album=self.albums[2],
                        post_time=datetime_from_str('2016-10-02 12:00:00'))

        albums = ditto_lastfm.top_albums(period='day',
                        date=datetime_from_str('2016-10-01 00:00:00'))
        self.assertEqual(len(albums), 1)
        self.assertEqual(albums[0].scrobble_count, 2)

    def test_for_day_with_date(self):
        "Should return only albums from the requested day, using date."
        # 2 scrobbles on this day:
        ScrobbleFactory(track=self.tracks[1], album=self.albums[1],
                        post_time=datetime_from_str('2016-10-01 00:00:00'))
        ScrobbleFactory(track=self.tracks[1], album=self.albums[1],
                        post_time=datetime_from_str('2016-10-01 23:59:59'))
        # 1 scrobble on this day:
        ScrobbleFactory(track=self.tracks[2], album=self.albums[2],
                        post_time=datetime_from_str('2016-10-02 12:00:00'))

        albums = ditto_lastfm.top_albums(period='day',
                        date=datetime_from_str('2016-10-01 00:00:00').date())
        self.assertEqual(len(albums), 1)
        self.assertEqual(albums[0].scrobble_count, 2)

    def test_for_month(self):
        "Should return only albums from the requested month."
        # 2 scrobbles in this month:
        ScrobbleFactory(track=self.tracks[1], album=self.albums[1],
                        post_time=datetime_from_str('2016-09-01 12:00:00'))
        ScrobbleFactory(track=self.tracks[1], album=self.albums[1],
                        post_time=datetime_from_str('2016-09-30 12:00:00'))
        # 1 scrobble in this month:
        ScrobbleFactory(track=self.tracks[2], album=self.albums[2],
                        post_time=datetime_from_str('2016-10-01 12:00:00'))

        albums = ditto_lastfm.top_albums(period='month',
                        date=datetime_from_str('2016-09-15 00:00:00'))
        self.assertEqual(len(albums), 1)
        self.assertEqual(albums[0].scrobble_count, 2)

    def test_for_year(self):
        "Should return only albums from the requested year."
        # 2 scrobbles in this year:
        ScrobbleFactory(track=self.tracks[1], album=self.albums[1],
                        post_time=datetime_from_str('2015-01-01 12:00:00'))
        ScrobbleFactory(track=self.tracks[1], album=self.albums[1],
                        post_time=datetime_from_str('2015-12-31 12:00:00'))
        # 1 scrobble in this year:
        ScrobbleFactory(track=self.tracks[2], album=self.albums[2],
                        post_time=datetime_from_str('2016-03-01 12:00:00'))

        albums = ditto_lastfm.top_albums(period='year',
                        date=datetime_from_str('2015-09-01 00:00:00'))
        self.assertEqual(len(albums), 1)
        self.assertEqual(albums[0].scrobble_count, 2)

    def test_for_account(self):
        "Should only count scrobbles by supplied Account."
        account = AccountFactory()
        # Our 1 scrobble by this account:
        ScrobbleFactory(account=account,
            artist=self.artist1, track=self.tracks[1], album=self.albums[1])
        albums = ditto_lastfm.top_albums(account=account, limit='all')
        self.assertEqual(len(albums), 1)
        self.assertEqual(albums[0], self.albums[1])
        self.assertEqual(albums[0].scrobble_count, 1)

    def test_account_error(self):
        "Should raise TypeError if invalid Account is supplied."
        with self.assertRaises(TypeError):
            ditto_lastfm.top_albums(account='bob', limit=3)

    def test_artist_error(self):
        "Should raise TypeError if invalid Artist is supplied."
        with self.assertRaises(TypeError):
            ditto_lastfm.top_albums(artist='bob', limit=3)

    def test_limit_error(self):
        "Should raise ValueError if `limit` is invalid."
        with self.assertRaises(ValueError):
            ditto_lastfm.top_albums(artist=self.artist1, limit='bob')

    def test_date_error(self):
        "Should raise TypeError if invalid date is supplied."
        with self.assertRaises(TypeError):
            ditto_lastfm.top_albums(date='bob', period='month')

    def test_period_error(self):
        "Should raise TypeError if invalid period is supplied."
        d = datetime_from_str('2016-10-24 12:00:00')
        with self.assertRaises(TypeError):
            ditto_lastfm.top_albums(date=d, period='bob')


class TopArtistsTestCase(TestCase):

    def setUp(self):
        self.artists = ArtistFactory.create_batch(11)
        self.tracks = []
        # Each artist has one track, scrobbled once:
        for artist in self.artists:
            track = TrackFactory(artist=artist)
            self.tracks.append(track)
            ScrobbleFactory(artist=artist, track=track)

        # Extra scrobbles.
        # For tracks[1] will be 1st, tracks[2] will be 2nd:
        ScrobbleFactory.create_batch(2,
                                artist=self.artists[1], track=self.tracks[1])
        ScrobbleFactory.create_batch(1,
                                artist=self.artists[2], track=self.tracks[2])

    def test_order(self):
        "The most scrobbled artists should be first"
        artists = ditto_lastfm.top_artists()
        self.assertEqual(artists[0], self.artists[1])
        self.assertEqual(artists[1], self.artists[2])

    def test_default_limit(self):
        "By default should return 10 artists."
        artists = ditto_lastfm.top_artists()
        self.assertEqual(len(artists), 10)

    def test_for_account(self):
        "Should only count Scrobbles by the supplied Account."
        account = AccountFactory()
        # Our one scrobble by this account:
        ScrobbleFactory(account=account,
                                artist=self.artists[1], track=self.tracks[1])
        artists = ditto_lastfm.top_artists(account=account)
        self.assertEqual(len(artists), 1)
        self.assertEqual(artists[0].scrobble_count, 1)

    def test_for_day_with_datetime(self):
        "Should return only artists from the requested day, using datetime."
        # 2 scrobbles on this day:
        ScrobbleFactory(track=self.tracks[1], artist=self.artists[1],
                        post_time=datetime_from_str('2016-10-01 00:00:00'))
        ScrobbleFactory(track=self.tracks[1], artist=self.artists[1],
                        post_time=datetime_from_str('2016-10-01 23:59:59'))
        # 1 scrobble on this day:
        ScrobbleFactory(track=self.tracks[2], artist=self.artists[2],
                        post_time=datetime_from_str('2016-10-02 12:00:00'))

        artists = ditto_lastfm.top_artists(period='day',
                        date=datetime_from_str('2016-10-01 00:00:00'))
        self.assertEqual(len(artists), 1)
        self.assertEqual(artists[0].scrobble_count, 2)

    def test_for_day_with_date(self):
        "Should return only artists from the requested day, using date."
        # 2 scrobbles on this day:
        ScrobbleFactory(track=self.tracks[1], artist=self.artists[1],
                        post_time=datetime_from_str('2016-10-01 00:00:00'))
        ScrobbleFactory(track=self.tracks[1], artist=self.artists[1],
                        post_time=datetime_from_str('2016-10-01 23:59:59'))
        # 1 scrobble on this day:
        ScrobbleFactory(track=self.tracks[2], artist=self.artists[2],
                        post_time=datetime_from_str('2016-10-02 12:00:00'))

        artists = ditto_lastfm.top_artists(period='day',
                        date=datetime_from_str('2016-10-01 00:00:00').date())
        self.assertEqual(len(artists), 1)
        self.assertEqual(artists[0].scrobble_count, 2)

    def test_for_month(self):
        "Should return only tracks from the requested month."
        # 2 scrobbles in this month:
        ScrobbleFactory(track=self.tracks[1], artist=self.artists[1],
                        post_time=datetime_from_str('2016-09-01 12:00:00'))
        ScrobbleFactory(track=self.tracks[1], artist=self.artists[1],
                        post_time=datetime_from_str('2016-09-30 12:00:00'))
        # 1 scrobble in this month:
        ScrobbleFactory(track=self.tracks[2], artist=self.artists[2],
                        post_time=datetime_from_str('2016-10-01 12:00:00'))

        artists = ditto_lastfm.top_artists(period='month',
                        date=datetime_from_str('2016-09-15 00:00:00'))
        self.assertEqual(len(artists), 1)
        self.assertEqual(artists[0].scrobble_count, 2)

    def test_for_year(self):
        "Should return only tracks from the requested year."
        # 2 scrobbles in this year:
        ScrobbleFactory(track=self.tracks[1], artist=self.artists[1],
                        post_time=datetime_from_str('2015-01-01 12:00:00'))
        ScrobbleFactory(track=self.tracks[1], artist=self.artists[1],
                        post_time=datetime_from_str('2015-12-31 12:00:00'))
        # 1 scrobble in this year:
        ScrobbleFactory(track=self.tracks[2], artist=self.artists[2],
                        post_time=datetime_from_str('2016-03-01 12:00:00'))

        artists = ditto_lastfm.top_artists(period='year',
                        date=datetime_from_str('2015-09-01 00:00:00'))
        self.assertEqual(len(artists), 1)
        self.assertEqual(artists[0].scrobble_count, 2)

    def test_limit(self):
        "Should return `limit` artists."
        artists = ditto_lastfm.top_artists(limit=3)
        self.assertEqual(len(artists), 3)

    def test_limit_all(self):
        "Should return all artists if `limit` is 'all'."
        artists = ditto_lastfm.top_artists(limit='all')
        self.assertEqual(len(artists), 11)

    def test_account_error(self):
        "Should raise TypeError if invalid Account is supplied."
        with self.assertRaises(TypeError):
            ditto_lastfm.top_artists(account='bob', limit=3)

    def test_limit_error(self):
        "Should raise ValueError if `limit` is invalid."
        with self.assertRaises(ValueError):
            ditto_lastfm.top_artists(limit='bob')

    def test_date_error(self):
        "Should raise TypeError if invalid date is supplied."
        with self.assertRaises(TypeError):
            ditto_lastfm.top_artists(date='bob', period='month')

    def test_period_error(self):
        "Should raise TypeError if invalid period is supplied."
        d = datetime_from_str('2016-10-24 12:00:00')
        with self.assertRaises(TypeError):
            ditto_lastfm.top_artists(date=d, period='bob')


class TopTracksTestCase(TestCase):

    def setUp(self):
        self.album1 = AlbumFactory()
        self.artist1 = ArtistFactory()
        self.tracks = TrackFactory.create_batch(11, artist=self.artist1)
        # Extra scrobbles.
        # For artist1, tracks[1] will be 1st, tracks[2] will be 2nd:
        ScrobbleFactory.create_batch(2,
                album=self.album1, artist=self.artist1, track=self.tracks[1])
        ScrobbleFactory.create_batch(1,
                album=self.album1, artist=self.artist1, track=self.tracks[2])

        # But artist2 has a more-scrobbled Track:
        self.album2 = AlbumFactory()
        self.artist2 = ArtistFactory()
        self.track2 = TrackFactory(artist=self.artist2)
        ScrobbleFactory.create_batch(4,
                album=self.album2, artist=self.artist2, track=self.track2)

    def test_order(self):
        "The most scrobbled tracks should be first."
        tracks = ditto_lastfm.top_tracks()
        self.assertEqual(tracks[0], self.track2)
        self.assertEqual(tracks[1], self.tracks[1])
        self.assertEqual(tracks[2], self.tracks[2])

    def test_default_limit(self):
        "By default should return 10 tracks."
        tracks = ditto_lastfm.top_tracks()
        self.assertEqual(len(tracks), 10)

    def test_limit(self):
        "Should return `limit` tracks."
        tracks = ditto_lastfm.top_tracks(limit=3)
        self.assertEqual(len(tracks), 3)

    def test_limit_all(self):
        "Should return all tracks if `limit` is 'all'."
        tracks = ditto_lastfm.top_tracks(limit='all')
        self.assertEqual(len(tracks), 12)

    def test_for_account(self):
        "Should only count scrobbles by the supplied Account."
        account = AccountFactory()
        # Our one scrobble by this account:
        ScrobbleFactory(account=account,
                        artist=self.artist1, track=self.tracks[1])
        tracks = ditto_lastfm.top_tracks(account=account, limit='all')
        self.assertEqual(len(tracks), 1)
        self.assertEqual(tracks[0], self.tracks[1])
        self.assertEqual(tracks[0].scrobble_count, 1)

    def test_for_album(self):
        "Should return only the tracks on that Album."
        tracks = ditto_lastfm.top_tracks(album=self.album1, limit='all')
        self.assertEqual(len(tracks), 2)
        self.assertEqual(tracks[0], self.tracks[1])
        self.assertEqual(tracks[1], self.tracks[2])

    def test_for_artist(self):
        "Should return only the Artist's tracks."
        tracks = ditto_lastfm.top_tracks(artist=self.artist1, limit='all')
        self.assertEqual(len(tracks), 2)
        self.assertEqual(tracks[0], self.tracks[1])
        self.assertEqual(tracks[1], self.tracks[2])

    def test_for_day_with_datetime(self):
        "Should return only tracks from the requested day, using datetime."
        # 2 scrobbles on this day:
        ScrobbleFactory(track=self.tracks[1],
                        post_time=datetime_from_str('2016-10-01 00:00:00'))
        ScrobbleFactory(track=self.tracks[1],
                        post_time=datetime_from_str('2016-10-01 23:59:59'))
        # 1 scrobble on this day:
        ScrobbleFactory(track=self.tracks[2],
                        post_time=datetime_from_str('2016-10-02 12:00:00'))

        tracks = ditto_lastfm.top_tracks(period='day',
                        date=datetime_from_str('2016-10-01 00:00:00'))
        self.assertEqual(len(tracks), 1)
        self.assertEqual(tracks[0].scrobble_count, 2)

    def test_for_day_with_date(self):
        "Should return only tracks from the requested day, using date."
        # 2 scrobbles on this day:
        ScrobbleFactory(track=self.tracks[1],
                        post_time=datetime_from_str('2016-10-01 00:00:00'))
        ScrobbleFactory(track=self.tracks[1],
                        post_time=datetime_from_str('2016-10-01 23:59:59'))
        # 1 scrobble on this day:
        ScrobbleFactory(track=self.tracks[2],
                        post_time=datetime_from_str('2016-10-02 12:00:00'))

        tracks = ditto_lastfm.top_tracks(period='day',
                        date=datetime_from_str('2016-10-01 00:00:00').date())
        self.assertEqual(len(tracks), 1)
        self.assertEqual(tracks[0].scrobble_count, 2)

    def test_for_month(self):
        "Should return only tracks from the requested month."
        # 2 scrobbles in this month:
        ScrobbleFactory(track=self.tracks[1],
                        post_time=datetime_from_str('2016-09-01 12:00:00'))
        ScrobbleFactory(track=self.tracks[1],
                        post_time=datetime_from_str('2016-09-30 12:00:00'))
        # 1 scrobble in this month:
        ScrobbleFactory(track=self.tracks[2],
                        post_time=datetime_from_str('2016-10-01 12:00:00'))

        tracks = ditto_lastfm.top_tracks(period='month',
                        date=datetime_from_str('2016-09-15 00:00:00'))
        self.assertEqual(len(tracks), 1)
        self.assertEqual(tracks[0].scrobble_count, 2)

    def test_for_year(self):
        "Should return only tracks from the requested year."
        # 2 scrobbles in this year:
        ScrobbleFactory(track=self.tracks[1],
                        post_time=datetime_from_str('2015-01-01 12:00:00'))
        ScrobbleFactory(track=self.tracks[1],
                        post_time=datetime_from_str('2015-12-31 12:00:00'))
        # 1 scrobble in this year:
        ScrobbleFactory(track=self.tracks[2],
                        post_time=datetime_from_str('2016-03-01 12:00:00'))

        tracks = ditto_lastfm.top_tracks(period='year',
                        date=datetime_from_str('2015-09-01 00:00:00'))
        self.assertEqual(len(tracks), 1)
        self.assertEqual(tracks[0].scrobble_count, 2)

    def test_account_error(self):
        "Should raise TypeError if invalid Account is supplied."
        with self.assertRaises(TypeError):
            ditto_lastfm.top_tracks(account='bob', limit=3)

    def test_artist_error(self):
        "Should raise TypeError if invalid Artist is supplied."
        with self.assertRaises(TypeError):
            ditto_lastfm.top_tracks(artist='bob', limit=3)

    def test_limit_error(self):
        "Should raise ValueError if `limit` is invalid."
        with self.assertRaises(ValueError):
            ditto_lastfm.top_tracks(artist=self.artist1, limit='bob')

    def test_date_error(self):
        "Should raise TypeError if invalid date is supplied."
        with self.assertRaises(TypeError):
            ditto_lastfm.top_tracks(date='bob', period='month')

    def test_period_error(self):
        "Should raise TypeError if invalid period is supplied."
        d = datetime_from_str('2016-10-24 12:00:00')
        with self.assertRaises(TypeError):
            ditto_lastfm.top_tracks(date=d, period='bob')


class RecentScrobblesTestCase(TestCase):

    def setUp(self):
        self.account1 = AccountFactory()
        self.account2 = AccountFactory()
        scrobbles1 = ScrobbleFactory.create_batch(11, account=self.account1)
        self.scrobble2 = ScrobbleFactory(account=self.account2)

    def test_for_account(self):
        "With an Account, it gets its recent scrobbles"
        scrobbles = ditto_lastfm.recent_scrobbles(
                                            account=self.account1, limit=12)
        self.assertEqual(len(scrobbles), 11)
        self.assertNotIn(self.scrobble2, scrobbles)

    def test_default_limit(self):
        "It returns 10 by default"
        scrobbles = ditto_lastfm.recent_scrobbles()
        self.assertEqual(len(scrobbles), 10)

    def test_limit(self):
        "It returns `limit` scrobbles"
        scrobbles = ditto_lastfm.recent_scrobbles(limit=3)
        self.assertEqual(len(scrobbles), 3)

    def test_account_error(self):
        "Should raise TypeError if invalid Account is supplied."
        with self.assertRaises(TypeError):
            ditto_lastfm.recent_scrobbles(account='bob', limit=3)

    def test_limit_error(self):
        "It throws an error if limit isn't an integer"
        with self.assertRaises(ValueError):
            ditto_lastfm.recent_scrobbles(limit='bob')


class AnnualScrobbleCountsTestCase(TestCase):

    def setUp(self):
        self.account1 = AccountFactory()
        self.account2 = AccountFactory()
        # Some for account1 in 2015 and 2016:
        scrobbles1 = ScrobbleFactory.create_batch(3,
                            post_time=datetime_from_str('2015-01-01 12:00:00'),
                            account=self.account1)
        scrobbles2 = ScrobbleFactory.create_batch(2,
                            post_time=datetime_from_str('2016-01-01 12:00:00'),
                            account=self.account1)
        # And one for account2 in 2015:
        scrobble3 = ScrobbleFactory(account=self.account2,
                            post_time=datetime_from_str('2015-01-01 12:00:00'))

    def test_response(self):
        "Returns correct data for all accounts."
        scrobbles = ditto_lastfm.annual_scrobble_counts()
        self.assertEqual(len(scrobbles), 2)
        self.assertEqual(scrobbles[0]['year'], 2015)
        self.assertEqual(scrobbles[0]['count'], 4)
        self.assertEqual(scrobbles[1]['year'], 2016)
        self.assertEqual(scrobbles[1]['count'], 2)

    def test_response_for_account(self):
        "Returns correct data for one account."
        scrobbles = ditto_lastfm.annual_scrobble_counts(account=self.account1)
        self.assertEqual(len(scrobbles), 2)
        self.assertEqual(scrobbles[0]['year'], 2015)
        self.assertEqual(scrobbles[0]['count'], 3)
        self.assertEqual(scrobbles[1]['year'], 2016)
        self.assertEqual(scrobbles[1]['count'], 2)

    def test_account_error(self):
        "Should raise TypeError if invalid Account is supplied."
        with self.assertRaises(TypeError):
            ditto_lastfm.recent_scrobbles(account='bob', limit=3)

    def test_empty_years(self):
        "It should include years for which there are no scrobbles."
        # Add a scrobble in 2018, leaving a gap for 2017:
        ScrobbleFactory(post_time=datetime_from_str('2018-01-01 12:00:00'))
        scrobbles = ditto_lastfm.annual_scrobble_counts()
        self.assertEqual(len(scrobbles), 4)
        self.assertEqual(scrobbles[2]['year'], 2017)
        self.assertEqual(scrobbles[2]['count'], 0)


class DayScrobblesTestCase(TestCase):

    def setUp(self):
        self.account1 = AccountFactory()
        self.account2 = AccountFactory()
        # Some for account1 on 1st Oct:
        self.scrobble1 = ScrobbleFactory(
                            post_time=datetime_from_str('2016-10-01 12:00:00'),
                            account=self.account1)
        self.scrobble2 = ScrobbleFactory(
                            post_time=datetime_from_str('2016-10-01 12:05:00'),
                            account=self.account1)
        # One for account1 on 2nd Oct:
        self.scrobble3 = ScrobbleFactory(
                            post_time=datetime_from_str('2016-10-02 00:00:01'),
                            account=self.account1)
        # And one for account2 on 1st Oct:
        self.scrobble4 = ScrobbleFactory(account=self.account2,
                            post_time=datetime_from_str('2016-10-01 13:00:00'))

    def test_for_all_accounts(self):
        "Returns ALL scrobbles from requested date."
        scrobbles = ditto_lastfm.day_scrobbles(
                                    datetime_from_str('2016-10-01 00:00:00'))
        self.assertEqual(len(scrobbles), 3)
        self.assertEqual(scrobbles[0], self.scrobble1)
        self.assertEqual(scrobbles[1], self.scrobble2)
        self.assertEqual(scrobbles[2], self.scrobble4)

    def test_for_one_accounts(self):
        "Only returns scrobbles for one account on requested date."
        scrobbles = ditto_lastfm.day_scrobbles(
                                account=self.account1,
                                date=datetime_from_str('2016-10-01 00:00:00'))
        self.assertEqual(len(scrobbles), 2)
        self.assertEqual(scrobbles[0], self.scrobble1)
        self.assertEqual(scrobbles[1], self.scrobble2)

    def test_with_date(self):
        "Returns when using a date, not a datetime."
        d = datetime_from_str('2016-10-01 00:00:00').date()
        scrobbles = ditto_lastfm.day_scrobbles(date=d)
        self.assertEqual(len(scrobbles), 3)
        self.assertEqual(scrobbles[0], self.scrobble1)
        self.assertEqual(scrobbles[1], self.scrobble2)
        self.assertEqual(scrobbles[2], self.scrobble4)

    def test_date_error(self):
        "Should raise ValueError if no date is supplied."
        with self.assertRaises(ValueError):
            ditto_lastfm.day_scrobbles()

    def test_date_error(self):
        "Should raise TypeError if invalid date is supplied."
        with self.assertRaises(TypeError):
            ditto_lastfm.day_scrobbles(date='bob')

    def test_account_error(self):
        "Should raise TypeError if invalid Account is supplied."
        with self.assertRaises(TypeError):
            ditto_lastfm.day_scrobbles(account='bob')

