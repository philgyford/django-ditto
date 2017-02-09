# coding: utf-8
from django.db import models
from django.core.urlresolvers import reverse

from ..core.models import DiffModelMixin, DittoItemModel, TimeStampedModelMixin
from ..core.utils import truncate_string
from . import managers


# For generating permalinks.
LASTFM_URL_ROOT = 'http://www.last.fm'

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
        return self.realname

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

    def get_recent_scrobbles(self, limit=10):
        return self.scrobbles.prefetch_related('artist', 'track')\
                                .order_by('-post_time')[:limit]


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
    slug = models.TextField(null=False, blank=False, db_index=True,
            help_text="Lowercase")
    original_slug = models.TextField(null=False, blank=False,
            help_text="As used on Last.fm. Mixed case.")
    artist = models.ForeignKey('Artist', related_name='albums')
    mbid = models.CharField(null=False, blank=True, max_length=36,
            verbose_name="MBID",
            help_text="MusicBrainz Identifier")

    objects = managers.AlbumsManager()

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']

    def get_absolute_url(self):
        "The Album's URL locally."
        return reverse('lastfm:album_detail', kwargs={
            'artist_slug': self.artist.slug,
            'album_slug': self.slug,
        })

    @property
    def permalink(self):
        "The Album's URL at Last.fm."
        return '%s/music/%s/%s' % (LASTFM_URL_ROOT,
                                   self.artist.original_slug,
                                   self.original_slug)

    @property
    def musicbrainz_url(self):
        if self.mbid:
            return '%s/release/%s' % (MUSICBRAINZ_URL_ROOT, self.mbid)
        else:
            return None

    @property
    def tracks(self):
        """
        A QuerySet of all the Tracks on this Album, ordered by how many times
        they were scrobbled, most-scrobbled first.
        """
        qs = Track.objects.with_scrobble_counts(album=self)
        return qs

    def get_scrobble_count(self):
        """
        If we just have a `scrobble_count` property it clashes when we use
        the Album.objects.with_scrobble_count() query.
        """
        return self.scrobbles.count()

    def get_most_recent_scrobble(self):
        """
        Returns the most recent Scrobble object for this Album.
        """
        return self.scrobbles.order_by('-post_time').first()


class Artist(TimeStampedModelMixin, models.Model):
    "Minimal model of a music artist."

    name = models.CharField(null=False, blank=False, max_length=255)
    # We're not using SlugField because an Artist slug can be longer than 255
    # characters and contain characters not allowed by SlugField().
    slug = models.TextField(null=False, blank=False, unique=True,
            help_text="Lowercase")
    original_slug = models.TextField(null=False, blank=False, unique=True,
            help_text="As used on Last.fm. Mixed case.")
    mbid = models.CharField(null=False, blank=True, max_length=36,
            verbose_name="MBID",
            help_text="MusicBrainz Identifier")

    objects = managers.ArtistsManager()

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']

    def get_absolute_url(self):
        "The Artist's URL locally."
        return reverse('lastfm:artist_detail', kwargs={
            'artist_slug': self.slug,
        })

    @property
    def permalink(self):
        "The Artist's URL at Last.fm."
        return '%s/music/%s' % (LASTFM_URL_ROOT, self.original_slug)

    @property
    def musicbrainz_url(self):
        if self.mbid:
            return '%s/artist/%s' % (MUSICBRAINZ_URL_ROOT, self.mbid)
        else:
            return None

    def get_scrobble_count(self):
        """
        If we just have a `scrobble_count` property it clashes when we use
        the Artist.objects.with_scrobble_count() query.
        """
        return self.scrobbles.count()

    def get_top_albums(self, limit='all'):
        """
        Returns a QuerySet of Albums by this Artist, ordered by most-scrobbled.
        By default returns all of them.
        `limit` is 'all' for all albums, or an integer to return that number.
        """
        qs = self.albums.with_scrobble_counts()

        if limit == 'all':
            return qs
        else:
            return qs[:limit]

    def get_top_tracks(self, limit='all'):
        """
        Returns a QuerySet of Tracks by this Artist, ordered by most-scrobbled.
        By default returns all of them.
        `limit` is 'all' for all tracks, or an integer to return that number.
        """
        qs = self.tracks.with_scrobble_counts()

        if limit == 'all':
            return qs
        else:
            return qs[:limit]

    def get_most_recent_scrobble(self):
        """
        Returns the most recent Scrobble object for this Artist.
        """
        return self.scrobbles.order_by('-post_time').first()


class Scrobble(DittoItemModel, models.Model):
    """
    A single play of a single music track.

    A lot of scrobbles have an album title, but the album has no MBID.
    In that case we record the title, but don't link this Scrobble to an
    Album model.
    """

    ditto_item_name = 'lastfm_scrobble'

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

    account = models.ForeignKey('Account', related_name='scrobbles')

    artist = models.ForeignKey('Artist', related_name='scrobbles')
    track = models.ForeignKey('Track', related_name='scrobbles')
    album = models.ForeignKey('Album', related_name='scrobbles',
                                                        blank=True, null=True)

    def __str__(self):
        return '%s (%s)' % (self.title, self.post_time)

    class Meta:
        ordering = ['-post_time']

    def save(self, *args, **kwargs):
        self.title = truncate_string(
            '{} – {}'.format(self.track.artist.name, self.track.name),
            chars=255,
            truncate='…',
            at_word_boundary=True
        )
        super().save(*args, **kwargs)

    def _summary_source(self):
        "Used to make the `summary` property."
        return self.post_time.strftime('%Y-%m-%d %H:%M')


class Track(TimeStampedModelMixin, models.Model):
    """
    Minimal model of a music track.

    We don't link Tracks to Albums directly. We only record the album info
    in the Scrobble, as it all seems a bit dodgy in Last.fm's modelling.
    """

    name = models.TextField(null=False, blank=False)
    # We're not using SlugField because a Track slug can be longer than 255
    # characters and contain characters not allowed by SlugField().
    slug = models.TextField(null=False, blank=False, db_index=True,
            help_text="Lowercase")
    original_slug = models.TextField(null=False, blank=False,
            help_text="As used on Last.fm. Mixed case.")
    artist = models.ForeignKey('Artist', related_name='tracks')
    mbid = models.CharField(null=False, blank=True, max_length=36,
            verbose_name="MBID",
            help_text="MusicBrainz Identifier")

    objects = managers.TracksManager()

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']

    def get_absolute_url(self):
        "The track's URL locally."
        return reverse('lastfm:track_detail', kwargs={
            'artist_slug': self.artist.slug,
            'track_slug': self.slug,
        })

    @property
    def permalink(self):
        "The Track's URL at Last.fm."
        return '%s/music/%s/_/%s' % (LASTFM_URL_ROOT,
                                     self.artist.original_slug,
                                    self.original_slug)

    @property
    def musicbrainz_url(self):
        if self.mbid:
            return '%s/recording/%s' % (MUSICBRAINZ_URL_ROOT, self.mbid)
        else:
            return None

    @property
    def albums(self):
        """
        A QuerySet of all the Albums on which this Track has appeared, ordered
        by how many times the Album was scrobbled, most-scrobbled first.
        """
        return Album.objects.with_scrobble_counts(track=self)

    def get_scrobble_count(self):
        """
        If we just have a `scrobble_count` property it clashes when we use
        the Track.objects.with_scrobble_count() query.
        """
        return self.scrobbles.count()

    def get_most_recent_scrobble(self):
        """
        Returns the most recent Scrobble object for this Track.
        """
        return self.scrobbles.order_by('-post_time').first()

