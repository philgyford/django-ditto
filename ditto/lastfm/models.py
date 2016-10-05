# coding: utf-8
from django.db import models
from django.core.urlresolvers import reverse

from ..core.models import DiffModelMixin, DittoItemModel, TimeStampedModelMixin

# For generating permalinks.
LASTFM_URL_ROOT = 'http://last.fm'


def lastfm_get_absolute_url(kind, id, mbid=''):
    """
    Generates the absolute URLs for artists, tracks and albums.

    kind -- One of 'artist', 'track' or 'album'.
    id -- The Django ID of the object.
    mbid -- The MBID of the object (Optional).
    """
    url_names = {
        'artist':   'lastfm:artist_detail',
        'track':    'lastfm:track_detail',
        'album':    'lastfm:album_detail',
    }

    # We won't have an MBID for every thing, so we'll fall back to ID.
    url_id = mbid if mbid != '' else id
    url_name = url_names[kind]
    return reverse(url_name, kwargs={'id': url_id})


def lastfm_urlify(s):
    """
    Takes a string and returns the version used in a Last.fm URL

    I don't think we can use something like urllib.parse.quote_plus() because
    there are some things - eg, ,.&!() - which Last.fm doesn't escape.
    """

    replacements = (
        ('%', '%25'), # Needs to be first.
        ('"', '%22'),
        ("'", '%27'),
        ('/', '%2F'),
        (';', '%3B'),
        ('<', '%3C'),
        ('>', '%3E'),
        ('?', '%3F'),
        ('[', '%5B'),
        ('\\', '%5C%5C'), # Replaces one backslash with '%5C%5C'.
        (']', '%5D'),
        ('^', '%5E'),
        ('`', '%60'),
        ('{', '%7B'),
        ('|', '%7C'),
        ('}', '%7D'),
        ('+', '%252B'),
        ('#', '%2316'),
        (' ', '+'), # Needs to be after the + encoding.
    )
    for find, repl in replacements:
        s = s.replace(find, repl)
    return s


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
    if in the scrobble the album has no MBID, we'll end up creating that album
    for each artist on the album.

    eg, with artist/track/album scrobbles like:
        Kelis / Milkshake / The Trevor Nelson Collection
        Luther Vandross / Never Too Much / The Trevor Nelson Collection

    we'd end up with two albums:
        Kelis / The Trevor Nelson Collection
        Luther Vandross / The Trevor Nelson Collection
    """

    name = models.TextField(null=False, blank=False)
    artist = models.ForeignKey('Artist', related_name='albums')
    mbid = models.CharField(null=False, blank=True, max_length=36,
            db_index=True,
            verbose_name="MBID",
            help_text="MusicBrainz Identifier")

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']

    def get_absolute_url(self):
        return lastfm_get_absolute_url('album', self.id, self.mbid)

    @property
    def permalink(self):
        return '%s/music/%s/%s' % (LASTFM_URL_ROOT,
                                   lastfm_urlify(self.artist.name),
                                   lastfm_urlify(self.name) )


class Artist(TimeStampedModelMixin, models.Model):
    "Minimal model of a music artist."

    name = models.CharField(null=False, blank=False, max_length=255)
    mbid = models.CharField(null=False, blank=True, max_length=36,
            db_index=True,
            verbose_name="MBID",
            help_text="MusicBrainz Identifier")

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']

    def get_absolute_url(self):
        return lastfm_get_absolute_url('artist', self.id, self.mbid)

    @property
    def permalink(self):
        return '%s/music/%s' % (LASTFM_URL_ROOT, lastfm_urlify(self.name))

    def get_top_albums(self, num=10):
        "Returns a QuerySet of `num` most scrobbled Albums by this Artist."
        qs = self.albums\
                    .annotate(scrobble_count=models.Count('scrobbles'))\
                    .order_by('-scrobble_count')
        return qs[:num]

    def get_top_tracks(self, num=10):
        "Returns a QuerySet of `num` most scrobbled Tracks by this Artist."
        qs = self.tracks\
                    .annotate(scrobble_count=models.Count('scrobbles'))\
                    .order_by('-scrobble_count')
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

    # Let's try denormalizing these things so that we can list scrobbles from
    # a particular day (etc) without making umpteen database requests:
    artist_name = models.CharField(null=False, blank=True, max_length=255)
    artist_mbid = models.CharField(null=False, blank=True, max_length=36,
                                            verbose_name="Artist MBID",
                                            help_text="MusicBrainz Identifier")
    track_name = models.TextField(null=False, blank=True)
    track_mbid = models.CharField(null=False, blank=True, max_length=36,
                                            verbose_name="Track MBID",
                                            help_text="MusicBrainz Identifier")
    album_name = models.TextField(null=False, blank=True)
    album_mbid = models.CharField(null=False, blank=True, max_length=36,
                                            verbose_name="Album MBID",
                                            help_text="MusicBrainz Identifier")

    def __str__(self):
        return '%s (%s)' % (self.title, self.post_time)

    class Meta:
        ordering = ['-post_time']

    def save(self, *args, **kwargs):
        self.title = '%s – %s' % (self.artist_name, self.track_name)
        self.summary = str(self.post_time)
        super().save(*args, **kwargs)

    def get_absolute_url_artist(self):
        return lastfm_get_absolute_url(
                                    'artist', self.artist.id, self.artist_mbid)

    def get_absolute_url_track(self):
        return lastfm_get_absolute_url('track', self.track.id, self.track_mbid)

    def get_absolute_url_album(self):
        if self.album:
            return lastfm_get_absolute_url(
                                    'album', self.album.id, self.album_mbid)
        else:
            return ''


class Track(TimeStampedModelMixin, models.Model):
    """
    Minimal model of a music track.
    We don't link Tracks to Albums directly. We only record the album info
    in the Scrobble, as it all seems a bit dodgy in Last.fm's modelling.
    """

    name = models.TextField(null=False, blank=False)
    artist = models.ForeignKey('Artist', related_name='tracks')
    mbid = models.CharField(null=False, blank=True, max_length=36,
            db_index=True,
            verbose_name="MBID",
            help_text="MusicBrainz Identifier")

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']

    def get_absolute_url(self):
        return lastfm_get_absolute_url('track', self.id, self.mbid)

    @property
    def permalink(self):
        return '%s/music/%s/_/%s' % (LASTFM_URL_ROOT,
                                     lastfm_urlify(self.artist.name),
                                     lastfm_urlify(self.name) )

