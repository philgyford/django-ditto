import datetime
import pytz
import factory

from . import models
from ..core.utils import datetime_now


class UserFactory(factory.DjangoModelFactory):
    class Meta:
        model = models.User

    twitter_id = factory.Sequence(lambda n: (n * 10000))
    screen_name = factory.Sequence(lambda n: 'user%d' % n)
    name = factory.Sequence(lambda n: 'User Name %d' % n)

    created_at = factory.LazyAttribute(lambda o:
                               datetime_now() - datetime.timedelta(weeks=52)
                            )

    description = factory.Sequence(lambda n: 'A description %d' % n)
    is_private = False
    fetch_time = datetime_now()


class AccountFactory(factory.DjangoModelFactory):
    class Meta:
        model = models.Account

    user = factory.SubFactory(UserFactory,
            twitter_id=factory.Sequence(lambda n: n),
            screen_name=factory.Sequence(lambda n: 'user%d' % n)
        )

class AccountWithCredentialsFactory(AccountFactory):
    """We only want to add these when we're going to be testing the
    fetching of API data for the Account's user.
    """
    consumer_key = 'TESTCONSUMERKEY'
    consumer_secret = 'TESTCONSUMERSECRET'
    access_token = factory.Sequence(lambda n: '%d-TESTACCESSTOKEN' % n)
    access_token_secret = 'TESTACCESSTOKENSECRET'


class TweetFactory(factory.DjangoModelFactory):

    class Meta:
        model = models.Tweet

    user = factory.SubFactory(UserFactory)
    text = factory.Sequence(lambda n: 'The text of tweet %d' % n)
    twitter_id = factory.Sequence(lambda n: (n * 10000000))
    fetch_time = datetime_now()

    post_time = factory.LazyAttribute(lambda o:
                                datetime_now() - datetime.timedelta(weeks=4)
                            )
    source = 'web'


class PhotoFactory(factory.DjangoModelFactory):

    class Meta:
        model = models.Media

    media_type = 'photo'
    tweet = factory.SubFactory(TweetFactory)
    twitter_id = factory.Sequence(lambda n: (n * 10000000))
    large_w = 938
    large_h = 397
    medium_w = 600
    medium_h = 253
    small_w = 340
    small_h = 143
    thumb_w = 150
    thumb_h = 150

    image_url = factory.Sequence(
                            lambda n: 'http://pbs.twimg.com/media/%d.jpg' % n)


class VideoFactory(factory.DjangoModelFactory):

    class Meta:
        model = models.Media

    media_type = 'video'
    tweet = factory.SubFactory(TweetFactory)
    twitter_id = factory.Sequence(lambda n: (n * 10000000))

    large_w = 640
    large_h = 360
    medium_w = 600
    medium_h = 338
    small_w = 340
    small_h = 191
    thumb_w = 150
    thumb_h = 150

    image_url = factory.Sequence(
        lambda n: 'http://pbs.twimg.com/ext_tw_video_thumb/%d/pu/img/%d.jpg' % (n, n))

    mp4_url_1 = factory.Sequence(lambda n: 'https://video.twimg.com/ext_tw_video/%d/pu/vid/320x180/%d.mp4' % (n, n))
    mp4_url_2 = factory.Sequence(lambda n: 'https://video.twimg.com/ext_tw_video/%d/pu/vid/640x360/%d.mp4' % (n, n))
    mp4_bitrate_1 = 320000
    mp4_bitrate_2 = 832000

    webm_url = factory.Sequence(lambda n: 'https://video.twimg.com/ext_tw_video/%d/pu/vid/640x360/%d.webm' % (n, n))

    aspect_ratio = '16:9'
    duration = 20000

