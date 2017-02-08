from django.core.urlresolvers import reverse
from django.test import TestCase

from freezegun import freeze_time

from ditto.core.utils import datetime_from_str
from ditto.lastfm.factories import AccountFactory, AlbumFactory,\
        ArtistFactory, ScrobbleFactory, TrackFactory

from ditto.lastfm.models import *

class AlbumDetailViewTests(TestCase):

    def setUp(self):
        self.artist = ArtistFactory(slug='Lou+Reed')
        self.album = AlbumFactory(slug='New+York', artist=self.artist)

    def test_templates(self):
        "Uses the correct templates"
        response = self.client.get(reverse('lastfm:album_detail',
                                    kwargs={'artist_slug': self.artist.slug,
                                            'album_slug': self.album.slug,}))
        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, 'lastfm/album_detail.html')
        self.assertTemplateUsed(response, 'lastfm/base.html')
        self.assertTemplateUsed(response, 'ditto/base.html')

    def test_context(self):
        "Sends the correct data to the templates"
        response = self.client.get(reverse('lastfm:album_detail',
                                    kwargs={'artist_slug': self.artist.slug,
                                            'album_slug': self.album.slug,}))
        self.assertIn('album', response.context)
        self.assertEqual(self.album.pk, response.context['album'].pk)

    def test_404s(self):
        "Responds with 404 if we request an album that doesn't exist."
        response = self.client.get(reverse('lastfm:album_detail',
                                    kwargs={'artist_slug': self.artist.slug,
                                            'album_slug': 'Transformer',}))
        self.assertEquals(response.status_code, 404)


class AlbumListViewTests(TestCase):

    def test_templates(self):
        "Uses the correct templates"
        response = self.client.get(reverse('lastfm:album_list'))
        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, 'lastfm/album_list.html')
        self.assertTemplateUsed(response, 'lastfm/base.html')
        self.assertTemplateUsed(response, 'ditto/base.html')

    def test_context(self):
        "Sends the correct data to the templates"
        accounts = AccountFactory.create_batch(2)
        albums = AlbumFactory.create_batch(3)
        response = self.client.get(reverse('lastfm:album_list'))
        self.assertIn('account_list', response.context)
        self.assertEqual(len(response.context['account_list']), 2)
        self.assertIn('album_list', response.context)
        self.assertEqual(len(response.context['album_list']), 3)
        self.assertIn('valid_days', response.context)
        self.assertEqual(response.context['valid_days'],
                        ['7', '30', '90', '180', '365', 'all',])
        self.assertIn('current_days', response.context)
        self.assertEqual(response.context['current_days'], 'all')

    @freeze_time("2016-10-05 12:00:00", tz_offset=-8)
    def test_default_days(self):
        "Has correct scrobble count context when all days are viewed, the default."
        artist = ArtistFactory()
        album = AlbumFactory(artist=artist)
        scrobble1 = ScrobbleFactory(artist=artist, album=album,
                            post_time=datetime_from_str('2012-10-01 12:00:00'))
        scrobble2 = ScrobbleFactory(artist=artist, album=album,
                            post_time=datetime_from_str('2016-10-01 12:00:00'))
        response = self.client.get(reverse('lastfm:album_list'))
        self.assertEqual(response.context['album_list'][0].scrobble_count, 2)

    @freeze_time("2016-10-05 12:00:00", tz_offset=-8)
    def test_all_days(self):
        "Has correct scrobble count context when all days are viewed."
        artist = ArtistFactory()
        album = AlbumFactory(artist=artist)
        scrobble1 = ScrobbleFactory(artist=artist, album=album,
                            post_time=datetime_from_str('2012-10-01 12:00:00'))
        scrobble2 = ScrobbleFactory(artist=artist, album=album,
                            post_time=datetime_from_str('2016-10-01 12:00:00'))
        response = self.client.get("%s?days=all" % reverse('lastfm:album_list'))
        self.assertEqual(response.context['album_list'][0].scrobble_count, 2)

    @freeze_time("2016-10-05 12:00:00", tz_offset=-8)
    def test_7_days(self):
        "Has correct scrobble count context when a restricted number of days are viewed."
        artist = ArtistFactory()
        album = AlbumFactory(artist=artist)
        scrobble1 = ScrobbleFactory(artist=artist, album=album,
                            post_time=datetime_from_str('2012-10-01 12:00:00'))
        scrobble2 = ScrobbleFactory(artist=artist, album=album,
                            post_time=datetime_from_str('2016-10-01 12:00:00'))
        response = self.client.get("%s?days=7" % reverse('lastfm:album_list'))
        self.assertEqual(response.context['album_list'][0].scrobble_count, 1)


