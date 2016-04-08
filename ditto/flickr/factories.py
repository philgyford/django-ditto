import datetime
import pytz
import factory

from . import models


class UserFactory(factory.DjangoModelFactory):
    class Meta:
        model = models.User

    nsid = factory.Sequence(lambda n: (n * 10000))
    username = factory.Sequence(lambda n: 'user%d' % n)
    realname = factory.Sequence(lambda n: 'User Name %d' % n)
    iconserver = '1234'
    iconfarm = 5
    timezone_id = 'America/Los_Angeles'

    photos_first_date = factory.LazyAttribute(lambda o:
                        datetime.datetime.utcnow().replace(tzinfo=pytz.utc)
                        - datetime.timedelta(weeks=52)
                    )
    photos_first_date_taken = factory.LazyAttribute(lambda o:
                        datetime.datetime.utcnow().replace(tzinfo=pytz.utc)
                        - datetime.timedelta(weeks=52)
                    )


class AccountFactory(factory.DjangoModelFactory):
    class Meta:
        model = models.Account

    user = factory.SubFactory(UserFactory,
            username=factory.Sequence(lambda n: n),
            realname=factory.Sequence(lambda n: 'User Name %d' % n)
        )


class PhotoFactory(factory.DjangoModelFactory):
    class Meta:
        model = models.Photo

    user = factory.SubFactory(UserFactory,
            username=factory.Sequence(lambda n: n),
            realname=factory.Sequence(lambda n: 'User Name %d' % n)
        )

    flickr_id = factory.Sequence(lambda n: (n * 1000000))
    title = factory.Sequence(lambda n: 'Photo %d' % n)
    secret = factory.Sequence(lambda n: (n * 10000))
    original_secret = factory.Sequence(lambda n: (n * 10001))
    server = '987'
    farm = 2




