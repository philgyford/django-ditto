import datetime
import pytz

from django.test import TestCase

from ditto.lastfm.factories import AccountFactory, AlbumFactory,\
        ArtistFactory, ScrobbleFactory, TrackFactory
from ditto.lastfm.models import Account, Album, Artist, Scrobble, Track


class AccountTestCase(TestCase):

    def test_str(self):
        account = AccountFactory(username='gyford')
        self.assertEqual(str(account), 'gyford')

    def test_ordering(self):
        account_1 = AccountFactory(username='bb', realname='Alan')
        account_2 = AccountFactory(username='aa', realname='Zak')
        accounts = Account.objects.all()
        self.assertEqual(accounts[0], account_2)
        self.assertEqual(accounts[1], account_1)

    def test_has_credentials(self):
        account = AccountFactory(api_key='1234')
        self.assertTrue(account.has_credentials())
        account = AccountFactory(api_key='')
        self.assertFalse(account.has_credentials())

    def test_permalink(self):
        account = AccountFactory(username='gyford')
        self.assertEqual(account.permalink, 'http://last.fm/user/gyford')

    def test_absolute_url(self):
        account = AccountFactory(username='gyford')
        self.assertEqual(account.get_absolute_url(), '/lastfm/user/gyford/')

    def test_recent_scrobbles(self):
        "By default it returns 10 scrobbles"
        account = AccountFactory()
        scrobbles = ScrobbleFactory.create_batch(11, account=account)
        self.assertEqual(len(account.get_recent_scrobbles()), 10)

    def test_recent_scrobbles_limit(self):
        "It returns `limit` scrobbles"
        account = AccountFactory()
        scrobbles = ScrobbleFactory.create_batch(5, account=account)
        self.assertEqual(len(account.get_recent_scrobbles(limit=3)), 3)

    def test_recent_scrobbles_order(self):
        "It returns the most recent first"
        account = AccountFactory()
        post_time_1 = datetime.datetime.strptime(
                '2015-08-11 12:00:00', '%Y-%m-%d %H:%M:%S').replace(
                                                            tzinfo=pytz.utc)
        post_time_2 = datetime.datetime.strptime(
                '2015-08-12 12:00:00', '%Y-%m-%d %H:%M:%S').replace(
                                                            tzinfo=pytz.utc)
        scrobble1 = ScrobbleFactory(account=account, post_time=post_time_1)
        scrobble2 = ScrobbleFactory(account=account, post_time=post_time_2)
        self.assertEqual(account.get_recent_scrobbles()[0], scrobble2)

    def test_recent_scrobbles_correct_account(self):
        "It only returns scrobbles for itself, not another account"
        account1 = AccountFactory()
        account2 = AccountFactory()
        scrobble1 = ScrobbleFactory(account=account1)
        scrobble2 = ScrobbleFactory(account=account2)
        scrobbles = account1.get_recent_scrobbles()
        self.assertEqual(len(scrobbles), 1)
        self.assertEqual(scrobbles[0], scrobble1)


