import datetime
import pytz
import factory

from taggit import models as taggit_models

from . import models
from ..core.utils import datetime_now


class UserFactory(factory.DjangoModelFactory):
    class Meta:
        model = models.User

    nsid = factory.Sequence(lambda n: '%s@N01' % (n * 10000))
    username = factory.Sequence(lambda n: 'user%04d' % n)
    realname = factory.Sequence(lambda n: 'User Name %04d' % n)
    iconserver = 1234
    iconfarm = 5
    timezone_id = 'America/Los_Angeles'
    photos_url = factory.Sequence(
                    lambda n: 'https://www.flickr.com/photos/user%04d/' % n)

    photos_first_date = factory.LazyAttribute(lambda o:
                               datetime_now() - datetime.timedelta(weeks=52)
                            )
    photos_first_date_taken = factory.LazyAttribute(lambda o:
                                datetime_now() - datetime.timedelta(weeks=52)
                            )
    fetch_time = datetime_now()

    avatar = factory.django.ImageField(filename='my_avatar.jpg')


class AccountFactory(factory.DjangoModelFactory):
    class Meta:
        model = models.Account

    user = factory.SubFactory(UserFactory,
            username=factory.Sequence(lambda n: n),
            realname=factory.Sequence(lambda n: 'User Name %04d' % n)
        )


class PhotoFactory(factory.DjangoModelFactory):
    class Meta:
        model = models.Photo

    user = factory.SubFactory(UserFactory,
            username=factory.Sequence(lambda n: n),
            realname=factory.Sequence(lambda n: 'User Name %04d' % n)
        )

    flickr_id = factory.Sequence(lambda n: (n * 1000000))
    title = factory.Sequence(lambda n: 'Photo %d' % n)
    secret = factory.Sequence(lambda n: (n * 10000))
    original_secret = factory.Sequence(lambda n: (n * 10001))
    original_format = 'jpg'
    server = '987'
    farm = 2
    media = 'photo'
    post_time = datetime_now()
    taken_time = factory.LazyAttribute(lambda o:
                                datetime_now() - datetime.timedelta(weeks=3)
                            )
    last_update_time = factory.LazyAttribute(lambda o:
                                datetime_now() - datetime.timedelta(weeks=2)
                            )
    fetch_time = factory.LazyAttribute(lambda o:
                                datetime_now() - datetime.timedelta(weeks=1)
                            )

    original_file = factory.django.ImageField(filename='example.jpg')
    video_original_file = factory.django.FileField(filename='example.mov')

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
    original_width = 3000
    original_height = 2000


class TagFactory(factory.DjangoModelFactory):

    class Meta:
        model = taggit_models.Tag

    slug = factory.Sequence(lambda n: 'slug%d' % n)
    name = slug


class TaggedPhotoFactory(factory.DjangoModelFactory):
    class Meta:
        model = models.TaggedPhoto

    tag = factory.SubFactory(TagFactory)
    flickr_id = factory.Sequence(lambda n: (n * 1000))
    author = factory.SubFactory(UserFactory)
    machine_tag = False
    content_object = factory.SubFactory(PhotoFactory)


class PhotosetFactory(factory.DjangoModelFactory):
    class Meta:
        model = models.Photoset

    user = factory.SubFactory(UserFactory,
            username=factory.Sequence(lambda n: n),
            realname=factory.Sequence(lambda n: 'User Name %04d' % n)
        )
    flickr_id = factory.Sequence(lambda n: (n * 1000000))
    title = factory.Sequence(lambda n: 'Photoset %d' % n)
    flickr_created_time = datetime_now()
    fetch_time = datetime_now()

