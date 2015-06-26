from django.core.validators import URLValidator
from django.db import models
from django.utils.encoding import python_2_unicode_compatible

from ditto.ditto.models import DittoItem, TimeStampedModel


@python_2_unicode_compatible
class Account(TimeStampedModel, models.Model):
    username = models.CharField(null=False, blank=False, max_length=30,
                unique=True,
                help_text="eg, 'philgyford'")
    url = models.URLField(max_length=255, null=False, blank=False,
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


class Bookmark(DittoItem):
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
        # TODO: May want to trim the description.
        self.summary = self.description
        super(Bookmark, self).save(*args, **kwargs)

    def get_absolute_url(self):
        from django.core.urlresolvers import reverse
        return reverse('bookmark_detail', kwargs={'pk': self.id})

