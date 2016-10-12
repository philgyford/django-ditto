from django import template
from django.utils.html import format_html

from ..models import Account, Artist, Scrobble


register = template.Library()


@register.assignment_tag
def artist_top_tracks(artist=None, limit=10):
    """Returns a QuerySet of an Artist's most-scrobbled Tracks, with the
    most-scrobbled first.

    Keyword arguments:
    artist -- An Artist object.
    limit -- Maximum number to fetch. Default is 10. 'all' for all tracks.
    """
    if type(artist) is not Artist:
        raise ValueError("`artist` must be an Artist object")

    if limit != 'all' and isinstance(limit, int) == False:
        raise ValueError("`limit` must be an integer or 'all'")

    return artist.get_top_tracks(limit=limit)


@register.assignment_tag
def artist_top_albums(artist=None, limit=10):
    """Returns a QuerySet of an Artist's most-scrobbled Albums, with the
    most-scrobbled first.

    Keyword arguments:
    artist -- An Artist object.
    limit -- Maximum number to fetch. Default is 10. 'all' for all albums.
    """
    if type(artist) is not Artist:
        raise ValueError("`artist` must be an Artist object")

    if limit != 'all' and isinstance(limit, int) == False:
        raise ValueError("`limit` must be an integer or 'all'")

    return artist.get_top_albums(limit=limit)

@register.assignment_tag
def recent_scrobbles(account=None, limit=10):
    if isinstance(limit, int) == False:
        raise ValueError("`limit` must be an integer")

    if type(account) is Account:
        return account.get_recent_scrobbles(limit)
    else:
        return Scrobble.objects.all().order_by('-post_time')[:limit]

