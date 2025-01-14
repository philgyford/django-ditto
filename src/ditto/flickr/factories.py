import datetime

import factory
from taggit import models as taggit_models

from ditto.core.utils import datetime_now

from . import models


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.User

    nsid = factory.Sequence(lambda n: f"{n * 10000}@N01")
    username = factory.Sequence(lambda n: f"user{n:04}")
    realname = factory.Sequence(lambda n: f"User Name {n:04}")
    iconserver = 1234
    iconfarm = 5
    timezone_id = "America/Los_Angeles"
    photos_url = factory.Sequence(
        lambda n: f"https://www.flickr.com/photos/user{n:04}/"
    )

    photos_first_date = factory.LazyAttribute(
        lambda o: datetime_now() - datetime.timedelta(weeks=52)
    )
    photos_first_date_taken = factory.LazyAttribute(
        lambda o: datetime_now() - datetime.timedelta(weeks=52)
    )
    fetch_time = datetime_now()

    avatar = factory.django.ImageField(filename="my_avatar.jpg")


class AccountFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Account

    user = factory.SubFactory(
        UserFactory,
        username=factory.Sequence(lambda n: n),
        realname=factory.Sequence(lambda n: f"User Name {n:04}"),
    )


class PhotoFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Photo

    user = factory.SubFactory(
        UserFactory,
        username=factory.Sequence(lambda n: n),
        realname=factory.Sequence(lambda n: f"User Name {n:04}"),
    )

    flickr_id = factory.Sequence(lambda n: (n * 1000000))
    title = factory.Sequence(lambda n: f"Photo {n}")
    secret = factory.Sequence(lambda n: (n * 10000))
    original_secret = factory.Sequence(lambda n: (n * 10001))
    original_format = "jpg"
    server = "987"
    farm = 2
    media = "photo"
    post_time = datetime_now()
    taken_time = factory.LazyAttribute(
        lambda o: datetime_now() - datetime.timedelta(weeks=3)
    )
    last_update_time = factory.LazyAttribute(
        lambda o: datetime_now() - datetime.timedelta(weeks=2)
    )
    fetch_time = factory.LazyAttribute(
        lambda o: datetime_now() - datetime.timedelta(weeks=1)
    )

    original_file = factory.django.ImageField(filename="example.jpg")
    video_original_file = factory.django.FileField(filename="example.mov")

    thumbnail_width = 100
    thumbnail_height = 67
    small_width = 240
    small_height = 160
    small_320_width = 320
    small_320_height = 213
    medium_width = 500
    medium_height = 333
    medium_640_width = 640
    medium_640_height = 427
    medium_800_width = 800
    medium_800_height = 533
    large_width = 1024
    large_height = 683
    large_1600_width = 1600
    large_1600_height = 1067
    large_2048_width = 2048
    large_2048_height = 1365
    x_large_3k_width = 3072
    x_large_3k_height = 2048
    x_large_4k_width = 4096
    x_large_4k_height = 2731
    x_large_5k_width = 5120
    x_large_5k_height = 3413
    x_large_6k_width = 6000
    x_large_6k_height = 4000
    original_width = 6000
    original_height = 4000


class TagFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = taggit_models.Tag

    slug = factory.Sequence(lambda n: f"slug{n}")
    name = slug


class TaggedPhotoFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.TaggedPhoto

    tag = factory.SubFactory(TagFactory)
    flickr_id = factory.Sequence(lambda n: (n * 1000))
    author = factory.SubFactory(UserFactory)
    machine_tag = False
    content_object = factory.SubFactory(PhotoFactory)


class PhotosetFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Photoset

    user = factory.SubFactory(
        UserFactory,
        username=factory.Sequence(lambda n: n),
        realname=factory.Sequence(lambda n: f"User Name {n:04}"),
    )
    flickr_id = factory.Sequence(lambda n: (n * 1000000))
    title = factory.Sequence(lambda n: f"Photoset {n}")
    flickr_created_time = datetime_now()
    fetch_time = datetime_now()