class ArtistAlbumsViewTests(TestCase):

    def setUp(self):
        self.artist = ArtistFactory(slug='Lou+Reed')

    def test_templates(self):
        "Uses the correct templates"
        response = self.client.get(reverse('lastfm:artist_albums',
                                    kwargs={'artist_slug': self.artist.slug,}))
        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, 'lastfm/artist_albums.html')
        self.assertTemplateUsed(response, 'lastfm/base.html')
        self.assertTemplateUsed(response, 'ditto/base.html')

    def test_context(self):
        "Sends the correct data to the templates"
        response = self.client.get(reverse('lastfm:artist_albums',
                                    kwargs={'artist_slug': self.artist.slug,}))
        self.assertIn('artist', response.context)
        self.assertEqual(self.artist.pk, response.context['artist'].pk)

    def test_404s(self):
        "Responds with 404 if we request an artist that doesn't exist."
        response = self.client.get(reverse('lastfm:artist_albums',
                                    kwargs={'artist_slug': 'Looper',}))
        self.assertEquals(response.status_code, 404)


class ArtistDetailViewTests(TestCase):

    def setUp(self):
        self.artist = ArtistFactory(slug='Lou+Reed')

    def test_templates(self):
        "Uses the correct templates"
        response = self.client.get(reverse('lastfm:artist_detail',
                                    kwargs={'artist_slug': self.artist.slug,}))
        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, 'lastfm/artist_detail.html')
        self.assertTemplateUsed(response, 'lastfm/base.html')
        self.assertTemplateUsed(response, 'ditto/base.html')

    def test_context(self):
        "Sends the correct data to the templates"
        response = self.client.get(reverse('lastfm:artist_detail',
                                    kwargs={'artist_slug': self.artist.slug,}))
        self.assertIn('artist', response.context)
        self.assertEqual(self.artist.pk, response.context['artist'].pk)

    def test_404s(self):
        "Responds with 404 if we request an artist that doesn't exist."
        response = self.client.get(reverse('lastfm:artist_detail',
                                    kwargs={'artist_slug': 'Looper',}))
        self.assertEquals(response.status_code, 404)


