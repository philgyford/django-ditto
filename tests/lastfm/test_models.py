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
        self.assertEqual(account.permalink,
                        'http://www.last.fm/user/gyford')


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


