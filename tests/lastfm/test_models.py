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

    def test_has_credentisals(self):
        account = AccountFactory(api_key='1234')
        self.assertTrue(account.has_credentials())
        account = AccountFactory(api_key='')
        self.assertFalse(account.has_credentials())

    def test_permalink(self):
        account = AccountFactory(username='gyford')
        self.assertEqual(account.permalink, 'http://last.fm/user/gyford')

    def test_absolute_url(self):
        account = AccountFactory(username='gyford')
        self.assertEqual(account.get_absolute_url(), '/lastfm/gyford/')


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

    def test_url_mbid(self):
        mbid = '65497352-51ea-40a6-b1f0-1bdff6750369'
        album = AlbumFactory(mbid=mbid)
        self.assertEqual(album.get_absolute_url(),
                        '/lastfm/album/%s/' % mbid)

    def test_url_no_mbid(self):
        album = AlbumFactory(mbid='')
        self.assertEqual(album.get_absolute_url(),
                        '/lastfm/album/%s/' % album.id)

    def test_permalink(self):
        artist = ArtistFactory(name='Life Without Buildings')
        album = AlbumFactory(name='Any Other City', artist=artist)
        self.assertEqual(album.permalink,
                'http://last.fm/music/Life+Without+Buildings/Any+Other+City')

    def test_musicbrainz_url(self):
        album = AlbumFactory(mbid='65497352-51ea-40a6-b1f0-1bdff6750369')
        self.assertEqual(album.musicbrainz_url,
            'https://musicbrainz.org/release/65497352-51ea-40a6-b1f0-1bdff6750369')

    def test_musicbrainz_url_none(self):
        album = AlbumFactory(mbid='')
        self.assertIsNone(album.musicbrainz_url)


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

    def test_url_mbid(self):
        mbid = '80fe34d0-6b4f-4ccd-81c3-281ab37f0451'
        artist = ArtistFactory(mbid=mbid)
        self.assertEqual(artist.get_absolute_url(),
                        '/lastfm/artist/%s/' % mbid)

    def test_url_no_mbid(self):
        artist = ArtistFactory(mbid='')
        self.assertEqual(artist.get_absolute_url(),
                        '/lastfm/artist/%s/' % artist.id)

    def test_permalink(self):
        artist = ArtistFactory(name="Tom Waits")
        self.assertEqual(artist.permalink, 'http://last.fm/music/Tom+Waits')

    def test_permalink_2(self):
        artist = ArtistFactory(name="/ # ? [ ] ' + ; %")
        self.assertEqual(artist.permalink,
                'http://last.fm/music/%2F+%2316+%3F+%5B+%5D+%27+%252B+%3B+%25')

    def test_permalink_3(self):
        artist = ArtistFactory(name='" < > \ ^ ` { | }')
        self.assertEqual(artist.permalink,
                'http://last.fm/music/%22+%3C+%3E+%5C%5C+%5E+%60+%7B+%7C+%7D')

    def test_permalink_4(self):
        "Things which don't get quoted."
        artist = ArtistFactory(name=', . & ! ( )')
        self.assertEqual(artist.permalink, 'http://last.fm/music/,+.+&+!+(+)')

    def test_musicbrainz_url(self):
        artist = ArtistFactory(mbid='80fe34d0-6b4f-4ccd-81c3-281ab37f0451')
        self.assertEqual(artist.musicbrainz_url,
            'https://musicbrainz.org/artist/80fe34d0-6b4f-4ccd-81c3-281ab37f0451')

    def test_musicbrainz_url_none(self):
        artist = ArtistFactory(mbid='')
        self.assertIsNone(artist.musicbrainz_url)

    def test_get_top_albums(self):
        "Returns 10 albums, ordered by most-scrobbled first"
        artist = ArtistFactory()
        albums = AlbumFactory.create_batch(11, artist=artist)
        # NB, Tracks & Albums are only associated via Scrobbles, not directly:
        tracks = TrackFactory.create_batch(11, artist=artist)
        # Scrobble all 11 tracks+albums once...
        for idx, t in enumerate(tracks):
            ScrobbleFactory(artist=artist, track=t, album=albums[idx])
        # ... but scrobble one of them an additional time:
        ScrobbleFactory(artist=artist, track=tracks[3], album=albums[3])
        top_albums = artist.get_top_albums()
        self.assertEqual(len(top_albums), 10)
        self.assertEqual(top_albums[0], albums[3])

    def test_get_top_albums_limit(self):
        "Only returns the number of top albums requested"
        artist = ArtistFactory()
        albums = AlbumFactory.create_batch(4, artist=artist)
        tracks = TrackFactory.create_batch(4, artist=artist)
        for idx, t in enumerate(tracks):
            ScrobbleFactory(artist=artist, track=t, album=albums[idx])
        top_albums = artist.get_top_albums(num=3)
        self.assertEqual(len(top_albums), 3)

    def test_get_top_tracks(self):
        "Returns 10 tracks, ordered by most-scrobbled first"
        artist = ArtistFactory()
        tracks = TrackFactory.create_batch(11, artist=artist)
        # Scrobble all 11 tracks once...
        for t in tracks:
            ScrobbleFactory(artist=artist, track=t)
        # ... but scrobble one of them an additional time:
        ScrobbleFactory(artist=artist, track=tracks[3])
        top_tracks = artist.get_top_tracks()
        self.assertEqual(len(top_tracks), 10)
        self.assertEqual(top_tracks[0], tracks[3])

    def test_get_top_tracks_limit(self):
        "Only returns the number of top tracks requested"
        artist = ArtistFactory()
        tracks = TrackFactory.create_batch(4, artist=artist)
        for t in tracks:
            ScrobbleFactory(artist=artist, track=t)
        top_tracks = artist.get_top_tracks(num=3)
        self.assertEqual(len(top_tracks), 3)

