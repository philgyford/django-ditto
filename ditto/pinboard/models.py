# coding: utf-8
from django.core.validators import URLValidator
from django.db import models

from taggit.managers import TaggableManager

from .managers import _BookmarkTaggableManager
from ditto.ditto.models import DittoItemModel, TimeStampedModelMixin


class Account(TimeStampedModelMixin, models.Model):
    username = models.CharField(null=False, blank=False, max_length=30,
                unique=True,
                help_text="eg, 'philgyford'")
    url = models.URLField(max_length=255, null=False, blank=False,
                unique=True,
                help_text="eg, 'https://pinboard.in/u:philgyford'")
    # max_length derived from DittoAccount.username max_length plus
    # 21 characters for ':12345...'.
    api_token = models.CharField(null=False, blank=False, max_length=51,
                    help_text='From https://pinboard.in/settings/password eg, "philgyford:1234567890ABCDEFGHIJ"')

    def __str__(self):
        return self.username

    class Meta:
        ordering = ['username']

    def get_absolute_url(self):
        from django.core.urlresolvers import reverse
        return reverse('pinboard:account_detail', kwargs={'username': self.username})


class Bookmark(DittoItemModel):
    account = models.ForeignKey(Account, null=False, blank=False)

    # `url` in the Pinboard API:
    url = models.TextField(null=False, blank=False,
                                                validators=[URLValidator()])

    # `time` in the Pinboard API:
    # Not required just in case the user adds a new bookmark in Django admin.
    post_time = models.DateTimeField(null=True, blank=True,
            help_text="The time this was created on Pinboard.")

    # `extended` in the Pinboard API:
    description = models.TextField(null=False, blank=True,
                    help_text="The 'extended' text description.")

    # `toread` in the Pinboard API:
    to_read = models.BooleanField(default=False, null=False, blank=False)

    # 'shared' in the Pinboard API is inverted and saved as
    # DittoItem::is_private.

    # Up to 100 tags
    # Up to 255 chars each. No commas or whitespace.
    # Private tags start with a period.
    tags = TaggableManager(manager=_BookmarkTaggableManager)

    class Meta:
        ordering = ['-post_time']
        unique_together = (('account', 'url'),)

    def get_absolute_url(self):
        from django.core.urlresolvers import reverse
        return reverse('pinboard:bookmark_detail',
                    kwargs={'username': self.account.username, 'pk': self.id})

    def summary_source(self):
        "The text that will be truncated to make a summary for this Bookmark"
        return self.description

    def slugs_match_tags(self, slugs):
        """Does a list of slugs equal the slugs of all this Bookmark's tags?
        Keyword arguments:
        slugs -- A list of slugs, eg ['carrot', 'pea']
        Returns boolean
        """
        return set(self.tags.slugs()) == set(slugs)

