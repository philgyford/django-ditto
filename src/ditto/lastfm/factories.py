import factory

from ditto.core.utils import datetime_now

from . import models


class AccountFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Account

    username = factory.Sequence(lambda n: f"user{n:04}")
    realname = factory.Sequence(lambda n: f"Real Name {n:04}")
    api_key = factory.Sequence(lambda n: f"api-key-{n:04}")


class ArtistFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Artist

    name = factory.Sequence(lambda n: f"Artist {n:04}")
    slug = factory.Sequence(lambda n: f"artist+{n:04}")
    original_slug = factory.Sequence(lambda n: f"Artist+{n:04}")


class TrackFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Track

    name = factory.Sequence(lambda n: f"Track {n:04}")
    slug = factory.Sequence(lambda n: f"track+{n:04}")
    original_slug = factory.Sequence(lambda n: f"Track+{n:04}")
    artist = factory.SubFactory(ArtistFactory)


class AlbumFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Album

    name = factory.Sequence(lambda n: f"Album {n:04}")
    slug = factory.Sequence(lambda n: f"album+{n:04}")
    original_slug = factory.Sequence(lambda n: f"Album+{n:04}")
    artist = factory.SubFactory(ArtistFactory)


class ScrobbleFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Scrobble

    account = factory.SubFactory(AccountFactory)
    track = factory.SubFactory(TrackFactory)
    artist = factory.SubFactory(ArtistFactory)
    post_time = datetime_now()
