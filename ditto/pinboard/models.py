# coding: utf-8
import hashlib
from django.core.validators import URLValidator
from django.db import models

from taggit.managers import TaggableManager
from taggit.models import GenericTaggedItemBase, TagBase

from .managers import _BookmarkTaggableManager, PublicToreadManager, ToreadManager
from ..core.models import DittoItemModel, TimeStampedModelMixin


class Account(TimeStampedModelMixin, models.Model):
    username = models.CharField(
        null=False,
        blank=False,
        max_length=30,
        unique=True,
        help_text="eg, 'philgyford'",
    )
    url = models.URLField(
        max_length=255,
        null=False,
        blank=False,
        unique=True,
        verbose_name="URL",
        help_text="eg, 'https://pinboard.in/u:philgyford'",
    )
    # max_length derived from DittoAccount.username max_length plus
    # 21 characters for ':12345...'.
    api_token = models.CharField(
        null=False,
        blank=False,
        max_length=51,
        verbose_name="API Token",
        help_text='eg, "philgyford:1234567890ABCDEFGHIJ"',
    )
    is_active = models.BooleanField(
        default=True,
        null=False,
        blank=False,
        help_text="If false, new Bookmarks won't be fetched.",
    )

    def __str__(self):
        return self.username

    class Meta:
        ordering = ["username"]

    def get_absolute_url(self):
        from django.urls import reverse

        return reverse("pinboard:account_detail", kwargs={"username": self.username})

    @property
    def public_bookmarks_count(self):
        return Bookmark.public_objects.count()


class ExtraBookmarkManagers(models.Model):
    """Managers to use in the Bookmark model, in addition to the defaults
    defined in DittoItemModel.
    These need to be here, rather than in the Pinboard model, or they will
    override those in DittoItemModel.
    """

    toread_objects = ToreadManager()
    public_toread_objects = PublicToreadManager()

    class Meta:
        abstract = True


class BookmarkTag(TimeStampedModelMixin, TagBase):
    """Our custom version of a Taggit Tag model, for use with Bookmarks.

    NOTE: If you create two tags in Pinboard, with names "dog" and "DOG",
    they will both get the slug "dog". Taggit doesn't work like that by
    default, as both Name and Slug are unique. So the second of those
    tags that you create will have a slug of "dog_1". Not sure how best to fix
    that, if at all.
    """

    class Meta:
        verbose_name = "Tag"
        verbose_name_plural = "Tags"

    def slugify(self, tag, i=None):
        """Pinboard's slugs for tags don't encode many things. Most unicode
        characters are allowed as-is, and only a few special characters
        are URL encoded. This may not be an exhaustive list.

        We also lowercase the slugs. Which isn't exactly what Pinboard does,
        but it makes it much easier for us to show related Bookmarks, no matter
        if they're tagged with 'Fish' or 'fish'.

        This is inherited from TagBase.

        `tag` is a string, like 'mytag'
        `i` is either None or an integer, which signifies how many times the
            slug for this tag has been attempted to be calculated, it is None
            on the first time, and the counting begins at 1 thereafter.
        """
        tag = tag.lower()
        tag = tag.replace("%", "%25")
        replace = {
            "#": "%23",
            "&": "%2526",
            "'": "%27",
            "+": "%252B",
            "/": "%252f",
            "?": "%3f",
            '"': "%22",
            "<": "%3C",
            ">": "%3E",
            "\\": "%5c",
            # These shouldn't be in the tag name, but just in case:
            ",": "",
            " ": "-",
        }

        for f, r in replace.items():
            tag = tag.replace(f, r)

        # So if you slugify "dog" for one tag and then "DOG" for another,
        # the first will have a slug of "dog" and the second will have "dog_1".

        if i is not None:
            tag += "_%d" % i

        return tag


class TaggedBookmark(TimeStampedModelMixin, GenericTaggedItemBase):
    tag = models.ForeignKey(
        BookmarkTag,
        on_delete=models.CASCADE,
        related_name="%(app_label)s_%(class)s_items",
    )


class Bookmark(DittoItemModel, ExtraBookmarkManagers):

    ditto_item_name = "pinboard_bookmark"

    # Properties inherited from DittoItemModel:
    #
    # title         (CharField)
    # permalink     (URLField)
    # summary       (CharField)
    # is_private    (BooleanField)
    # fetch_time    (DateTimeField, UTC)
    # post_time     (DateTimeField, UTC)
    # latitude      (DecimalField)
    # longitude     (DecimalField)
    # raw           (TextField)

    account = models.ForeignKey(
        Account, on_delete=models.CASCADE, null=False, blank=False
    )

    # `url` in the Pinboard API:
    url = models.TextField(null=False, blank=False, validators=[URLValidator()])

    # `extended` in the Pinboard API:
    description = models.TextField(
        null=False, blank=True, help_text="The 'extended' text description."
    )

    # `toread` in the Pinboard API:
    to_read = models.BooleanField(default=False, null=False, blank=False)

    # 'shared' in the Pinboard API is inverted and saved as
    # DittoItem::is_private.

    # Pinboard usese some kind of hash for each individual URL, but these
    # don't come back via the API. So we'll make our own (in self.save()).
    url_hash = models.CharField(
        null=False,
        blank=True,
        max_length=12,
        db_index=True,
        help_text="Slug in the Bookmark's local URL.",
    )

    # Up to 100 tags
    # Up to 255 chars each. No commas or whitespace.
    # Private tags start with a period.
    tags = TaggableManager(manager=_BookmarkTaggableManager, through=TaggedBookmark)

    class Meta:
        ordering = ["-post_time"]
        unique_together = (("account", "url"),)

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        """Create a url_hash for this bookmark if it doesn't have one.
        This is not the best ever way to do this. For one, there's a very slim
        chance of clashes. But it seems good enough for now.
        """
        if not self.url_hash:
            self.url_hash = hashlib.md5(self.url.encode("utf-8")).hexdigest()[:12]
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        from django.urls import reverse

        return reverse(
            "pinboard:bookmark_detail",
            kwargs={"username": self.account.username, "hash": self.url_hash},
        )

    def get_next_public_by_post_time(self):
        "The next public Bookmark by this Account, ordered by post_time."
        try:
            return (
                Bookmark.public_objects.filter(
                    post_time__gte=self.post_time, account=self.account
                )
                .exclude(pk=self.pk)
                .order_by("post_time")[:1]
                .get()
            )
        except Exception:
            pass

    def get_previous_public_by_post_time(self):
        "The previous public Bookmark by this Account, ordered by post_time."
        try:
            return (
                Bookmark.public_objects.filter(
                    post_time__lte=self.post_time, account=self.account
                )
                .exclude(pk=self.pk)
                .order_by("-post_time")[:1]
                .get()
            )
        except Exception:
            pass

    # Shortcuts:
    def get_next(self):
        return self.get_next_public_by_post_time()

    def get_previous(self):
        return self.get_previous_public_by_post_time()

    def slugs_match_tags(self, slugs):
        """Does a list of slugs equal the slugs of all this Bookmark's tags?
        Keyword arguments:
        slugs -- A list of slugs, eg ['carrot', 'pea']
        Returns boolean
        """
        return set(self.tags.slugs()) == set(slugs)

    def _summary_source(self):
        "Used to make the `summary` property."
        return self.description
