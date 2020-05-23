import datetime
import pytz

from django import template

from ..models import Bookmark
from ...core.utils import get_annual_item_counts


register = template.Library()


@register.simple_tag
def recent_bookmarks(account=None, limit=10):
    """Returns a QuerySet of recent public Bookmarks, in reverse-chronological
    order.

    Keyword arguments:
    account -- An account username, 'philgyford', or None to fetch for all.
    limit -- Maximum number to fetch. Default is 10.
    """
    bookmarks = Bookmark.public_objects.all()
    if account is not None:
        bookmarks = bookmarks.filter(account__username=account)
    bookmarks = bookmarks.prefetch_related("account")
    return bookmarks[:limit]


@register.simple_tag
def day_bookmarks(date, account=None):
    """Returns a QuerySet of public Bookmarks posted on a specific date.

    Arguments:
    date -- A date object.

    Keyword arguments:
    account -- An account username, 'philgyford', or None to fetch for all.
    """
    start = datetime.datetime.combine(date, datetime.time.min).replace(tzinfo=pytz.utc)
    end = datetime.datetime.combine(date, datetime.time.max).replace(tzinfo=pytz.utc)
    bookmarks = Bookmark.public_objects.filter(post_time__range=[start, end])
    if account is not None:
        bookmarks = bookmarks.filter(account__username=account)
    bookmarks = bookmarks.prefetch_related("account")
    return bookmarks


@register.simple_tag
def annual_bookmark_counts(account=None):
    """
    Get the number of public Bookmarks per year.
    Returns a list of dicts, sorted by year, like:
        [ {'year': 2015, 'count': 1234}, {'year': 2016, 'count': 9876} ]

    Keyword arguments:
    account -- An account username, 'philgyford', or None to fetch for all.
    """
    bookmarks = Bookmark.public_objects

    if account:
        bookmarks = bookmarks.filter(account__username=account)

    return get_annual_item_counts(bookmarks)


@register.simple_tag
def popular_bookmark_tags(limit=10):
    return Bookmark.tags.most_common()[:limit]
