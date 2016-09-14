import factory

from . import models
from ..core.utils import datetime_now


class AccountFactory(factory.DjangoModelFactory):
    class Meta:
        model = models.Account

    username = factory.Sequence(lambda n: 'user%04d' % n)
    realname = factory.Sequence(lambda n: 'Real Name %04d' % n)
    api_key = factory.Sequence(lambda n: 'api-key-%04d' % n)


class ArtistFactory(factory.DjangoModelFactory):
    class Meta:
        model = models.Artist

    name = factory.Sequence(lambda n: 'Artist %04d' % n)

class TrackFactory(factory.DjangoModelFactory):
    class Meta:
        model = models.Track

    name = factory.Sequence(lambda n: 'Track %04d' % n)
    artist = factory.SubFactory(ArtistFactory)


class AlbumFactory(factory.DjangoModelFactory):
    class Meta:
        model = models.Album

    name = factory.Sequence(lambda n: 'Album %04d' % n)
    artist = factory.SubFactory(ArtistFactory)


class ScrobbleFactory(factory.DjangoModelFactory):
    class Meta:
        model = models.Scrobble

    account = factory.SubFactory(AccountFactory)
    artist = factory.SubFactory(ArtistFactory)
    track = factory.SubFactory(TrackFactory)

    artist_name = factory.Sequence(lambda n: 'Artist Name %04d' % n)
    track_name = factory.Sequence(lambda n: 'Track Name %04d' % n)

    post_time = datetime_now()

