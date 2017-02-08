from django.test import TestCase

from ditto.core.utils import datetime_from_str
from ditto.lastfm.factories import AccountFactory, AlbumFactory,\
        ArtistFactory, ScrobbleFactory, TrackFactory
from ditto.lastfm.models import Account, Album, Artist, Scrobble, Track


class AlbumManagersWithScrobbleCountsTestCase(TestCase):
    "Testing the WithScrobbleCountsManager stuff."

    def setUp(self):
        artist = ArtistFactory()
        track = TrackFactory(artist=artist)
        album = AlbumFactory(artist=artist)

        # Scrobbled 4 times on different days, by 2 different Accounts:
        scrobble1 = ScrobbleFactory(artist=artist, track=track, album=album,
                            post_time=datetime_from_str('2015-08-11 12:00:00'))
        scrobble2 = ScrobbleFactory(artist=artist, track=track, album=album,
                            post_time=datetime_from_str('2015-08-12 12:00:00'))
        scrobble2 = ScrobbleFactory(artist=artist, track=track, album=album,
                            post_time=datetime_from_str('2015-08-13 12:00:00'))
        scrobble4 = ScrobbleFactory(artist=artist, track=track, album=album,
                            post_time=datetime_from_str('2015-08-14 12:00:00'))

    def test_scrobble_counts(self):
        "Should add a `scrobble_count` aggregate Count to each Album."
        # Add another album, with 1 scrobble, as well as the one in setUp():
        artist2 = ArtistFactory()
        track2 = TrackFactory(artist=artist2)
        album2 = AlbumFactory(artist=artist2)
        scrobble2 = ScrobbleFactory(artist=artist2, track=track2, album=album2)
        albums = Album.objects.with_scrobble_counts()
        self.assertEqual(len(albums), 2)
        self.assertEqual(albums[0].scrobble_count, 4)
        self.assertEqual(albums[1].scrobble_count, 1)

    def test_args_min(self):
        "Only aggregates scrobble_counts after supplied min time."
        albums = Album.objects.with_scrobble_counts(
                        min_post_time=datetime_from_str('2015-08-12 12:00:00'),
                    )
        self.assertEqual(len(albums), 1)
        self.assertEqual(albums[0].scrobble_count, 3)

    def test_args_max(self):
        "Only aggregates scrobble_counts before supplied max time."
        albums = Album.objects.with_scrobble_counts(
                        max_post_time=datetime_from_str('2015-08-13 12:00:00'),
                    )
        self.assertEqual(len(albums), 1)
        self.assertEqual(albums[0].scrobble_count, 3)

    def test_args_min_max(self):
        "Only aggregates scrobble_counts within supplied times."
        albums = Album.objects.with_scrobble_counts(
                        min_post_time=datetime_from_str('2015-08-12 12:00:00'),
                        max_post_time=datetime_from_str('2015-08-13 12:00:00')
                    )
        self.assertEqual(len(albums), 1)
        self.assertEqual(albums[0].scrobble_count, 2)

    def test_args_account(self):
        "Should only return Scrobbles by supplied Account"
        account = AccountFactory()
        album2 = AlbumFactory()
        scrobble2 = ScrobbleFactory(account=account, album=album2)
        albums = Album.objects.with_scrobble_counts(account=account)
        self.assertEqual(len(albums), 1)
        self.assertEqual(albums[0], album2)

    def test_args_track(self):
        "Should only return Scrobbles on Albums featuring supplied Track"
        album2 = AlbumFactory()
        track2 = TrackFactory()
        ScrobbleFactory(album=album2, track=track2)
        ScrobbleFactory(album=album2, track=track2)
        albums = Album.objects.with_scrobble_counts(track=track2)
        self.assertEqual(len(albums), 1)
        self.assertEqual(len(albums), 1)
        self.assertEqual(albums[0], album2)
        self.assertEqual(albums[0].scrobble_count, 2)

    def test_args_artist(self):
        "Should only return Scrobbles by supplied Artist"
        artist2 = ArtistFactory()
        track2 = TrackFactory(artist=artist2)
        album2 = AlbumFactory(artist=artist2)
        scrobble2 = ScrobbleFactory(artist=artist2, track=track2, album=album2)
        albums = Album.objects.with_scrobble_counts(artist=artist2)
        self.assertEqual(len(albums), 1)
        self.assertEqual(albums[0].artist, artist2)
        self.assertEqual(albums[0].scrobble_count, 1)

    def test_min_post_time_error(self):
        with self.assertRaises(TypeError):
            Album.objects.with_scrobble_counts(min_post_time='foo')

    def test_max_post_time_error(self):
        with self.assertRaises(TypeError):
            Album.objects.with_scrobble_counts(max_post_time='foo')

    def test_account_error(self):
        with self.assertRaises(TypeError):
            Album.objects.with_scrobble_counts(account='foo')

    def test_artist_error(self):
        with self.assertRaises(TypeError):
            Album.objects.with_scrobble_counts(artist='foo')

    def test_album_error(self):
        album = AlbumFactory()
        with self.assertRaises(ValueError):
            Album.objects.with_scrobble_counts(album=album)


