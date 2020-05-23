from django.db import models

from taggit.managers import _TaggableManager

from ..core.managers import PublicItemManager


class PhotosManager(models.Manager):
    """Returns public AND PRIVATE Photos posted by one of the Users with
    Accounts here.
    As opposed to just Photos, which includes Photos by any User that
    have been favorited by a User with an Account.
    """

    def get_queryset(self):
        from .models import User

        users = User.objects_with_accounts.all()
        return super().get_queryset().filter(user__in=users)


class PublicPhotosManager(PublicItemManager):
    """Returns public Photos posted by one of the Users with Accounts here.
    As opposed to just public Photos, which includes Photos by any User that
    have been favorited by a User with an Account.
    """

    def get_queryset(self):
        from .models import User

        users = User.objects_with_accounts.all()
        return super().get_queryset().filter(user__in=users)


class WithAccountsManager(models.Manager):
    "Returns Flickr Users who have an Account on Ditto."

    def get_queryset(self):
        from .models import Account

        accounts = Account.objects.exclude(user__isnull=True)
        user_ids = [account.user.id for account in accounts]
        return super().get_queryset().filter(pk__in=user_ids)


class _PhotoTaggableManager(_TaggableManager):
    """Providing some extra features related to private Photos."""

    def most_common(self):
        """Gets the most commonly-used tags but:
            * Doesn't count tags on private Photos
        Overriding django-taggit's standard `most_common()` method.
        """
        extra_filters = {
            "photo__is_private": False,
        }

        return (
            self.get_queryset(extra_filters)
            .annotate(num_times=models.Count(self.through.tag_relname()))
            .order_by("-num_times")
        )
