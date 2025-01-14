import datetime

import factory

from ditto.core.utils import datetime_now

from . import models


class AccountFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Account

    username = factory.Sequence(lambda n: f"user{n}")
    url = factory.LazyAttribute(lambda obj: f"https://pinboard.com/{obj.username}")
    api_token = factory.LazyAttribute(lambda obj: f"{obj.username}:123ABC")


class BookmarkFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Bookmark

    # DittoItem properties:
    title = factory.Sequence(lambda n: f"A Title {n}")
    is_private = False

    # Bookmark properties:
    account = factory.SubFactory(AccountFactory)
    url = factory.Sequence(lambda n: f"http://www.example.com/{n}")

    post_time = factory.LazyAttribute(
        lambda o: datetime_now() - datetime.timedelta(hours=1)
    )
    description = factory.Sequence(lambda n: f"A description of {n}")
    to_read = False

    # Leave tags empty by default.