class ArtistListViewTests(TestCase):

    def test_templates(self):
        "Uses the correct templates"
        response = self.client.get(reverse('lastfm:artist_list'))
        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, 'lastfm/artist_list.html')
        self.assertTemplateUsed(response, 'lastfm/base.html')
        self.assertTemplateUsed(response, 'ditto/base.html')

    def test_context(self):
        "Sends the correct data to the templates"
        accounts = AccountFactory.create_batch(2)
        artists = ArtistFactory.create_batch(3)
        response = self.client.get(reverse('lastfm:artist_list'))
        self.assertIn('account_list', response.context)
        self.assertEqual(len(response.context['account_list']), 2)
        self.assertIn('artist_list', response.context)
        self.assertEqual(len(response.context['artist_list']), 3)
        self.assertIn('valid_days', response.context)
        self.assertEqual(response.context['valid_days'],
                        ['7', '30', '90', '180', '365', 'all',])
        self.assertIn('current_days', response.context)
        self.assertEqual(response.context['current_days'], 'all')

    @freeze_time("2016-10-05 12:00:00", tz_offset=-8)
    def test_default_days(self):
        "Has correct scrobble count context when all days are viewed, the default."
        artist = ArtistFactory()
        track = TrackFactory(artist=artist)
        scrobble1 = ScrobbleFactory(artist=artist, track=track,
                            post_time=datetime_from_str('2012-10-01 12:00:00'))
        scrobble2 = ScrobbleFactory(artist=artist, track=track,
                            post_time=datetime_from_str('2016-10-01 12:00:00'))
        response = self.client.get(reverse('lastfm:artist_list'))
        self.assertEqual(response.context['artist_list'][0].scrobble_count, 2)

    @freeze_time("2016-10-05 12:00:00", tz_offset=-8)
    def test_all_days(self):
        "Has correct scrobble count context when all days are viewed."
        artist = ArtistFactory()
        track = TrackFactory(artist=artist)
        scrobble1 = ScrobbleFactory(artist=artist, track=track,
                            post_time=datetime_from_str('2012-10-01 12:00:00'))
        scrobble2 = ScrobbleFactory(artist=artist, track=track,
                            post_time=datetime_from_str('2016-10-01 12:00:00'))
        response = self.client.get(
                                "%s?days=all" % reverse('lastfm:artist_list'))
        self.assertEqual(response.context['artist_list'][0].scrobble_count, 2)

    @freeze_time("2016-10-05 12:00:00", tz_offset=-8)
    def test_7_days(self):
        "Has correct scrobble count context when a restricted number of days are viewed."
        artist = ArtistFactory()
        track = TrackFactory(artist=artist)
        scrobble1 = ScrobbleFactory(artist=artist, track=track,
                            post_time=datetime_from_str('2012-10-01 12:00:00'))
        scrobble2 = ScrobbleFactory(artist=artist, track=track,
                            post_time=datetime_from_str('2016-10-01 12:00:00'))
        response = self.client.get("%s?days=7" % reverse('lastfm:artist_list'))
        self.assertEqual(response.context['artist_list'][0].scrobble_count, 1)


class HomeViewTests(TestCase):

    def test_templates(self):
        "Uses the correct templates"
        response = self.client.get(reverse('lastfm:home'))
        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, 'lastfm/home.html')
        self.assertTemplateUsed(response, 'lastfm/base.html')
        self.assertTemplateUsed(response, 'ditto/base.html')

    def test_context(self):
        "Sends the correct data to the templates"
        accounts = AccountFactory.create_batch(3)
        scrobble1 = ScrobbleFactory(account=accounts[0])
        scrobble2 = ScrobbleFactory(account=accounts[1])
        response = self.client.get(reverse('lastfm:home'))
        self.assertIn('account_list', response.context)
        self.assertEqual(len(response.context['account_list']), 3)
        self.assertIn('counts', response.context)
        self.assertIn('scrobbles', response.context['counts'])
        self.assertEqual(response.context['counts']['scrobbles'], 2)


class ScrobbleListViewTests(TestCase):

    def test_templates(self):
        "Uses the correct templates"
        response = self.client.get(reverse('lastfm:scrobble_list'))
        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, 'lastfm/scrobble_list.html')
        self.assertTemplateUsed(response, 'lastfm/base.html')
        self.assertTemplateUsed(response, 'ditto/base.html')

    def test_context(self):
        "Sends the correct data to the templates"
        accounts = AccountFactory.create_batch(3)
        response = self.client.get(reverse('lastfm:scrobble_list'))
        self.assertIn('account_list', response.context)
        self.assertEqual(len(response.context['account_list']), 3)
        self.assertIn('scrobble_list', response.context)


class TrackDetailViewTests(TestCase):

    def setUp(self):
        self.artist = ArtistFactory(slug='Lou+Reed')
        self.track = TrackFactory(slug='Hold+On', artist=self.artist)

    def test_templates(self):
        "Uses the correct templates"
        response = self.client.get(reverse('lastfm:track_detail',
                                    kwargs={'artist_slug': self.artist.slug,
                                            'track_slug': self.track.slug,}))
        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, 'lastfm/track_detail.html')
        self.assertTemplateUsed(response, 'lastfm/base.html')
        self.assertTemplateUsed(response, 'ditto/base.html')

    def test_context(self):
        "Sends the correct data to the templates"
        response = self.client.get(reverse('lastfm:track_detail',
                                    kwargs={'artist_slug': self.artist.slug,
                                            'track_slug': self.track.slug,}))
        self.assertIn('track', response.context)
        self.assertEqual(self.track.pk, response.context['track'].pk)

    def test_404s(self):
        "Responds with 404 if we request a track that doesn't exist."
        response = self.client.get(reverse('lastfm:track_detail',
                                    kwargs={'artist_slug': self.artist.slug,
                                            'track_slug': 'Viscious',}))
        self.assertEquals(response.status_code, 404)


