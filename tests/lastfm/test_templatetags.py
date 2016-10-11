from django.test import TestCase

from ditto.lastfm.templatetags import ditto_lastfm
from ditto.lastfm.factories import AlbumFactory, ArtistFactory,\
        ScrobbleFactory, TrackFactory


class ArtistTopTracksTestCase(TestCase):

    def setUp(self):
        self.artist = ArtistFactory()
        self.tracks = TrackFactory.create_batch(11, artist=self.artist)
        # tracks[1] will be 1st, tracks[2] will be 2nd:
        ScrobbleFactory.create_batch(2,
                                    artist=self.artist, track=self.tracks[1])
        ScrobbleFactory.create_batch(1,
                                    artist=self.artist, track=self.tracks[2])

    def test_top_tracks(self):
        "By default should return 10 tracks."
        tracks = ditto_lastfm.artist_top_tracks(artist=self.artist)
        self.assertEqual(len(tracks), 10)
        self.assertEqual(tracks[0], self.tracks[1])
        self.assertEqual(tracks[1], self.tracks[2])

    def test_top_tracks_limit(self):
        "Should return `limit` tracks."
        tracks = ditto_lastfm.artist_top_tracks(artist=self.artist, limit=3)
        self.assertEqual(len(tracks), 3)
        self.assertEqual(tracks[0], self.tracks[1])
        self.assertEqual(tracks[1], self.tracks[2])

    def test_top_tracks_all(self):
        "Should return all tracks if `limit` is 'all'."
        tracks = ditto_lastfm.artist_top_tracks(artist=self.artist, limit='all')
        self.assertEqual(len(tracks), 11)
        self.assertEqual(tracks[0], self.tracks[1])
        self.assertEqual(tracks[1], self.tracks[2])

    def test_artist_error(self):
        "Should raise ValueError if no Artist is supplied."
        with self.assertRaises(ValueError):
            ditto_lastfm.artist_top_tracks(limit=3)

    def test_limit_error(self):
        "Should raise ValueError if `limit` is invalid."
        with self.assertRaises(ValueError):
            ditto_lastfm.artist_top_tracks(artist=self.artist, limit='bob')


class ArtistTopAlbumsTestCase(TestCase):

    def setUp(self):
        self.artist = ArtistFactory()
        self.tracks = TrackFactory.create_batch(11, artist=self.artist)
        self.albums = AlbumFactory.create_batch(11, artist=self.artist)
        # Scrobble each album/track once:
        for idx, track in enumerate(self.tracks):
            ScrobbleFactory(artist=self.artist,
                            track=track,
                            album=self.albums[idx])

        # tracks[1] will be 1st, tracks[2] will be 2nd:
        ScrobbleFactory.create_batch(2, artist=self.artist,
                                    track=self.tracks[1], album=self.albums[1])
        ScrobbleFactory.create_batch(1, artist=self.artist,
                                    track=self.tracks[2], album=self.albums[2])

    def test_top_albums(self):
        "By default should return 10 albums."
        albums = ditto_lastfm.artist_top_albums(artist=self.artist)
        self.assertEqual(len(albums), 10)
        self.assertEqual(albums[0], self.albums[1])
        self.assertEqual(albums[1], self.albums[2])

    def test_top_albums_limit(self):
        "Should return `limit` albums."
        albums = ditto_lastfm.artist_top_albums(artist=self.artist, limit=3)
        self.assertEqual(len(albums), 3)
        self.assertEqual(albums[0], self.albums[1])
        self.assertEqual(albums[1], self.albums[2])

    def test_top_albums_all(self):
        "Should return all albums if `limit` is 'all'."
        albums = ditto_lastfm.artist_top_albums(artist=self.artist, limit='all')
        self.assertEqual(len(albums), 11)
        self.assertEqual(albums[0], self.albums[1])
        self.assertEqual(albums[1], self.albums[2])

    def test_artist_error(self):
        "Should raise ValueError if no Artist is supplied."
        with self.assertRaises(ValueError):
            ditto_lastfm.artist_top_albums(limit=3)

    def test_limit_error(self):
        "Should raise ValueError if `limit` is invalid."
        with self.assertRaises(ValueError):
            ditto_lastfm.artist_top_albums(artist=self.artist, limit='bob')

