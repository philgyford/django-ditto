# coding: utf-8
from django.core.validators import URLValidator
from django.db import models
from django.utils.encoding import python_2_unicode_compatible

from ditto.ditto.models import DittoItemModel, TimeStampedModelMixin
from ditto.ditto.utils import truncate_string


@python_2_unicode_compatible
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
        return "%s: %s" % (self.service_name, self.username)

    @property
    def service_name(self):
      return "Pinboard"

    def get_absolute_url(self):
        from django.core.urlresolvers import reverse
        return reverse('account_detail', kwargs={'username': self.username})


class Bookmark(DittoItemModel):
    account = models.ForeignKey(Account, null=False, blank=False)

    # `url` in the Pinboard API:
    url = models.TextField(null=False, blank=False,
                                                validators=[URLValidator()])

    # `time` in the Pinboard API:
    post_time = models.DateTimeField(null=False, blank=False)

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
    # TODO tags

    class Meta:
        unique_together = (('account', 'url'),)

    def save(self, *args, **kwargs):
        self.summary = truncate_string(self.description, strip_html=True, chars=255, truncate=u'…', at_word_boundary=True)
        super(Bookmark, self).save(*args, **kwargs)

    def get_absolute_url(self):
        from django.core.urlresolvers import reverse
        return reverse('bookmark_detail',
                    kwargs={'username': self.account.username, 'pk': self.id})