class AlbumTestCase(TestCase):

    def test_str(self):
        album = AlbumFactory(name='Tallahassee')
        self.assertEqual(str(album), 'Tallahassee')

    def test_ordering(self):
        album_1 = AlbumFactory(name='We Shall All Be Healed')
        album_2 = AlbumFactory(name='All Hail West Texas')
        albums = Album.objects.all()
        self.assertEqual(albums[0], album_2)
        self.assertEqual(albums[1], album_1)

    def test_absolute_url(self):
        artist = ArtistFactory(slug='Life+Without+Buildings')
        album = AlbumFactory(artist=artist, slug='Any+Other+City')
        self.assertEqual(album.get_absolute_url(),
                        '/lastfm/music/Life+Without+Buildings/Any+Other+City/')

    def test_permalink(self):
        artist = ArtistFactory(slug='Life+Without+Buildings')
        album = AlbumFactory(artist=artist, slug='Any+Other+City')
        self.assertEqual(album.permalink,
                'http://last.fm/music/Life+Without+Buildings/Any+Other+City')

    def test_musicbrainz_url(self):
        album = AlbumFactory(mbid='65497352-51ea-40a6-b1f0-1bdff6750369')
        self.assertEqual(album.musicbrainz_url,
            'https://musicbrainz.org/release/65497352-51ea-40a6-b1f0-1bdff6750369')

    def test_musicbrainz_url_none(self):
        album = AlbumFactory(mbid='')
        self.assertIsNone(album.musicbrainz_url)

    def test_tracks(self):
        artist = ArtistFactory()
        track1 = TrackFactory(artist=artist)
        track2 = TrackFactory(artist=artist)
        album = AlbumFactory(artist=artist)
        # Scrobble track1 once, track2 twice:
        ScrobbleFactory(artist=artist, track=track1, album=album)
        ScrobbleFactory(artist=artist, track=track2, album=album)
        ScrobbleFactory(artist=artist, track=track2, album=album)

        tracks = album.tracks
        self.assertEqual(len(tracks), 2)
        self.assertEqual(tracks[0], track2)
        self.assertEqual(tracks[1], track1)
        self.assertEqual(tracks[0].scrobble_count, 2)
        self.assertEqual(tracks[1].scrobble_count, 1)

    def test_get_scrobble_count(self):
        artist = ArtistFactory()
        track = TrackFactory(artist=artist)
        album = AlbumFactory(artist=artist)
        # Scrobbled 2 times:
        ScrobbleFactory.create_batch(2, artist=artist, track=track, album=album)
        # And another Scrobble with different artist/track:
        ScrobbleFactory()
        self.assertEqual(album.get_scrobble_count(), 2)

    def test_get_most_recent_scrobble(self):
        artist = ArtistFactory()
        track = TrackFactory(artist=artist)
        album = AlbumFactory(artist=artist)
        post_time_1 = datetime.datetime.strptime(
                '2015-08-11 12:00:00', '%Y-%m-%d %H:%M:%S').replace(
                                                            tzinfo=pytz.utc)
        post_time_2 = datetime.datetime.strptime(
                '2015-08-12 12:00:00', '%Y-%m-%d %H:%M:%S').replace(
                                                            tzinfo=pytz.utc)
        scrobble1 = ScrobbleFactory(artist=artist, track=track, album=album,
                                                        post_time=post_time_1)
        scrobble2 = ScrobbleFactory(artist=artist, track=track, album=album,
                                                        post_time=post_time_2)
        self.assertEqual(album.get_most_recent_scrobble(), scrobble2)


