from django.core.urlresolvers import reverse
from django.test import TestCase

from ditto.lastfm.factories import AccountFactory, AlbumFactory,\
        ArtistFactory, ScrobbleFactory, TrackFactory


class albumDetailViewTests(TestCase):

    def setUp(self):
        self.album = AlbumFactory(
                                mbid='708d3f34-d189-4f0b-aaa9-f62dd6a5399a')

    def test_album_detail_templates(self):
        "Uses the correct templates"
        response = self.client.get(reverse('lastfm:album_detail',
                                    kwargs={'id': self.album.mbid,}))
        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, 'lastfm/album_detail.html')
        self.assertTemplateUsed(response, 'lastfm/album_detail.html')
        self.assertTemplateUsed(response, 'ditto/base.html')

    def test_album_detail_context(self):
        "Sends the correct data to the templates"
        response = self.client.get(reverse('lastfm:album_detail',
                                    kwargs={'id': self.album.mbid,}))
        self.assertIn('album', response.context)
        self.assertEqual(self.album.pk, response.context['album'].pk)

    def test_album_detail_redirects_with_pk_and_mbid(self):
        "If it uses a Django PK but has an MBID, it redirects"
        response = self.client.get(reverse('lastfm:album_detail',
                                    kwargs={'id': self.album.id,}))
        self.assertRedirects(response,
                        '/lastfm/album/708d3f34-d189-4f0b-aaa9-f62dd6a5399a/')

    def test_album_detail_does_not_redirect_with_no_mbid(self):
        "If it uses a Django PK but has no MBID, it does not redirect"
        self.album.mbid = ''
        self.album.save()
        response = self.client.get(reverse('lastfm:album_detail',
                                    kwargs={'id': self.album.id,}))
        self.assertEquals(response.status_code, 200)


class ArtistDetailViewTests(TestCase):

    def setUp(self):
        self.artist = ArtistFactory(
                                mbid='199097d0-c306-40e8-80ae-b87659695e82')

    def test_artist_detail_templates(self):
        "Uses the correct templates"
        response = self.client.get(reverse('lastfm:artist_detail',
                                    kwargs={'id': self.artist.mbid,}))
        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, 'lastfm/artist_detail.html')
        self.assertTemplateUsed(response, 'lastfm/artist_detail.html')
        self.assertTemplateUsed(response, 'ditto/base.html')

    def test_artist_detail_context(self):
        "Sends the correct data to the templates"
        response = self.client.get(reverse('lastfm:artist_detail',
                                    kwargs={'id': self.artist.mbid,}))
        self.assertIn('artist', response.context)
        self.assertEqual(self.artist.pk, response.context['artist'].pk)

    def test_artist_detail_redirects_with_pk_and_mbid(self):
        "If it uses a Django PK but has an MBID, it redirects"
        response = self.client.get(reverse('lastfm:artist_detail',
                                    kwargs={'id': self.artist.id,}))
        self.assertRedirects(response,
                        '/lastfm/artist/199097d0-c306-40e8-80ae-b87659695e82/')

    def test_artist_detail_does_not_redirect_with_no_mbid(self):
        "If it uses a Django PK but has no MBID, it does not redirect"
        self.artist.mbid = ''
        self.artist.save()
        response = self.client.get(reverse('lastfm:artist_detail',
                                    kwargs={'id': self.artist.id,}))
        self.assertEquals(response.status_code, 200)


class TrackDetailViewTests(TestCase):

    def setUp(self):
        self.track = TrackFactory(
                                mbid='e9861fe5-8340-49e2-a45f-6e01a5089e92')

    def test_track_detail_templates(self):
        "Uses the correct templates"
        response = self.client.get(reverse('lastfm:track_detail',
                                    kwargs={'id': self.track.mbid,}))
        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, 'lastfm/track_detail.html')
        self.assertTemplateUsed(response, 'lastfm/track_detail.html')
        self.assertTemplateUsed(response, 'ditto/base.html')

    def test_track_detail_context(self):
        "Sends the correct data to the templates"
        response = self.client.get(reverse('lastfm:track_detail',
                                    kwargs={'id': self.track.mbid,}))
        self.assertIn('track', response.context)
        self.assertEqual(self.track.pk, response.context['track'].pk)

    def test_track_detail_redirects_with_pk_and_mbid(self):
        "If it uses a Django PK but has an MBID, it redirects"
        response = self.client.get(reverse('lastfm:track_detail',
                                    kwargs={'id': self.track.id,}))
        self.assertRedirects(response,
                        '/lastfm/track/e9861fe5-8340-49e2-a45f-6e01a5089e92/')

    def test_track_detail_does_not_redirect_with_no_mbid(self):
        "If it uses a Django PK but has no MBID, it does not redirect"
        self.track.mbid = ''
        self.track.save()
        response = self.client.get(reverse('lastfm:track_detail',
                                    kwargs={'id': self.track.id,}))
        self.assertEquals(response.status_code, 200)

