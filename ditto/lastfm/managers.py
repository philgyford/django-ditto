from django.db import models


class TracksManager(models.Manager):
    """
    Adds a `scrobble_count` field to the Track objects.
    """
    def with_scrobble_counts(self):
        return self.annotate(scrobble_count=models.Count('scrobbles'))


class AlbumsManager(models.Manager):
    """
    Adds a `scrobble_count` field to the Album objects.
    """
    def with_scrobble_counts(self):
        return self.annotate(scrobble_count=models.Count('scrobbles'))


class ArtistsManager(models.Manager):
    """
    Adds a `scrobble_count` field to the Album objects.
    """
    def with_scrobble_counts(self):
        return self.annotate(scrobble_count=models.Count('scrobbles'))

