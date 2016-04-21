import datetime
import pytz

from django import template

from ..models import Photo, User
from ...ditto.templatetags.ditto import display_time


register = template.Library()


@register.assignment_tag
def recent_photos(nsid=None, limit=10):
    """Returns a QuerySet of recent public Photos, in reverse-chronological
    order.

    Keyword arguments:
    nsid -- A Flickr user's NSID. If not supplied, we fetch
                    Photos for all Flickr users that have Accounts.
    limit -- Maximum number to fetch. Default is 10.
    """
    if nsid is None:
        users = User.objects_with_accounts.all()
        photos = Photo.public_objects.filter(user=users)
    else:
        photos = Photo.public_objects.filter(user__nsid=nsid)
    return photos.select_related()[:limit]

@register.assignment_tag
def day_photos(date, nsid=None):
    """Returns a QuerySet of public Photos posted on a specific date.

    Arguments:
    date -- A date object.

    Keyword arguments:
    nsid -- A Flickr user's NSID. If not supplied, we fetch
                    Photos for all Flickr users that have Accounts.
    """
    start = datetime.datetime.combine(date, datetime.time.min).replace(
                                                            tzinfo=pytz.utc)
    end   = datetime.datetime.combine(date, datetime.time.max).replace(
                                                            tzinfo=pytz.utc)
    photos = Photo.public_objects.filter(post_time__range=[start, end])
    if nsid is None:
        users = User.objects_with_accounts.all()
        photos = photos.filter(user=users)
    else:
        photos = photos.filter(user__nsid=nsid)
    return photos


@register.simple_tag
def photo_license(n):
    """Returns the text value of the Photo's license, indicated by the number n.
    Will probably be an HTML link to more info.
    """
    licenses = dict((x,y) for x,y in Photo.LICENSES)

    if n in licenses:
        if n in Photo.LICENSE_URLS and Photo.LICENSE_URLS[n] != '':
            return '<a href="%s" title="More about permissions">%s</a>' % \
                                        (Photo.LICENSE_URLS[n], licenses[n])
        else:
            return licenses[n]
    else:
        return '[missing]'

@register.simple_tag
def photo_safety_level(n):
    """Returns the textual version of the Photo's safety level."""
    levels = dict((x,y) for x,y in Photo.SAFETY_LEVELS)

    try:
        return levels[n]
    except KeyError:
        return '[missing]'

