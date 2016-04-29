from django.db import models


class PublicItemManager(models.Manager):
    """
    Only returns items that are public.
    Should be used on ALL public pages of the site.
    """
    def get_queryset(self):
        return super().get_queryset().filter(is_private=False)

