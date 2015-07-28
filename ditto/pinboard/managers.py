from django.db import models

from taggit.managers import _TaggableManager


class _BookmarkTaggableManager(_TaggableManager):

    def most_common_public(self):
        extra_filters = {'bookmark__is_private': False}
        return self.get_queryset(extra_filters).annotate(
            num_times=models.Count(self.through.tag_relname())
        ).order_by('-num_times')

