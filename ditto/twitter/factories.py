import factory

from . import models


class AccountFactory(factory.DjangoModelFactory):
    class Meta:
        model = models.Account

    screen_name = factory.Sequence(lambda n: 'user%d' % n)