class ArtistManagersWithScrobbleCountsTestCase(TestCase):
    "Testing the WithScrobbleCountsManager stuff."

    def setUp(self):
        self.artist = ArtistFactory()
        track = TrackFactory(artist=self.artist)

        # Scrobbled 4 times on different days:
        scrobble1 = ScrobbleFactory(artist=self.artist, track=track,
                            post_time=datetime_from_str('2015-08-11 12:00:00'))
        scrobble2 = ScrobbleFactory(artist=self.artist, track=track,
                            post_time=datetime_from_str('2015-08-12 12:00:00'))
        scrobble2 = ScrobbleFactory(artist=self.artist, track=track,
                            post_time=datetime_from_str('2015-08-13 12:00:00'))
        scrobble4 = ScrobbleFactory(artist=self.artist, track=track,
                            post_time=datetime_from_str('2015-08-14 12:00:00'))

    def test_scrobble_counts(self):
        "Should add a `scrobble_count` aggregate Count to each Artist."
        # Add another track, with 1 scrobble, as well as the one in setUp():
        artist2 = ArtistFactory()
        track2 = TrackFactory(artist=artist2)
        scrobble2 = ScrobbleFactory(artist=artist2, track=track2)
        artists = Artist.objects.with_scrobble_counts()
        self.assertEqual(len(artists), 2)
        self.assertEqual(artists[0].scrobble_count, 4)
        self.assertEqual(artists[1].scrobble_count, 1)

    def test_args_album(self):
        "Only aggregates scrobble_counts for a particular album."
        artist2 = ArtistFactory()
        album1 = AlbumFactory()
        album2 = AlbumFactory()
        track = TrackFactory()
        ScrobbleFactory(album=album1, artist=self.artist, track=track)
        ScrobbleFactory(album=album1, artist=self.artist, track=track)
        ScrobbleFactory(album=album1, artist=artist2, track=track)
        ScrobbleFactory(album=album2, artist=self.artist, track=track)
        artists = Artist.objects.with_scrobble_counts(album=album1)
        self.assertEqual(len(artists), 2)
        self.assertEqual(artists[0].scrobble_count, 2)
        self.assertEqual(artists[1].scrobble_count, 1)

    def test_args_min(self):
        "Only aggregates scrobble_counts after supplied min time."
        artists = Artist.objects.with_scrobble_counts(
                        min_post_time=datetime_from_str('2015-08-12 12:00:00'),
                    )
        self.assertEqual(len(artists), 1)
        self.assertEqual(artists[0].scrobble_count, 3)

    def test_args_max(self):
        "Only aggregates scrobble_counts before supplied max time."
        artists = Artist.objects.with_scrobble_counts(
                        max_post_time=datetime_from_str('2015-08-13 12:00:00'),
                    )
        self.assertEqual(len(artists), 1)
        self.assertEqual(artists[0].scrobble_count, 3)

    def test_args_min_max(self):
        "Only aggregates scrobble_counts within supplied times."
        artists = Artist.objects.with_scrobble_counts(
                        min_post_time=datetime_from_str('2015-08-12 12:00:00'),
                        max_post_time=datetime_from_str('2015-08-13 12:00:00')
                    )
        self.assertEqual(len(artists), 1)
        self.assertEqual(artists[0].scrobble_count, 2)

    def test_args_account(self):
        "Should only return Scrobbles by supplied Account"
        account = AccountFactory()
        scrobble2 = ScrobbleFactory(artist=self.artist, account=account)
        artists = Artist.objects.with_scrobble_counts(account=account)
        self.assertEqual(len(artists), 1)
        self.assertEqual(artists[0].scrobble_count, 1)

    def test_min_post_time_error(self):
        with self.assertRaises(TypeError):
            Artist.objects.with_scrobble_counts(min_post_time='foo')

    def test_max_post_time_error(self):
        with self.assertRaises(TypeError):
            Artist.objects.with_scrobble_counts(max_post_time='foo')

    def test_account_error(self):
        with self.assertRaises(TypeError):
            Artist.objects.with_scrobble_counts(account='foo')

    def test_artist_error(self):
        artist = ArtistFactory()
        with self.assertRaises(ValueError):
            Artist.objects.with_scrobble_counts(artist=artist)


