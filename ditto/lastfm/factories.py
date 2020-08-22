import factory

from . import models
from ..core.utils import datetime_now


class AccountFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Account

    username = factory.Sequence(lambda n: "user%04d" % n)
    realname = factory.Sequence(lambda n: "Real Name %04d" % n)
    api_key = factory.Sequence(lambda n: "api-key-%04d" % n)


class ArtistFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Artist

    name = factory.Sequence(lambda n: "Artist %04d" % n)
    slug = factory.Sequence(lambda n: "artist+%04d" % n)
    original_slug = factory.Sequence(lambda n: "Artist+%04d" % n)


class TrackFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Track

    name = factory.Sequence(lambda n: "Track %04d" % n)
    slug = factory.Sequence(lambda n: "track+%04d" % n)
    original_slug = factory.Sequence(lambda n: "Track+%04d" % n)
    artist = factory.SubFactory(ArtistFactory)


class AlbumFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Album

    name = factory.Sequence(lambda n: "Album %04d" % n)
    slug = factory.Sequence(lambda n: "album+%04d" % n)
    original_slug = factory.Sequence(lambda n: "Album+%04d" % n)
    artist = factory.SubFactory(ArtistFactory)


class ScrobbleFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Scrobble

    account = factory.SubFactory(AccountFactory)
    track = factory.SubFactory(TrackFactory)
    artist = factory.SubFactory(ArtistFactory)
    post_time = datetime_now()
