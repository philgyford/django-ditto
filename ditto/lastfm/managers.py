from datetime import datetime

from django.db import models


class WithScrobbleCountsManager(models.Manager):
    """
    Adds a with_scrobble_counts() method.
    """

    # Can we filter these (things) by Album?
    is_filterable_by_album = True

    # Can we filter these (things) by Artist?
    is_filterable_by_artist = True

    # Can we filter these (things) by Track?
    is_filterable_by_track = True

    def with_scrobble_counts(self, **kwargs):
        """
        Adds a `scrobble_count` field to the Queryset's objects, and
        orders the results by that, descending.

        eg:
            # All Tracks, each with a scrobble_count:
            Track.objects.with_scrobble_counts()

            # All Albums, each with a total scrobble_count:
            Album.objects.with_scrobble_counts()

            # All Artists, each with a total scrobble_count:
            Artist.objects.with_scrobble_counts()

            # Tracks by artist_obj:
            Track.objects.with_scrobble_counts(artist=artist_obj)

            # Tracks appearing on album_obj:
            Track.objects.with_scrobble_counts(album=album_obj)

            # Albums on which track_obj appears:
            Album.objects.with_scrobble_counts(track=track_obj)

        or combine filters:

            # Tracks by artist_obj, scrobbled by account_obj between
            # datetime_obj_1 and datetime_obj2:
            Track.objects.with_scrobble_counts(
                account         = account_obj,
                artist          = artist_obj,
                min_post_time   = datetime_obj_1,
                max_post_time   = datetime_obj_2,
            )

        Include an `account` to only include Scrobbles by that Account.
        Include an `album` to only include Scrobbles on that Album.
        Include an `artist` to only include Scrobbles by that Artist.
        Include a `track` to only include Scrobbles including that Track.
        Include a `min_post_time` to only include Scrobbles after then.
        Include a `max_post_time` to only include Scrobbles before then.
        """
        account = kwargs.get("account", None)
        min_post_time = kwargs.get("min_post_time", None)
        max_post_time = kwargs.get("max_post_time", None)
        album = kwargs.get("album", None)
        artist = kwargs.get("artist", None)
        track = kwargs.get("track", None)

        if album and not self.is_filterable_by_album:
            raise ValueError("This is not filterable by album")

        if artist and not self.is_filterable_by_artist:
            raise ValueError("This is not filterable by artist")

        if track and not self.is_filterable_by_track:
            raise ValueError("This is not filterable by track")

        if account is not None and account.__class__.__name__ != "Account":
            raise TypeError(
                "account must be an Account instance, " "not a %s" % type(account)
            )

        if album is not None and album.__class__.__name__ != "Album":
            raise TypeError(
                "album must be an Album instance, " "not a %s" % type(album)
            )

        if artist is not None and artist.__class__.__name__ != "Artist":
            raise TypeError(
                "artist must be an Artist instance, " "not a %s" % type(account)
            )

        if min_post_time is not None and type(min_post_time) is not datetime:
            raise TypeError(
                "min_post_time must be a datetime.datetime, "
                "not a %s" % type(min_post_time)
            )

        if max_post_time is not None and type(max_post_time) is not datetime:
            raise TypeError(
                "max_post_time must be a datetime.datetime, "
                "not a %s" % type(max_post_time)
            )

        filter_kwargs = {}

        if account:
            filter_kwargs["scrobbles__account"] = account

        if album:
            filter_kwargs["scrobbles__album"] = album

        if artist:
            filter_kwargs["scrobbles__artist"] = artist

        if track:
            filter_kwargs["scrobbles__track"] = track

        if min_post_time and max_post_time:
            filter_kwargs["scrobbles__post_time__gte"] = min_post_time
            filter_kwargs["scrobbles__post_time__lte"] = max_post_time

        elif min_post_time:
            filter_kwargs["scrobbles__post_time__gte"] = min_post_time

        elif max_post_time:
            filter_kwargs["scrobbles__post_time__lte"] = max_post_time

        qs = self.filter(**filter_kwargs)

        return qs.annotate(
            scrobble_count=models.Count("scrobbles", distinct=True)
        ).order_by("-scrobble_count")


class TracksManager(WithScrobbleCountsManager):
    """
    Adds a `scrobble_count` field to the Track objects.
    See WithScrobbleCountsManager for docs.
    """

    # We can't filter a list of Tracks by Tracks.
    is_filterable_by_track = False

    def with_scrobble_counts(self, **kwargs):
        "Pre-fetch all the Tracks' Artists."
        qs = (
            super(TracksManager, self)
            .with_scrobble_counts(**kwargs)
            .prefetch_related("artist")
        )
        return qs


class AlbumsManager(WithScrobbleCountsManager):
    """
    Adds a `scrobble_count` field to the Album objects.
    See WithScrobbleCountsManager for docs.
    """

    # We can't filter a list of Albums by Album.
    is_filterable_by_album = False

    def with_scrobble_counts(self, **kwargs):
        "Pre-fetch all the Albums' Artists."
        qs = (
            super(AlbumsManager, self)
            .with_scrobble_counts(**kwargs)
            .prefetch_related("artist")
        )
        return qs


class ArtistsManager(WithScrobbleCountsManager):
    """
    Adds a `scrobble_count` field to the Artist objects.
    See WithScrobbleCountsManager for docs.
    """

    # We can't filter a list of Artists by Artist.
    is_filterable_by_artist = False
