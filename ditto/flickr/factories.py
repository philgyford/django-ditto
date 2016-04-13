import datetime
import pytz
import factory

from . import models
from ..ditto.utils import datetime_now


class UserFactory(factory.DjangoModelFactory):
    class Meta:
        model = models.User

    nsid = factory.Sequence(lambda n: (n * 10000))
    username = factory.Sequence(lambda n: 'user%d' % n)
    realname = factory.Sequence(lambda n: 'User Name %d' % n)
    iconserver = 1234
    iconfarm = 5
    timezone_id = 'America/Los_Angeles'
    photos_url = factory.Sequence(
                        lambda n: 'https://www.flickr.com/photos/user%d/' % n)

    photos_first_date = factory.LazyAttribute(lambda o:
                               datetime_now() - datetime.timedelta(weeks=52)
                            )
    photos_first_date_taken = factory.LazyAttribute(lambda o:
                                datetime_now() - datetime.timedelta(weeks=52)
                            )
    fetch_time = datetime_now()


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
    post_time = datetime_now()