class TrackManagersWithScrobbleCountsTestCase(TestCase):
    "Testing the WithScrobbleCountsManager stuff."

    def setUp(self):
        self.artist = ArtistFactory()
        self.track = TrackFactory(artist=self.artist)

        # Scrobbled 4 times on different days:
        scrobble1 = ScrobbleFactory(artist=self.artist, track=self.track,
                            post_time=datetime_from_str('2015-08-11 12:00:00'))
        scrobble2 = ScrobbleFactory(artist=self.artist, track=self.track,
                            post_time=datetime_from_str('2015-08-12 12:00:00'))
        scrobble2 = ScrobbleFactory(artist=self.artist, track=self.track,
                            post_time=datetime_from_str('2015-08-13 12:00:00'))
        scrobble4 = ScrobbleFactory(artist=self.artist, track=self.track,
                            post_time=datetime_from_str('2015-08-14 12:00:00'))

    def test_scrobble_counts(self):
        "Should add a `scrobble_count` aggregate Count to each Track."
        # Add another track, with 1 scrobble, as well as the one in setUp():
        artist2 = ArtistFactory()
        track2 = TrackFactory(artist=artist2)
        scrobble2 = ScrobbleFactory(artist=artist2, track=track2)
        tracks = Track.objects.with_scrobble_counts()
        self.assertEqual(len(tracks), 2)
        self.assertEqual(tracks[0].scrobble_count, 4)
        self.assertEqual(tracks[1].scrobble_count, 1)

    def test_args_album(self):
        "Only aggregates scrobble_counts in supplied album."
        album1 = AlbumFactory()
        album2 = AlbumFactory()
        track1 = TrackFactory()
        ScrobbleFactory.create_batch(2, album=album1, track=self.track)
        ScrobbleFactory.create_batch(1, album=album1, track=track1)
        ScrobbleFactory.create_batch(1, album=album2, track=self.track)
        tracks = Track.objects.with_scrobble_counts(album=album1)
        self.assertEqual(len(tracks), 2)
        self.assertEqual(tracks[0].scrobble_count, 2)
        self.assertEqual(tracks[0], self.track)
        self.assertEqual(tracks[1].scrobble_count, 1)
        self.assertEqual(tracks[1], track1)

    def test_args_min(self):
        "Only aggregates scrobble_counts after supplied min time."
        tracks = Track.objects.with_scrobble_counts(
                        min_post_time=datetime_from_str('2015-08-12 12:00:00'),
                    )
        self.assertEqual(len(tracks), 1)
        self.assertEqual(tracks[0].scrobble_count, 3)

    def test_args_max(self):
        "Only aggregates scrobble_counts before supplied max time."
        tracks = Track.objects.with_scrobble_counts(
                        max_post_time=datetime_from_str('2015-08-13 12:00:00'),
                    )
        self.assertEqual(len(tracks), 1)
        self.assertEqual(tracks[0].scrobble_count, 3)

    def test_args_min_max(self):
        "Only aggregates scrobble_counts within supplied times."
        tracks = Track.objects.with_scrobble_counts(
                        min_post_time=datetime_from_str('2015-08-12 12:00:00'),
                        max_post_time=datetime_from_str('2015-08-13 12:00:00')
                    )
        self.assertEqual(len(tracks), 1)
        self.assertEqual(tracks[0].scrobble_count, 2)

    def test_args_account(self):
        "Should only return Scrobbles by supplied Account"
        account = AccountFactory()
        scrobble2 = ScrobbleFactory(
                        account=account, track=self.track, artist=self.artist)
        tracks = Track.objects.with_scrobble_counts(account=account)
        self.assertEqual(len(tracks), 1)
        self.assertEqual(tracks[0], self.track)
        self.assertEqual(tracks[0].scrobble_count, 1)

    def test_args_artist(self):
        "Should only return Scrobbles by supplied Artist"
        artist2 = ArtistFactory()
        track2 = TrackFactory(artist=artist2)
        scrobble2 = ScrobbleFactory(artist=artist2, track=track2)
        tracks = Track.objects.with_scrobble_counts(artist=artist2)
        self.assertEqual(len(tracks), 1)
        self.assertEqual(tracks[0].artist, artist2)
        self.assertEqual(tracks[0].scrobble_count, 1)

    def test_min_post_time_error(self):
        with self.assertRaises(TypeError):
            Track.objects.with_scrobble_counts(min_post_time='foo')

    def test_max_post_time_error(self):
        with self.assertRaises(TypeError):
            Track.objects.with_scrobble_counts(max_post_time='foo')

    def test_account_error(self):
        with self.assertRaises(TypeError):
            Track.objects.with_scrobble_counts(account='foo')

    def test_artist_error(self):
        with self.assertRaises(TypeError):
            Track.objects.with_scrobble_counts(artist='foo')

    def test_track_error(self):
        track = TrackFactory()
        with self.assertRaises(ValueError):
            Track.objects.with_scrobble_counts(track=track)

