from django import template
from django.db import models
from django.utils.html import format_html

from ..models import Account, Album, Artist, Scrobble, Track


register = template.Library()


@register.assignment_tag
def top_tracks(artist=None, limit=10):
    """Returns a QuerySet of most-scrobbled Tracks, with the most-scrobbled
    first.

    Restrict to Tracks by one Artist by suppling the `artist`.

    Keyword arguments:
    artist -- An Artist object or None.
    limit -- Maximum number to fetch. Default is 10. 'all' for all Tracks.
    """
    if type(artist) is not Artist and artist is not None:
        raise ValueError("`artist` must be an Artist object or `None`")

    if limit != 'all' and isinstance(limit, int) == False:
        raise ValueError("`limit` must be an integer or 'all'")

    if artist is None:
        qs = Track.objects.with_scrobble_counts().order_by('-scrobble_count')
        if limit != 'all':
            qs = qs[:limit]
    else:
        qs = artist.get_top_tracks(limit=limit)

    return qs


@register.assignment_tag
def top_albums(artist=None, limit=10):
    """Returns a QuerySet of most-scrobbled Albums, with the most-scrobbled
    first.

    Restrict to Albums by one Artist by suppling the `artist`.

    Keyword arguments:
    artist -- An Artist object or None.
    limit -- Maximum number to fetch. Default is 10. 'all' for all Albums.
    """
    if type(artist) is not Artist and artist is not None:
        raise ValueError("`artist` must be an Artist object or `None`")

    if limit != 'all' and isinstance(limit, int) == False:
        raise ValueError("`limit` must be an integer or 'all'")

    if artist is None:
        qs = Album.objects.with_scrobble_counts().order_by('-scrobble_count')
        if limit != 'all':
            qs = qs[:limit]
    else:
        qs = artist.get_top_albums(limit=limit)

    return qs


@register.assignment_tag
def recent_scrobbles(account=None, limit=10):
    if isinstance(limit, int) == False:
        raise ValueError("`limit` must be an integer")

    if type(account) is Account:
        return account.get_recent_scrobbles(limit)
    else:
        return Scrobble.objects.all().order_by('-post_time')[:limit]