class ArtistTestCase(TestCase):

    def test_str(self):
        artist = ArtistFactory(name='The Mountain Goats')
        self.assertEqual(str(artist), 'The Mountain Goats')

    def test_ordering(self):
        artist_1 = ArtistFactory(name='Robyn')
        artist_2 = ArtistFactory(name='Art Brut')
        artists = Artist.objects.all()
        self.assertEqual(artists[0], artist_2)
        self.assertEqual(artists[1], artist_1)

    def test_absolute_url(self):
        mbid = '80fe34d0-6b4f-4ccd-81c3-281ab37f0451'
        artist = ArtistFactory(slug='Tom+Waits')
        self.assertEqual(artist.get_absolute_url(), '/lastfm/music/Tom+Waits/')

    def test_permalink(self):
        artist = ArtistFactory(slug="Tom+Waits")
        self.assertEqual(artist.permalink, 'http://last.fm/music/Tom+Waits')

    def test_musicbrainz_url(self):
        artist = ArtistFactory(mbid='80fe34d0-6b4f-4ccd-81c3-281ab37f0451')
        self.assertEqual(artist.musicbrainz_url,
            'https://musicbrainz.org/artist/80fe34d0-6b4f-4ccd-81c3-281ab37f0451')

    def test_musicbrainz_url_none(self):
        artist = ArtistFactory(mbid='')
        self.assertIsNone(artist.musicbrainz_url)

    def test_get_top_albums(self):
        "Returns all albums, ordered by most-scrobbled first"
        artist = ArtistFactory()
        albums = AlbumFactory.create_batch(3, artist=artist)
        # NB, Tracks & Albums are only associated via Scrobbles, not directly:
        tracks = TrackFactory.create_batch(3, artist=artist)
        # Scrobble all tracks+albums once...
        for idx, t in enumerate(tracks):
            ScrobbleFactory(artist=artist, track=t, album=albums[idx])
        # ... but scrobble one of them an additional time:
        ScrobbleFactory(artist=artist, track=tracks[1], album=albums[1])
        top_albums = artist.get_top_albums()
        self.assertEqual(len(top_albums), 3)
        self.assertEqual(top_albums[0], albums[1])

    def test_get_top_albums_limit(self):
        "Only returns the number of top albums requested"
        artist = ArtistFactory()
        albums = AlbumFactory.create_batch(4, artist=artist)
        tracks = TrackFactory.create_batch(4, artist=artist)
        for idx, t in enumerate(tracks):
            ScrobbleFactory(artist=artist, track=t, album=albums[idx])
        top_albums = artist.get_top_albums(limit=3)
        self.assertEqual(len(top_albums), 3)

    def test_get_top_tracks(self):
        "Returns all tracks, ordered by most-scrobbled first"
        artist = ArtistFactory()
        tracks = TrackFactory.create_batch(3, artist=artist)
        # Scrobble all tracks once...
        for t in tracks:
            ScrobbleFactory(artist=artist, track=t)
        # ... but scrobble one of them an additional time:
        ScrobbleFactory(artist=artist, track=tracks[1])
        top_tracks = artist.get_top_tracks()
        self.assertEqual(len(top_tracks), 3)
        self.assertEqual(top_tracks[0], tracks[1])

    def test_get_top_tracks_limit(self):
        "Only returns the number of top tracks requested"
        artist = ArtistFactory()
        tracks = TrackFactory.create_batch(4, artist=artist)
        for t in tracks:
            ScrobbleFactory(artist=artist, track=t)
        top_tracks = artist.get_top_tracks(limit=3)
        self.assertEqual(len(top_tracks), 3)

    def test_get_scrobble_count(self):
        artist = ArtistFactory()
        scrobbles = ScrobbleFactory.create_batch(3, artist=artist)
        self.assertEqual(artist.get_scrobble_count(), 3)

    def test_get_most_recent_scrobble(self):
        artist = ArtistFactory()
        post_time_1 = datetime.datetime.strptime(
                '2015-08-11 12:00:00', '%Y-%m-%d %H:%M:%S').replace(
                                                            tzinfo=pytz.utc)
        post_time_2 = datetime.datetime.strptime(
                '2015-08-12 12:00:00', '%Y-%m-%d %H:%M:%S').replace(
                                                            tzinfo=pytz.utc)
        scrobble1 = ScrobbleFactory(artist=artist, post_time=post_time_1)
        scrobble2 = ScrobbleFactory(artist=artist, post_time=post_time_2)
        self.assertEqual(artist.get_most_recent_scrobble(), scrobble2)


class ScrobbleTestCase(TestCase):

    def setUp(self):
        self.artist = ArtistFactory(name='The Mountain Goats')
        self.track = TrackFactory(name='Dance Music', artist=self.artist)


    def test_str(self):
        post_time = datetime.datetime.strptime(
                        '2016-04-07 12:00:00', '%Y-%m-%d %H:%M:%S'
                    ).replace(tzinfo=pytz.utc)
        scrobble = ScrobbleFactory(artist=self.artist,
                                   track=self.track,
                                   post_time=post_time)
        self.assertEqual(str(scrobble),
                'The Mountain Goats – Dance Music (2016-04-07 12:00:00+00:00)')

    def test_ordering(self):
        "It should order by post_time descending."
        post_time_1 = datetime.datetime.strptime(
                        '2016-04-06 12:00:00', '%Y-%m-%d %H:%M:%S'
                    ).replace(tzinfo=pytz.utc)
        post_time_2 = datetime.datetime.strptime(
                        '2016-04-07 12:00:00', '%Y-%m-%d %H:%M:%S'
                    ).replace(tzinfo=pytz.utc)
        scrobble_1 = ScrobbleFactory(post_time=post_time_1)
        scrobble_2 = ScrobbleFactory(post_time=post_time_2)
        scrobbles = Scrobble.objects.all()
        self.assertEqual(scrobbles[0], scrobble_2)
        self.assertEqual(scrobbles[1], scrobble_1)

    def test_title(self):
        "It should set the title on save."
        scrobble = ScrobbleFactory(artist=self.artist, track=self.track)
        self.assertEqual(scrobble.title, 'The Mountain Goats – Dance Music')

    def test_summary(self):
        "It should set the summary on save."
        post_time = datetime.datetime.strptime(
                        '2016-04-07 12:00:00', '%Y-%m-%d %H:%M:%S'
                    ).replace(tzinfo=pytz.utc)
        scrobble = ScrobbleFactory(post_time=post_time)
        self.assertEqual(scrobble.summary, '2016-04-07 12:00:00+00:00')


