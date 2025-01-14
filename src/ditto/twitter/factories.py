import datetime

import factory

from ditto.core.utils import datetime_now

from . import models


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.User

    twitter_id = factory.Sequence(lambda n: (n * 10000))
    screen_name = factory.Sequence(lambda n: f"user{n}")
    name = factory.Sequence(lambda n: f"User Name {n}")

    created_at = factory.LazyAttribute(
        lambda o: datetime_now() - datetime.timedelta(weeks=52)
    )

    description = factory.Sequence(lambda n: f"A description {n}")
    is_private = False
    fetch_time = datetime_now()

    avatar = factory.django.ImageField(filename="my_avatar.jpg")


class AccountFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Account

    user = factory.SubFactory(
        UserFactory,
        twitter_id=factory.Sequence(lambda n: n),
        screen_name=factory.Sequence(lambda n: f"user{n}"),
    )


class AccountWithCredentialsFactory(AccountFactory):
    """We only want to add these when we're going to be testing the
    fetching of API data for the Account's user.
    """

    consumer_key = "TESTCONSUMERKEY"
    consumer_secret = "TESTCONSUMERSECRET"
    access_token = factory.Sequence(lambda n: f"{n}-TESTACCESSTOKEN")
    access_token_secret = "TESTACCESSTOKENSECRET"


class TweetFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Tweet

    user = factory.SubFactory(UserFactory)
    text = factory.Sequence(lambda n: f"The text of tweet {n}")
    twitter_id = factory.Sequence(lambda n: (n * 10000000))
    fetch_time = datetime_now()

    post_time = factory.LazyAttribute(
        lambda o: datetime_now() - datetime.timedelta(weeks=4)
    )
    source = "web"


class MediaFactory(factory.django.DjangoModelFactory):
    "Parent class for the photo, video and gif factories."

    class Meta:
        model = models.Media

    twitter_id = factory.Sequence(lambda n: (n * 10000000))
    large_w = 640
    large_h = 360
    medium_w = 600
    medium_h = 338
    small_w = 340
    small_h = 191
    thumb_w = 150
    thumb_h = 150

    image_file = factory.django.ImageField(filename="example.jpg")
    mp4_file = factory.django.FileField(filename="example.mp4")

    @factory.post_generation
    def tweets(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for tweet in extracted:
                self.tweets.add(tweet)


class PhotoFactory(MediaFactory):
    media_type = "photo"

    large_w = 938
    large_h = 397
    medium_w = 600
    medium_h = 253
    small_w = 340
    small_h = 143
    thumb_w = 150
    thumb_h = 150

    image_url = factory.Sequence(lambda n: f"http://pbs.twimg.com/media/{n}.jpg")
    image_file = factory.django.ImageField(filename="example.jpg")


class VideoFactory(MediaFactory):
    media_type = "video"

    image_url = factory.Sequence(
        lambda n: f"http://pbs.twimg.com/ext_tw_video_thumb/{n}/pu/img/{n}.jpg"
    )

    xmpeg_url = factory.Sequence(
        lambda n: f"https://video.twimg.com/ext_tw_video/{n}/pu/pl/{n}.m3u8"
    )
    dash_url = factory.Sequence(
        lambda n: f"https://video.twimg.com/ext_tw_video/{n}/pu/pl/{n}.mpd"
    )

    aspect_ratio = "16:9"
    duration = 20000

    image_file = factory.django.ImageField(filename="example.jpg")


class AnimatedGifFactory(MediaFactory):
    media_type = "animated_gif"

    image_url = factory.Sequence(
        lambda n: f"http://pbs.twimg.com/ext_tw_video_thumb/{n}/pu/img/{n}.jpg"
    )

    mp4_url = factory.Sequence(lambda n: f"https://pbs.twimg.com/tweet_video/{n}.mp4")

    aspect_ratio = "16:9"

    image_file = factory.django.ImageField(filename="example.jpg")
    mp4_file = factory.django.FileField(filename="example.mp4")
