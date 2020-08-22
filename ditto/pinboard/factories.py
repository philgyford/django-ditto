import datetime
import factory

from . import models
from ..core.utils import datetime_now


class AccountFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Account

    username = factory.Sequence(lambda n: "user%d" % n)
    url = factory.LazyAttribute(lambda obj: "https://pinboard.com/%s" % obj.username)
    api_token = factory.LazyAttribute(lambda obj: "%s:123ABC" % obj.username)


class BookmarkFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Bookmark

    # DittoItem properties:
    title = factory.Sequence(lambda n: "A Title %d" % n)
    is_private = False

    # Bookmark properties:
    account = factory.SubFactory(AccountFactory)
    url = factory.Sequence(lambda n: "http://www.example.com/%d" % n)

    post_time = factory.LazyAttribute(
        lambda o: datetime_now() - datetime.timedelta(hours=1)
    )
    description = factory.Sequence(lambda n: "A description of %d" % n)
    to_read = False

    # Leave tags empty by default.
