import datetime
import pytz
import factory

from . import models


class UserFactory(factory.DjangoModelFactory):
    class Meta:
        model = models.User

    twitter_id = factory.Sequence(lambda n: (n * 10000))
    screen_name = factory.Sequence(lambda n: 'user%d' % n)
    name = factory.Sequence(lambda n: 'User Name %d' % n)

    created_at = factory.LazyAttribute(lambda o:
                        datetime.datetime.utcnow().replace(tzinfo=pytz.utc)
                        - datetime.timedelta(weeks=52)
                    )

    description = factory.Sequence(lambda n: 'A description %d' % n)
    is_private = False


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

    created_at = factory.LazyAttribute(lambda o:
                        datetime.datetime.utcnow().replace(tzinfo=pytz.utc)
                        - datetime.timedelta(weeks=4)
                    )
    source = 'web'


class PhotoFactory(factory.DjangoModelFactory):

    class Meta:
        model = models.Photo

    tweet = factory.SubFactory(TweetFactory)
    twitter_id = factory.Sequence(lambda n: (n * 10000000))
    url = factory.Sequence(lambda n: 'http://pbs.twimg.com/media/%d.jpg' % n)
    large_w = 938
    large_h = 397
    medium_w = 600
    medium_h = 253
    small_w = 340
    small_h = 143
    thumb_w = 150
    thumb_h = 150

