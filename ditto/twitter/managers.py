from django.db import models


class PublicFavoritesManager(models.Manager):
    """
    Returns public Tweets favorited by any of the Accounts.
    """
    def get_queryset(self):
        from .models import User
        # All Users associated with Accounts:
        users = User.objects.filter(account__isnull=False)
        return super().get_queryset().filter(is_private=False).filter(favoriting_users__in=users).distinct()


class FavoritesManager(models.Manager):
    """
    Returns public AND PRIVATE Tweets favorited by any of the Accounts.
    """
    def get_queryset(self):
        from .models import User
        # All Users associated with Accounts:
        users = User.objects.filter(account__isnull=False)
        return super().get_queryset().filter(favoriting_users__in=users).distinct()

