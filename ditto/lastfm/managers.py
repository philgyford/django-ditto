from datetime import datetime

from django.db import models


class WithScrobbleCountsManager(models.Manager):
    """
    Adds a with_scrobble_counts() method.
    """

    # Can we filter these (things) by Album?
    filterable_by_album = True

    # Can we filter these (things) by Artist?
    filterable_by_artist = True

    def with_scrobble_counts(self, **kwargs):
        """
        Adds a `scrobble_count` field to the Queryset's objects.

        eg:
            Track.objects.with_scrobble_counts()
        or:
            Track.objects.with_scrobble_counts(
                account         = my_account_obj,
                artist          = my_artist_obj,
                min_post_time   = my_datetime_obj_1,
                max_post_time   = my_datetime_obj_2,
            )
        or something in between.

        Include an `account` to only include Scrobbles by that Account.
        Include an `artist` to only include Scrobbles by that Artist.
        Include a `min_post_time` to only include Scrobbles after then.
        Include a `max_post_time` to only include Scrobbles before then.
        """
        account         = kwargs.get('account', None)
        min_post_time   = kwargs.get('min_post_time', None)
        max_post_time   = kwargs.get('max_post_time', None)
        album           = kwargs.get('album', None)
        artist          = kwargs.get('artist', None)

        if album and not self.filterable_by_album:
            raise ValueError('This is not filterable by album')

        if artist and not self.filterable_by_artist:
            raise ValueError('This is not filterable by artist')

        if account is not None and account.__class__.__name__ != 'Account':
            raise TypeError('account must be an Account instance, '
                            'not a %s' % type(account))

        if album is not None and album.__class__.__name__ != 'Album':
            raise TypeError('album must be an Album instance, '
                            'not a %s' % type(album))

        if artist is not None and artist.__class__.__name__ != 'Artist':
            raise TypeError('artist must be an Artist instance, '
                            'not a %s' % type(account))

        if min_post_time is not None and type(min_post_time) is not datetime:
            raise TypeError('min_post_time must be a datetime.datetime, '
                            'not a %s' % type(min_post_time))

        if max_post_time is not None and type(max_post_time) is not datetime:
            raise TypeError('max_post_time must be a datetime.datetime, '
                            'not a %s' % type(max_post_time))

        filter_kwargs = {}

        if account:
            filter_kwargs['scrobbles__account'] = account

        if album:
            filter_kwargs['scrobbles__album'] = album

        if artist:
            filter_kwargs['scrobbles__artist'] = artist

        if min_post_time and max_post_time:
            filter_kwargs['scrobbles__post_time__gte'] = min_post_time
            filter_kwargs['scrobbles__post_time__lte'] = max_post_time

        elif min_post_time:
            filter_kwargs['scrobbles__post_time__gte'] = min_post_time

        elif max_post_time:
            filter_kwargs['scrobbles__post_time__lte'] = max_post_time

        qs = self.filter(**filter_kwargs)

        return qs.annotate(
                scrobble_count = models.Count('scrobbles', distinct=True)
            )


class TracksManager(WithScrobbleCountsManager):
    "Adds a `scrobble_count` field to the Track objects."
    pass


class AlbumsManager(WithScrobbleCountsManager):
    "Adds a `scrobble_count` field to the Album objects."

    # Obviously, we can't filter a list of Albums by Album.
    filterable_by_album = False


class ArtistsManager(WithScrobbleCountsManager):
    "Adds a `scrobble_count` field to the Artist objects."

    # Obviously, we can't filter a list of Artists by Artist.
    filterable_by_artist = False

