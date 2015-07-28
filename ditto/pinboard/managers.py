from django.db import models

from taggit.managers import _TaggableManager


class _BookmarkTaggableManager(_TaggableManager):
    """Providing some extra features related to private Bookmarks and tags."""

    def most_common(self):
        """Gets the most commonly-used tags but:
            * Doesn't count tags on private Bookmarks
            * Doesn't show tags that start with '.' (Pinboard's private tags)
        Overriding django-taggit's standard `most_common()` method.
        """
        extra_filters = {
            'bookmark__is_private': False,
        }

        return self.get_queryset(extra_filters).exclude(name__startswith='.').annotate(
            num_times=models.Count(self.through.tag_relname())
        ).order_by('-num_times')

    def all(self):
        """Overriding the default self.all() so we can exclude the private tags
        Pinboard uses, ie, tags that start with '.'.
        Use like `Bookmark.tags.all()`.
        """
        return self.get_queryset().exclude(name__startswith='.')