class TrackListViewTests(TestCase):

    def test_templates(self):
        "Uses the correct templates"
        response = self.client.get(reverse('lastfm:track_list'))
        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, 'lastfm/track_list.html')
        self.assertTemplateUsed(response, 'lastfm/base.html')
        self.assertTemplateUsed(response, 'ditto/base.html')

    def test_context(self):
        "Sends the correct data to the templates"
        accounts = AccountFactory.create_batch(2)
        tracks = TrackFactory.create_batch(3)
        response = self.client.get(reverse('lastfm:track_list'))
        self.assertIn('account_list', response.context)
        self.assertEqual(len(response.context['account_list']), 2)
        self.assertIn('track_list', response.context)
        self.assertEqual(len(response.context['track_list']), 3)
        self.assertIn('valid_days', response.context)
        self.assertEqual(response.context['valid_days'],
                        ['7', '30', '90', '180', '365', 'all',])
        self.assertIn('current_days', response.context)
        self.assertEqual(response.context['current_days'], 'all')

    @freeze_time("2016-10-05 12:00:00", tz_offset=-8)
    def test_default_days(self):
        "Has correct scrobble count context when all days are viewed, the default."
        artist = ArtistFactory()
        track = TrackFactory(artist=artist)
        scrobble1 = ScrobbleFactory(artist=artist, track=track,
                            post_time=datetime_from_str('2012-10-01 12:00:00'))
        scrobble2 = ScrobbleFactory(artist=artist, track=track,
                            post_time=datetime_from_str('2016-10-01 12:00:00'))
        response = self.client.get(reverse('lastfm:track_list'))
        self.assertEqual(response.context['track_list'][0].scrobble_count, 2)

    @freeze_time("2016-10-05 12:00:00", tz_offset=-8)
    def test_all_days(self):
        "Has correct scrobble count context when all days are viewed."
        artist = ArtistFactory()
        track = TrackFactory(artist=artist)
        scrobble1 = ScrobbleFactory(artist=artist, track=track,
                            post_time=datetime_from_str('2012-10-01 12:00:00'))
        scrobble2 = ScrobbleFactory(artist=artist, track=track,
                            post_time=datetime_from_str('2016-10-01 12:00:00'))
        response = self.client.get(
                                "%s?days=all" % reverse('lastfm:track_list'))
        self.assertEqual(response.context['track_list'][0].scrobble_count, 2)

    @freeze_time("2016-10-05 12:00:00", tz_offset=-8)
    def test_7_days(self):
        "Has correct scrobble count context when a restricted number of days are viewed."
        artist = ArtistFactory()
        track = TrackFactory(artist=artist)
        scrobble1 = ScrobbleFactory(artist=artist, track=track,
                            post_time=datetime_from_str('2012-10-01 12:00:00'))
        scrobble2 = ScrobbleFactory(artist=artist, track=track,
                            post_time=datetime_from_str('2016-10-01 12:00:00'))
        response = self.client.get("%s?days=7" % reverse('lastfm:track_list'))
        self.assertEqual(response.context['track_list'][0].scrobble_count, 1)


