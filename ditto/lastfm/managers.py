from datetime import datetime

from django.db import models


class WithScrobbleCountsManager(models.Manager):
    """
    Adds a with_scrobble_counts() method.
    """

    def with_scrobble_counts(self, min_post_time=None, max_post_time=None):
        """
        Adds a `scrobble_count` field to the Queryset's objects.

        Include a `min_post_time` to only include Scrobbles after then.
        Include a `max_post_time` to only include Scrobbles before then.
        """
        if min_post_time and type(min_post_time) is not datetime:
            raise TypeError('min_post_time must be a datetime.datetime, '
                            'not a %s' % type(min_post_time))

        if max_post_time and type(max_post_time) is not datetime:
            raise TypeError('max_post_time must be a datetime.datetime, '
                            'not a %s' % type(max_post_time))

        qs = self

        if min_post_time and max_post_time:
            qs = qs.filter(scrobbles__post_time__gte=min_post_time,
                           scrobbles__post_time__lte=max_post_time)
        elif min_post_time:
            qs = qs.filter(scrobbles__post_time__gte=min_post_time)

        elif max_post_time:
            qs = qs.filter(scrobbles__post_time__lte=max_post_time)

        return qs.annotate(
                    scrobble_count=models.Count('scrobbles', distinct=True))


class TracksManager(WithScrobbleCountsManager):
    "Adds a `scrobble_count` field to the Track objects."
    pass


class AlbumsManager(WithScrobbleCountsManager):
    "Adds a `scrobble_count` field to the Album objects."
    pass


class ArtistsManager(WithScrobbleCountsManager):
    "Adds a `scrobble_count` field to the Album objects."
    pass