class TrackTestCase(TestCase):

    def test_str(self):
        track = TrackFactory(name='Dance Music')
        self.assertEqual(str(track), 'Dance Music')

    def test_ordering(self):
        track_1 = TrackFactory(name='This Year')
        track_2 = TrackFactory(name='Dance Music')
        tracks = Track.objects.all()
        self.assertEqual(tracks[0], track_2)
        self.assertEqual(tracks[1], track_1)

    def test_absolute_url(self):
        artist = ArtistFactory(slug='The+Mountain+Goats')
        track = TrackFactory(slug='Dance+Music', artist=artist)
        self.assertEqual(track.get_absolute_url(),
                        '/lastfm/music/The+Mountain+Goats/_/Dance+Music/')

    def test_permalink(self):
        artist = ArtistFactory(slug='The+Mountain+Goats')
        track = TrackFactory(slug='Dance+Music', artist=artist)
        self.assertEqual(track.permalink,
                    'http://last.fm/music/The+Mountain+Goats/_/Dance+Music')

    def test_musicbrainz_url(self):
        track = TrackFactory(mbid='330fd2ed-785e-473a-bd9b-ab0b109029c8')
        self.assertEqual(track.musicbrainz_url,
            'https://musicbrainz.org/recording/330fd2ed-785e-473a-bd9b-ab0b109029c8')

    def test_musicbrainz_url_none(self):
        track = TrackFactory(mbid='')
        self.assertIsNone(track.musicbrainz_url)

    def test_albums(self):
        artist = ArtistFactory()
        track = TrackFactory(artist=artist)
        album1 = AlbumFactory(artist=artist)
        album2 = AlbumFactory(artist=artist)
        # Scrobble album1 once, album2 twice:
        ScrobbleFactory(artist=artist, track=track, album=album1)
        ScrobbleFactory(artist=artist, track=track, album=album2)
        ScrobbleFactory(artist=artist, track=track, album=album2)

        albums = track.albums
        self.assertEqual(len(albums), 2)
        self.assertEqual(albums[0], album2)
        self.assertEqual(albums[1], album1)
        self.assertEqual(albums[0].scrobble_count, 2)
        self.assertEqual(albums[1].scrobble_count, 1)

    def test_get_scrobble_count(self):
        artist = ArtistFactory()
        track = TrackFactory(artist=artist)
        # Scrobbled 2 times:
        ScrobbleFactory.create_batch(2, artist=artist, track=track)
        # And another Scrobble with different artist/track:
        ScrobbleFactory()
        self.assertEqual(track.get_scrobble_count(), 2)

    def test_get_most_recent_scrobble(self):
        artist = ArtistFactory()
        track = TrackFactory(artist=artist)
        post_time_1 = datetime.datetime.strptime(
                '2015-08-11 12:00:00', '%Y-%m-%d %H:%M:%S').replace(
                                                            tzinfo=pytz.utc)
        post_time_2 = datetime.datetime.strptime(
                '2015-08-12 12:00:00', '%Y-%m-%d %H:%M:%S').replace(
                                                            tzinfo=pytz.utc)
        scrobble1 = ScrobbleFactory(
                        artist=artist, track=track, post_time=post_time_1)
        scrobble2 = ScrobbleFactory(
                        artist=artist, track=track, post_time=post_time_2)
        self.assertEqual(track.get_most_recent_scrobble(), scrobble2)

