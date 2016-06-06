import datetime
import pytz

from django import template

from ..models import Bookmark


register = template.Library()

@register.assignment_tag
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
    return bookmarks[:limit]

@register.assignment_tag
def day_bookmarks(date, account=None):
    """Returns a QuerySet of public Bookmarks posted on a specific date.

    Arguments:
    date -- A date object.

    Keyword arguments:
    account -- An account username, 'philgyford', or None to fetch for all.
    """
    start = datetime.datetime.combine(date, datetime.time.min).replace(
                                                            tzinfo=pytz.utc)
    end   = datetime.datetime.combine(date, datetime.time.max).replace(
                                                            tzinfo=pytz.utc)
    bookmarks = Bookmark.public_objects.filter(post_time__range=[start, end])
    if account is not None:
        bookmarks = bookmarks.filter(account__username=account)
    return bookmarks

