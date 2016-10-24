from django import template
from django.db.models import Count
from django.db.models.functions import ExtractYear
from django.utils.html import format_html

from ..models import Account, Album, Artist, Scrobble, Track


register = template.Library()


@register.assignment_tag
def top_albums(account=None, artist=None, limit=10):
    """Returns a QuerySet of most-scrobbled Albums, with the most-scrobbled
    first.

    Restrict to Albums by one Artist by suppling the `artist`.
    Restrict to only one user's scrobbles by supplying the `account`.

    Keyword arguments:
    account -- An Account object or None (for Scrobbles by all Accounts).
    artist -- An Artist object or None.
    limit -- Maximum number to fetch. Default is 10. 'all' for all Albums.
    """
    if account is not None and not isinstance(account, Account):
        raise TypeError('account must be an Account instance, '
                        'not a %s' % type(account))

    if artist is not None and not isinstance(artist, Artist):
        raise TypeError('artist must be an Artist instance, '
                        'not a %s' % type(artist))

    if limit != 'all' and isinstance(limit, int) == False:
        raise ValueError("`limit` must be an integer or 'all'")


    qs_kwargs = {}

    if account:
        qs_kwargs['account'] = account

    if artist:
        qs_kwargs['artist'] = artist

    qs = Album.objects.with_scrobble_counts(**qs_kwargs)\
                        .order_by('-scrobble_count')

    if limit != 'all':
        qs = qs[:limit]

    return qs


@register.assignment_tag
def top_artists(account=None, limit=10):
    """Returns a QuerySet of the most-scrobbled Artists, with the
    most-scrobbled first.

    Restrict to only one user's scrobbles by supplying the `account`.

    Keyword arguments:
    account -- An Account object or None (for Scrobbles by all Accounts).
    limit -- Maximum number to fetch. Default is 10. 'all' for all Artists.
    """
    if account is not None and not isinstance(account, Account):
        raise TypeError('account must be an Account instance, '
                        'not a %s' % type(account))

    if limit != 'all' and isinstance(limit, int) == False:
        raise ValueError("`limit` must be an integer or 'all'")

    qs_kwargs = {}

    if account:
        qs_kwargs['account'] = account

    qs = Artist.objects.with_scrobble_counts(**qs_kwargs)\
                        .order_by('-scrobble_count')

    if limit != 'all':
        qs = qs[:limit]

    return qs


@register.assignment_tag
def top_tracks(account=None, artist=None, limit=10):
    """Returns a QuerySet of most-scrobbled Tracks, with the most-scrobbled
    first.

    Restrict to Tracks by one Artist by suppling the `artist`.
    Restrict to only one user's scrobbles by supplying the `account`.

    Keyword arguments:
    account -- An Account object or None (for Scrobbles by all Accounts).
    artist -- An Artist object or None.
    limit -- Maximum number to fetch. Default is 10. 'all' for all Tracks.
    """
    if account is not None and not isinstance(account, Account):
        raise TypeError('account must be an Account instance, '
                        'not a %s' % type(account))

    if artist is not None and type(artist) is not Artist:
        raise TypeError('artist must be an Artist instance, '
                        'not a %s' % type(artist))

    if limit != 'all' and isinstance(limit, int) == False:
        raise ValueError("`limit` must be an integer or 'all'")

    qs_kwargs = {}

    if account:
        qs_kwargs['account'] = account

    if artist:
        qs_kwargs['artist'] = artist

    qs = Track.objects.with_scrobble_counts(**qs_kwargs)\
                        .order_by('-scrobble_count')

    if limit != 'all':
        qs = qs[:limit]

    return qs


@register.assignment_tag
def recent_scrobbles(account=None, limit=10):
    """Returns a QuerySet of the most recent Scrobbles by all Accounts, or one,
    most recent first.

    Keyword arguments:
    account -- An Account object or None (for Scrobbles by all Accounts).
    limit -- Maximum number to fetch. Default is 10.
    """
    if account is not None and not isinstance(account, Account):
        raise TypeError('account must be an Account instance, '
                        'not a %s' % type(account))

    if isinstance(limit, int) == False:
        raise ValueError("`limit` must be an integer")

    if type(account) is Account:
        return account.get_recent_scrobbles(limit)
    else:
        return Scrobble.objects.all().order_by('-post_time')[:limit]


@register.assignment_tag
def annual_scrobble_counts(account=None):
    """
    Get the number of Scrobbles per year.
    Returns a list of dicts, sorted by year, like:
        [ {'year': 2015, 'count': 1234}, {'year': 2016, 'count': 9876} ]

    Keyword arguments:
    account -- An Account object or None (for Scrobbles by all Accounts).
    """

    if account is not None and not isinstance(account, Account):
        raise TypeError('account must be an Account instance, '
                        'not a %s' % type(account))

    qs = Scrobble.objects

    if account:
        qs = qs.filter(account=account)

    return qs.annotate(year=ExtractYear('post_time'))\
                .values('year')\
                .annotate(count=Count('id'))\
                .values('year', 'count')\
                .order_by('year')


