# coding: utf-8
from django.core.validators import URLValidator
from django.db import models

from taggit.managers import TaggableManager
from taggit.models import GenericTaggedItemBase, TagBase

from .managers import _BookmarkTaggableManager, PublicToreadManager, ToreadManager
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
    is_active = models.BooleanField(default=True, null=False, blank=False,
                        help_text="If false, new Bookmarks won't be fetched.")

    def __str__(self):
        return self.username

    class Meta:
        ordering = ['username']

    def get_absolute_url(self):
        from django.core.urlresolvers import reverse
        return reverse('pinboard:account_detail', kwargs={'username': self.username})

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
    "Our custom version of a Taggit Tag model, for use with Bookmarks."

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
        """
        tag = tag.lower()
        tag = tag.replace('%', '%25')
        replace = {
                '#':    '%23',
                '&':    '%2526',
                "'":    '%27',
                '+':    '%252B',
                '/':    '%252f',
                '?':    '%3f',
                '"':    '%22',
                '<':    '%3C',
                '>':    '%3E',
                '\\':   '%5c',
                # These shouldn't be in the tag name, but just in case:
                ',':    '',
                ' ':    '-',
        }

        for f, r in replace.items():
            tag = tag.replace(f, r)

        if i is not None:
            tag += "_%d" % i

        return tag


class TaggedBookmark(TimeStampedModelMixin, GenericTaggedItemBase):
    tag = models.ForeignKey(BookmarkTag,
                            related_name="%(app_label)s_%(class)s_items")


class Bookmark(DittoItemModel, ExtraBookmarkManagers):
    account = models.ForeignKey(Account, null=False, blank=False)

    # `url` in the Pinboard API:
    url = models.TextField(null=False, blank=False,
                                                validators=[URLValidator()])

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
    tags = TaggableManager(manager=_BookmarkTaggableManager,
                                                        through=TaggedBookmark)

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

