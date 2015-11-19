from django.db import models


class WithAccountsManager(models.Manager):
    "Returns Flickr Users who have an Account on Ditto."

    def get_queryset(self):
        from .models import Account
        accounts = Account.objects.exclude(user__isnull=True)
        user_ids = [account.user.id for account in accounts]
        return super().get_queryset().filter(pk__in=user_ids)

