import factory

from . import models


class AccountFactory(factory.Factory):
    class Meta:
        model = models.Account

    username = factory.Sequence(lambda n: 'user%d' % n)
    url = factory.LazyAttribute(lambda obj: 'https://pinboard.com/%s' %
                                                                obj.username)
    api_token = factory.LazyAttribute(lambda obj: '%s:123ABC' % obj.username)


