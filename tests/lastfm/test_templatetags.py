from django.test import TestCase

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


class TopTracksTestCase(TestCase):

    def setUp(self):
        self.artist1 = ArtistFactory()
        self.tracks = TrackFactory.create_batch(11, artist=self.artist1)
        # Extra scrobbles.
        # For artist1, tracks[1] will be 1st, tracks[2] will be 2nd:
        ScrobbleFactory.create_batch(2,
                                    artist=self.artist1, track=self.tracks[1])
        ScrobbleFactory.create_batch(1,
                                    artist=self.artist1, track=self.tracks[2])

        # But artist2 has a more-scrobbled Track:
        self.artist2 = ArtistFactory()
        self.track2 = TrackFactory(artist=self.artist2)
        ScrobbleFactory.create_batch(4,
                                    artist=self.artist2, track=self.track2)

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

    def test_for_artist(self):
        "Should return only the Artist's tracks."
        tracks = ditto_lastfm.top_tracks(artist=self.artist1, limit='all')
        self.assertEqual(len(tracks), 2)
        self.assertEqual(tracks[0], self.tracks[1])
        self.assertEqual(tracks[1], self.tracks[2])

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
