from django.core.urlresolvers import reverse
from django.test import TestCase

from ditto.lastfm.factories import AccountFactory, AlbumFactory,\
        ArtistFactory, ScrobbleFactory, TrackFactory


class HomeViewTests(TestCase):

    def test_home_templates(self):
        "Uses the correct templates"
        response = self.client.get(reverse('lastfm:home'))
        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, 'lastfm/home.html')
        self.assertTemplateUsed(response, 'lastfm/base.html')
        self.assertTemplateUsed(response, 'ditto/base.html')

    def test_home_context(self):
        "Sends the correct data to the templates"
        accounts = AccountFactory.create_batch(3)
        response = self.client.get(reverse('lastfm:home'))
        self.assertIn('account_list', response.context)
        self.assertEqual(len(response.context['account_list']), 3)


class AlbumDetailViewTests(TestCase):

    def setUp(self):
        self.artist = ArtistFactory(slug='Lou+Reed')
        self.album = AlbumFactory(slug='New+York', artist=self.artist)

    def test_album_detail_templates(self):
        "Uses the correct templates"
        response = self.client.get(reverse('lastfm:album_detail',
                                    kwargs={'artist_slug': self.artist.slug,
                                            'album_slug': self.album.slug,}))
        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, 'lastfm/album_detail.html')
        self.assertTemplateUsed(response, 'lastfm/base.html')
        self.assertTemplateUsed(response, 'ditto/base.html')

    def test_album_detail_context(self):
        "Sends the correct data to the templates"
        response = self.client.get(reverse('lastfm:album_detail',
                                    kwargs={'artist_slug': self.artist.slug,
                                            'album_slug': self.album.slug,}))
        self.assertIn('album', response.context)
        self.assertEqual(self.album.pk, response.context['album'].pk)

    def test_album_detail_404s(self):
        "Responds with 404 if we request an album that doesn't exist."
        response = self.client.get(reverse('lastfm:album_detail',
                                    kwargs={'artist_slug': self.artist.slug,
                                            'album_slug': 'Transformer',}))
        self.assertEquals(response.status_code, 404)


class ArtistDetailViewTests(TestCase):

    def setUp(self):
        self.artist = ArtistFactory(slug='Lou+Reed')

    def test_artist_detail_templates(self):
        "Uses the correct templates"
        response = self.client.get(reverse('lastfm:artist_detail',
                                    kwargs={'artist_slug': self.artist.slug,}))
        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, 'lastfm/artist_detail.html')
        self.assertTemplateUsed(response, 'lastfm/base.html')
        self.assertTemplateUsed(response, 'ditto/base.html')

    def test_artist_detail_context(self):
        "Sends the correct data to the templates"
        response = self.client.get(reverse('lastfm:artist_detail',
                                    kwargs={'artist_slug': self.artist.slug,}))
        self.assertIn('artist', response.context)
        self.assertEqual(self.artist.pk, response.context['artist'].pk)

    def test_artist_detail_404s(self):
        "Responds with 404 if we request an artist that doesn't exist."
        response = self.client.get(reverse('lastfm:artist_detail',
                                    kwargs={'artist_slug': 'Looper',}))
        self.assertEquals(response.status_code, 404)


class ArtistAlbumsViewTests(TestCase):

    def setUp(self):
        self.artist = ArtistFactory(slug='Lou+Reed')

    def test_artist_albums_templates(self):
        "Uses the correct templates"
        response = self.client.get(reverse('lastfm:artist_albums',
                                    kwargs={'artist_slug': self.artist.slug,}))
        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, 'lastfm/artist_albums.html')
        self.assertTemplateUsed(response, 'lastfm/base.html')
        self.assertTemplateUsed(response, 'ditto/base.html')

    def test_artist_albums_context(self):
        "Sends the correct data to the templates"
        response = self.client.get(reverse('lastfm:artist_albums',
                                    kwargs={'artist_slug': self.artist.slug,}))
        self.assertIn('artist', response.context)
        self.assertEqual(self.artist.pk, response.context['artist'].pk)

    def test_artist_albums_404s(self):
        "Responds with 404 if we request an artist that doesn't exist."
        response = self.client.get(reverse('lastfm:artist_albums',
                                    kwargs={'artist_slug': 'Looper',}))
        self.assertEquals(response.status_code, 404)


class TrackDetailViewTests(TestCase):

    def setUp(self):
        self.artist = ArtistFactory(slug='Lou+Reed')
        self.track = TrackFactory(slug='Hold+On', artist=self.artist)

    def test_track_detail_templates(self):
        "Uses the correct templates"
        response = self.client.get(reverse('lastfm:track_detail',
                                    kwargs={'artist_slug': self.artist.slug,
                                            'track_slug': self.track.slug,}))
        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, 'lastfm/track_detail.html')
        self.assertTemplateUsed(response, 'lastfm/base.html')
        self.assertTemplateUsed(response, 'ditto/base.html')

    def test_track_detail_context(self):
        "Sends the correct data to the templates"
        response = self.client.get(reverse('lastfm:track_detail',
                                    kwargs={'artist_slug': self.artist.slug,
                                            'track_slug': self.track.slug,}))
        self.assertIn('track', response.context)
        self.assertEqual(self.track.pk, response.context['track'].pk)

    def test_track_detail_404s(self):
        "Responds with 404 if we request a track that doesn't exist."
        response = self.client.get(reverse('lastfm:track_detail',
                                    kwargs={'artist_slug': self.artist.slug,
                                            'track_slug': 'Viscious',}))
        self.assertEquals(response.status_code, 404)

