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
class DittoAccount(TimeStampedModel, models.Model):
    """
    A user account on a service.
    eg, The 'philgyford' account on Twitter.

    Should be inherited by an Account model in child apps.
    That child model should have a property that returns a service_name:
        @property
        def service_name(self):
            return "Twitter"
    """
    username = models.CharField(null=False, blank=False, max_length=30,
                help_text="eg, 'philgyford'")
    url = models.URLField(max_length=255, null=False, blank=False,
                help_text="eg, 'https://twitter.com/philgyford'")

    class Meta:
        abstract = True

    def __str__(self):
        return "%s: %s" % (self.service_name, self.username)

    @property
    def service_name(self):
        return "[No service name set]"


@python_2_unicode_compatible
class DittoItem(TimeStampedModel, models.Model):
    """
    An item on whatever service we're copying.
    eg, a Tweet, a Photo, a Bookmark, etc.

    Should be inherited by a model in child apps.
    eg, Tweet, Photo, Bookmark, etc.
    """
    title = models.CharField(null=False, blank=False, max_length=255)
    permalink = models.URLField(null=False, blank=False,
                    help_text="URL of the item itself.")
    summary = models.TextField(null=False, blank=True,
                help_text="eg, First paragraph of a blog post, start of the description of a photo, all of a Tweet's text, etc")
    is_private = models.BooleanField(default=False, null=False, blank=False,
                    help_text="If True, this item should NOT be shown on public-facing pages.")

    class Meta:
        abstract = True

    def __str__(self):
        return self.title