class UserCommonTests(object):
    """Parent for all user-specific views.
    Doesn't inherit from TestCase because we don't want the tests in this class
    to run, only in its child classes.

    Child classes should inherit like:

        class MyChildTestCase(UserCommonTests, TestCase):

    in that order, so that setUp() runs.
    """

    # eg, 'user_album_list':
    view_name = 'DEFINE IN CHILD CLASSES'

    def setUp(self):
        bob = AccountFactory(username='bob')
        terry = AccountFactory(username='terry')

        self.artist1 = ArtistFactory()
        self.track1 = TrackFactory(artist=self.artist1)
        self.album1 = AlbumFactory(artist=self.artist1)

        self.artist2 = ArtistFactory()
        self.track2 = TrackFactory(artist=self.artist2)

        bobs1 = ScrobbleFactory.create_batch(2, account=bob,
                    track=self.track1, artist=self.artist1, album=self.album1)
        bobs2 = ScrobbleFactory.create_batch(5, account=bob,
                    track=self.track2, artist=self.artist2)

        terrys1 = ScrobbleFactory.create_batch(3, account=terry,
                    track=self.track1, artist=self.artist1, album=self.album1)
        terrys2 = ScrobbleFactory.create_batch(7, account=terry,
                    track=self.track2, artist=self.artist2)

    def test_templates(self):
        "Uses the correct templates"
        response = self.client.get(reverse('lastfm:%s' % self.view_name,
                                    kwargs={'username': 'bob',}))
        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, 'lastfm/%s.html' % self.view_name)
        self.assertTemplateUsed(response, 'lastfm/base.html')
        self.assertTemplateUsed(response, 'ditto/base.html')

    def test_context_counts(self):
        """Sends the correct count data to the templates.
        All user_* views should have these same counts in their context.
        """
        response = self.client.get(reverse('lastfm:%s' % self.view_name,
                                    kwargs={'username': 'bob',}))
        self.assertIn('counts', response.context)
        self.assertEqual(response.context['counts']['albums'], 1)
        self.assertEqual(response.context['counts']['artists'], 2)
        self.assertEqual(response.context['counts']['scrobbles'], 7)
        self.assertEqual(response.context['counts']['tracks'], 2)

    def test_404s(self):
        "Responds with 404 if we request a user that doesn't exist."
        response = self.client.get(reverse('lastfm:%s' % self.view_name,
                                    kwargs={'username': 'thelma',}))
        self.assertEquals(response.status_code, 404)


class UserDetailViewTestCase(UserCommonTests, TestCase):

    view_name = 'user_detail'


class UserAlbumListViewTestCase(UserCommonTests, TestCase):

    view_name = 'user_album_list'

    def test_context_albums(self):
        "Sends the correct album data to the templates"
        response = self.client.get(reverse('lastfm:%s' % self.view_name,
                                    kwargs={'username': 'bob',}))
        self.assertIn('album_list', response.context)
        albums = response.context['album_list']
        self.assertEqual(len(albums), 1)
        self.assertEqual(albums[0], self.album1)
        self.assertEqual(albums[0].scrobble_count, 2)


class UserArtistListViewTestCase(UserCommonTests, TestCase):

    view_name = 'user_artist_list'

    def test_context_albums(self):
        "Sends the correct album data to the templates"
        response = self.client.get(reverse('lastfm:%s' % self.view_name,
                                    kwargs={'username': 'bob',}))
        self.assertIn('artist_list', response.context)
        artists = response.context['artist_list']
        self.assertEqual(len(artists), 2)
        self.assertEqual(artists[0], self.artist2)
        self.assertEqual(artists[1], self.artist1)
        self.assertEqual(artists[0].scrobble_count, 5)
        self.assertEqual(artists[1].scrobble_count, 2)


class UserScrobbleListViewTestCase(UserCommonTests, TestCase):

    view_name = 'user_scrobble_list'

    def test_context_scrobbles(self):
        "Sends the correct scrobble data to the templates"
        response = self.client.get(reverse('lastfm:%s' % self.view_name,
                                    kwargs={'username': 'bob',}))
        self.assertIn('scrobble_list', response.context)
        scrobbles = response.context['scrobble_list']
        self.assertEqual(len(scrobbles), 7)


class UserTrackListViewTestCase(UserCommonTests, TestCase):

    view_name = 'user_track_list'

    def test_context_tracks(self):
        "Sends the correct track data to the templates"
        response = self.client.get(reverse('lastfm:%s' % self.view_name,
                                    kwargs={'username': 'bob',}))
        self.assertIn('track_list', response.context)
        tracks = response.context['track_list']
        self.assertEqual(len(tracks), 2)
        self.assertEqual(tracks[0], self.track2)
        self.assertEqual(tracks[0].scrobble_count, 5)
        self.assertEqual(tracks[1], self.track1)
        self.assertEqual(tracks[1].scrobble_count, 2)

