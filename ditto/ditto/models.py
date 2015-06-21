from django.db import models
from django.utils.encoding import python_2_unicode_compatible


class TimeStampedModel(models.Model):
    """
    Should be mixed in to all models.
    """
    time_created = models.DateTimeField(auto_now_add=True)
    time_modified = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


@python_2_unicode_compatible
class DittoItem(TimeStampedModel, models.Model):
    """
    An item on whatever service we're copying.
    eg, a Tweet, a Photo, a Bookmark, etc.

    Should be inherited by a model in child apps.
    eg, Tweet, Photo, Bookmark, etc.
    """
    title = models.CharField(null=False, blank=True, max_length=255)
    permalink = models.URLField(null=False, blank=True,
                    help_text="URL of the item on the service's website.")
    summary = models.TextField(null=False, blank=True,
                help_text="eg, First paragraph of a blog post, start of the description of a photo, all of a Tweet's text, etc.")
    is_private = models.BooleanField(default=False, null=False, blank=False,
                    help_text="If True, this item should NOT be shown on public-facing pages.")
    fetch_time = models.DateTimeField(null=True, blank=True,
                    help_text="The time the Raw data was last fetched.")
    raw = models.TextField(null=False, blank=True,
                    help_text="The raw JSON from the API.")

    class Meta:
        abstract = True

    def __str__(self):
        return self.title


