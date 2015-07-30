import datetime
import pytz
import factory

from . import models


class UserFactory(factory.DjangoModelFactory):
    class Meta:
        model = models.User

    twitter_id = factory.Sequence(lambda n: (n * 10000))
    twitter_id_str = factory.LazyAttribute(lambda obj: '%s' % obj.twitter_id)

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
            twitter_id_str=factory.Sequence(lambda n: '%d' % n),
            screen_name=factory.Sequence(lambda n: 'user%d' % n)
        )


class TweetFactory(factory.DjangoModelFactory):

    class Meta:
        model = models.Tweet

    user = factory.SubFactory(UserFactory)
    text = factory.Sequence(lambda n: 'The text of tweet %d' % n)
    twitter_id = factory.Sequence(lambda n: (n * 10000000))
    twitter_id_str = factory.LazyAttribute(lambda obj: '%s' % obj.twitter_id)

    created_at = factory.LazyAttribute(lambda o:
                        datetime.datetime.utcnow().replace(tzinfo=pytz.utc)
                        - datetime.timedelta(weeks=4)
                    )
    source = 'web'