class ScrobbleTestCase(TestCase):

    def test_str(self):
        post_time = datetime.datetime.strptime(
                        '2016-04-07 12:00:00', '%Y-%m-%d %H:%M:%S'
                    ).replace(tzinfo=pytz.utc)
        scrobble = ScrobbleFactory(artist_name='The Mountain Goats',
                                    track_name='Dance Music',
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
        scrobble = ScrobbleFactory(artist_name='The Mountain Goats',
                                    track_name='Dance Music')
        self.assertEqual(scrobble.title, 'The Mountain Goats – Dance Music')

    def test_summary(self):
        "It should set the summary on save."
        post_time = datetime.datetime.strptime(
                        '2016-04-07 12:00:00', '%Y-%m-%d %H:%M:%S'
                    ).replace(tzinfo=pytz.utc)
        scrobble = ScrobbleFactory(post_time=post_time)
        self.assertEqual(scrobble.summary, '2016-04-07 12:00:00+00:00')

    def test_url_album_with_mbid(self):
        mbid = '65497352-51ea-40a6-b1f0-1bdff6750369'
        album = AlbumFactory(mbid=mbid)
        scrobble = ScrobbleFactory(album=album, album_mbid=mbid)
        self.assertEqual(scrobble.get_absolute_url_album(),
                        '/lastfm/album/%s/' % mbid)

    def test_url_album_with_no_mbid(self):
        "Should use the Album's Django ID."
        album = AlbumFactory(mbid='')
        scrobble = ScrobbleFactory(album=album, album_mbid='')
        self.assertEqual(scrobble.get_absolute_url_album(),
                        '/lastfm/album/%s/' % album.id)

    def test_url_artist_with_mbid(self):
        mbid = '80fe34d0-6b4f-4ccd-81c3-281ab37f0451'
        artist = ArtistFactory(mbid=mbid)
        scrobble = ScrobbleFactory(artist=artist, artist_mbid=mbid)
        self.assertEqual(scrobble.get_absolute_url_artist(),
                        '/lastfm/artist/%s/' % mbid)

    def test_url_artist_with_no_mbid(self):
        "Should use the Artist's Django ID."
        artist = ArtistFactory(mbid='')
        scrobble = ScrobbleFactory(artist=artist, artist_mbid='')
        self.assertEqual(scrobble.get_absolute_url_artist(),
                        '/lastfm/artist/%s/' % artist.id)

    def test_url_track_with_mbid(self):
        mbid = '330fd2ed-785e-473a-bd9b-ab0b109029c8'
        track = TrackFactory(mbid=mbid)
        scrobble = ScrobbleFactory(track=track, track_mbid=mbid)
        self.assertEqual(scrobble.get_absolute_url_track(),
                        '/lastfm/track/%s/' % mbid)

    def test_url_track_with_no_mbid(self):
        "Should use the Track's Django ID."
        track = TrackFactory(mbid='')
        scrobble = ScrobbleFactory(track=track, track_mbid='')
        self.assertEqual(scrobble.get_absolute_url_track(),
                        '/lastfm/track/%s/' % track.id)


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

    def test_url_mbid(self):
        mbid = '330fd2ed-785e-473a-bd9b-ab0b109029c8'
        track = TrackFactory(mbid=mbid)
        self.assertEqual(track.get_absolute_url(),
                        '/lastfm/track/%s/' % mbid)

    def test_url_no_mbid(self):
        track = TrackFactory(mbid='')
        self.assertEqual(track.get_absolute_url(),
                        '/lastfm/track/%s/' % track.id)

    def test_permalink(self):
        artist = ArtistFactory(name='Death Cab for Cutie')
        track = TrackFactory(name='A Lack of Color', artist=artist)
        self.assertEqual(track.permalink,
                'http://last.fm/music/Death+Cab+for+Cutie/_/A+Lack+of+Color')

    def test_musicbrainz_url(self):
        track = TrackFactory(mbid='330fd2ed-785e-473a-bd9b-ab0b109029c8')
        self.assertEqual(track.musicbrainz_url,
            'https://musicbrainz.org/recording/330fd2ed-785e-473a-bd9b-ab0b109029c8')

    def test_musicbrainz_url_none(self):
        track = TrackFactory(mbid='')
        self.assertIsNone(track.musicbrainz_url)

