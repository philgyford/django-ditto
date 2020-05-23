# coding: utf-8
from django.db import models
from django.forms.models import model_to_dict

from .managers import PublicItemManager
from .utils import truncate_string


class TimeStampedModelMixin(models.Model):
    "Should be mixed in to all models."
    time_created = models.DateTimeField(
        auto_now_add=True, help_text="The time this item was created in the database."
    )
    time_modified = models.DateTimeField(
        auto_now=True, help_text="The time this item was last saved to the database."
    )

    class Meta:
        abstract = True


class DiffModelMixin(object):
    """A model mixin that tracks model fields' values and provide some useful
    api to know what fields have been changed.

    eg:
    Get an object from the database.
    Set some of its properties.
    Call `myObj.has_changed` to see if any fields are different to in the DB.

    From http://stackoverflow.com/a/13842223/250962
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__initial = self._dict

    @property
    def diff(self):
        """Returns a dict of properties that have changed, with values a list
        of before/after changes. eg:
        `{'categories': (None, [1, 3, 5]), 'rank': (0, 42)}`
        """
        d1 = self.__initial
        d2 = self._dict
        diffs = [(k, (v, d2[k])) for k, v in d1.items() if v != d2[k]]
        return dict(diffs)

    @property
    def has_changed(self):
        "Returns True if any of the properties have changed."
        return bool(self.diff)

    @property
    def changed_fields(self):
        "Returns a list of property names for any that have changed."
        return self.diff.keys()

    def get_field_diff(self, field_name):
        "Returns a diff for field if it's changed and None otherwise."
        return self.diff.get(field_name, None)

    def save(self, *args, **kwargs):
        "Saves model and set initial state."
        super().save(*args, **kwargs)
        self.__initial = self._dict

    @property
    def _dict(self):
        return model_to_dict(self, fields=[field.name for field in self._meta.fields])


class DittoItemModel(TimeStampedModelMixin, DiffModelMixin, models.Model):
    """
    A content item on whatever service we're copying.
    eg, a Tweet, a Photo, a Bookmark, etc.

    Should be inherited by a model in child apps.
    eg, Tweet, Photo, Bookmark, etc.
    """

    # Should be overridden for child classes.
    # eg, 'flickr_photo', 'twitter_tweet', etc.
    # Used in templates.
    ditto_item_name = "set__ditto_item_name__in_child_class"

    title = models.CharField(blank=True, max_length=255)
    permalink = models.URLField(
        blank=True, help_text="URL of the item on the service's website."
    )
    # Ensures that all children have a common short piece of text for display:
    summary = models.CharField(
        blank=True,
        max_length=255,
        help_text=(
            "eg, Brief summary or excerpt of item's text content. "
            "No linebreaks or HTML."
        ),
    )
    is_private = models.BooleanField(
        default=False,
        help_text="If true, this item will not be shown on public-facing pages.",
    )
    fetch_time = models.DateTimeField(
        null=True, blank=True, help_text="The time the item's data was last fetched."
    )

    post_time = models.DateTimeField(
        null=True,
        blank=True,
        db_index=True,
        help_text="The time the item was originally posted/created on its service.",
    )
    post_year = models.PositiveSmallIntegerField(
        null=True, blank=True, db_index=True, help_text="Set automatically on save"
    )

    # Obviously not relevant to some items, like Bookmarks.
    latitude = models.DecimalField(
        null=True, blank=True, max_digits=9, decimal_places=6
    )
    longitude = models.DecimalField(
        null=True, blank=True, max_digits=9, decimal_places=6
    )

    raw = models.TextField(blank=True, help_text="eg, the raw JSON from the API.")

    # All Items (eg, used in Admin):
    objects = models.Manager()

    # All Items which aren't private. Should ALWAYS be used for public pages:
    public_objects = PublicItemManager()

    class Meta:
        abstract = True
        get_latest_by = "post_time"

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        self.summary = self._make_summary()
        if self.post_time:
            self.post_year = self.post_time.year
        else:
            self.post_year = None
        super().save(*args, **kwargs)

    def _summary_source(self):
        """
        Child classes can return a string that's used to make the truncated,
        HTML-free `summary`.
        e.g.:
            return self.description
        """
        return ""

    def _make_summary(self):
        """
        Returns the string to be used for the `summary` property.
        """
        return (
            truncate_string(
                self._summary_source(),
                strip_html=True,
                chars=255,
                truncate="…",
                at_word_boundary=True,
            )
            .replace("\n", " ")
            .replace("\r", " ")
        )
