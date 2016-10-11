# coding: utf-8
from django.db import models
from django.core.urlresolvers import reverse

from ..core.models import DiffModelMixin, DittoItemModel, TimeStampedModelMixin

# For generating permalinks.
LASTFM_URL_ROOT = 'http://last.fm'

# For generating links to MB.
MUSICBRAINZ_URL_ROOT = 'https://musicbrainz.org'


class Account(TimeStampedModelMixin, models.Model):
    "The account of a user, with API key, on Last.fm"

    username = models.CharField(null=False, blank=False, max_length=30,
                unique=True,
                help_text="eg, 'rj'")

    realname = models.CharField(null=False, blank=False, max_length=30,
                unique=False,
                help_text="eg, 'Richard Jones'")

    api_key = models.CharField(blank=True, max_length=255,
                                                        verbose_name='API Key')
    is_active = models.BooleanField(default=True,
                        help_text="If false, new scrobbles won't be fetched.")

    def __str__(self):
        return self.username

    class Meta:
        ordering = ['username']

    def get_absolute_url(self):
        return reverse('lastfm:user_detail',
                                        kwargs={'username': self.username})

    @property
    def permalink(self):
        return '%s/user/%s' % (LASTFM_URL_ROOT, self.username)

    def has_credentials(self):
        "Does this at least have something in its API field? True or False"
        if self.api_key:
            return True
        else:
            return False


class Album(TimeStampedModelMixin, models.Model):
    """
    Minimal model of a music album.

    Last.fm's data isn't great - the album might be by various artists but,
    if the album has no MBID in the scrobble, we'll end up creating that album
    for each artist on the album.

    eg, with artist/track/album scrobbles like:
        Kelis / Milkshake / The Trevor Nelson Collection
        Luther Vandross / Never Too Much / The Trevor Nelson Collection

    we'd end up with two albums:
        Kelis / The Trevor Nelson Collection
        Luther Vandross / The Trevor Nelson Collection
    """

    name = models.TextField(null=False, blank=False)
    # We're not using SlugField because a Track slug can be longer than 255
    # characters and contain characters not allowed by SlugField().
    slug = models.TextField(null=False, blank=False, db_index=True)
    artist = models.ForeignKey('Artist', related_name='albums')
    mbid = models.CharField(null=False, blank=True, max_length=36,
            verbose_name="MBID",
            help_text="MusicBrainz Identifier")

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']

    def get_absolute_url(self):
        return reverse('lastfm:album_detail', kwargs={
            'artist_slug': self.artist.slug,
            'album_slug': self.slug,
        })

    @property
    def permalink(self):
        return '%s/music/%s/%s' % (
                                LASTFM_URL_ROOT, self.artist.slug, self.slug)

    @property
    def musicbrainz_url(self):
        if self.mbid:
            return '%s/release/%s' % (MUSICBRAINZ_URL_ROOT, self.mbid)
        else:
            return None


class Artist(TimeStampedModelMixin, models.Model):
    "Minimal model of a music artist."

    name = models.CharField(null=False, blank=False, max_length=255)
    # We're not using SlugField because an Artist slug can be longer than 255
    # characters and contain characters not allowed by SlugField().
    slug = models.TextField(null=False, blank=False, unique=True)
    mbid = models.CharField(null=False, blank=True, max_length=36,
            verbose_name="MBID",
            help_text="MusicBrainz Identifier")

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']

    def get_absolute_url(self):
        return reverse('lastfm:artist_detail', kwargs={
            'artist_slug': self.slug,
        })

    @property
    def permalink(self):
        return '%s/music/%s' % (LASTFM_URL_ROOT, self.slug)

    @property
    def musicbrainz_url(self):
        if self.mbid:
            return '%s/artist/%s' % (MUSICBRAINZ_URL_ROOT, self.mbid)
        else:
            return None

    def get_top_albums(self, num='all'):
        """
        Returns a QuerySet of Albums by this Artist, ordered by most-scrobbled.
        By default returns all of them.
        `num` is 'all' for all albums, or an integer to return that number.
        """
        qs = self.albums\
                    .annotate(scrobble_count=models.Count('scrobbles'))\
                    .order_by('-scrobble_count')

        if num == 'all':
            return qs
        else:
            return qs[:num]

    def get_top_tracks(self, num='all'):
        """
        Returns a QuerySet of Tracks by this Artist, ordered by most-scrobbled.
        By default returns all of them.
        `num` is 'all' for all tracks, or an integer to return that number.
        """
        qs = self.tracks\
                    .annotate(scrobble_count=models.Count('scrobbles'))\
                    .order_by('-scrobble_count')

        if num == 'all':
            return qs
        else:
            return qs[:num]


class Scrobble(DittoItemModel, models.Model):
    """
    A single play of a single music track.

    A lot of scrobbles have an album title, but the album has no MBID.
    In that case we record the title, but don't link this Scrobble to an
    Album model.
    """

    # Properties inherited from DittoItemModel:
    #
    # title         (CharField)
    # permalink     (URLField)
    # summary       (CharField)
    # is_private    (BooleanField)
    # fetch_time    (DateTimeField, UTC)
    # post_time     (DateTimeField, UTC) (ie, time of scrobble)
    # latitude      (DecimalField)
    # longitude     (DecimalField)
    # raw           (TextField)

    account = models.ForeignKey('Account')

    artist = models.ForeignKey('Artist', related_name='scrobbles')
    track = models.ForeignKey('Track', related_name='scrobbles')
    album = models.ForeignKey('Album', related_name='scrobbles',
                                                        blank=True, null=True)

    def __str__(self):
        return '%s (%s)' % (self.title, self.post_time)

    class Meta:
        ordering = ['-post_time']

    def save(self, *args, **kwargs):
        self.title = '%s – %s' % (self.track.artist.name, self.track.name)
        self.summary = str(self.post_time)
        super().save(*args, **kwargs)


class Track(TimeStampedModelMixin, models.Model):
    """
    Minimal model of a music track.

    We don't link Tracks to Albums directly. We only record the album info
    in the Scrobble, as it all seems a bit dodgy in Last.fm's modelling.
    """

    name = models.TextField(null=False, blank=False)
    # We're not using SlugField because a Track slug can be longer than 255
    # characters and contain characters not allowed by SlugField().
    slug = models.TextField(null=False, blank=False, db_index=True)
    artist = models.ForeignKey('Artist', related_name='tracks')
    mbid = models.CharField(null=False, blank=True, max_length=36,
            verbose_name="MBID",
            help_text="MusicBrainz Identifier")

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']

    def get_absolute_url(self):
        return reverse('lastfm:track_detail', kwargs={
            'artist_slug': self.artist.slug,
            'track_slug': self.slug,
        })

    @property
    def permalink(self):
        return '%s/music/%s/_/%s' % (
                                LASTFM_URL_ROOT, self.artist.slug, self.slug)

    @property
    def musicbrainz_url(self):
        if self.mbid:
            return '%s/recording/%s' % (MUSICBRAINZ_URL_ROOT, self.mbid)
        else:
            return None

