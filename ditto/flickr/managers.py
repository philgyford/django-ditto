from django.db import models

from ..ditto.managers import PublicItemManager


class PhotosManager(models.Manager):
    """Returns public AND PRIVATE Photos posted by one of the Users with
    Accounts here.
    As opposed to just Photos, which includes Photos by any User that
    have been favorited by a User with an Account.
    """
    def get_queryset(self):
        from .models import User
        users = User.objects_with_accounts.all()
        return super().get_queryset().filter(user=users)


class PublicPhotosManager(PublicItemManager):
    """Returns public Photos posted by one of the Users with Accounts here.
    As opposed to just public Photos, which includes Photos by any User that
    have been favorited by a User with an Account.
    """
    def get_queryset(self):
        from .models import User
        users = User.objects_with_accounts.all()
        return super().get_queryset().filter(user=users)


class WithAccountsManager(models.Manager):
    "Returns Flickr Users who have an Account on Ditto."

    def get_queryset(self):
        from .models import Account
        accounts = Account.objects.exclude(user__isnull=True)
        user_ids = [account.user.id for account in accounts]
        return super().get_queryset().filter(pk__in=user_ids)

