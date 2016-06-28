import datetime
import pytz

from django import template
from django.utils.html import format_html

from ..models import Photo, Photoset, User
from ...core.templatetags.ditto_core import display_time


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
    photos = Photo.public_photo_objects.all()
    if nsid is not None:
        photos = photos.filter(user__nsid=nsid)
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
    photos = Photo.public_photo_objects.filter(post_time__range=[start, end])
    if nsid is not None:
        photos = photos.filter(user__nsid=nsid)
    return photos

@register.assignment_tag
def photosets(nsid=None, limit=10):
    """Returns a QuerySet of recent Photosets.

    Keyword arguments:
    nsid -- A Flickr user's NSID. If not supplied, we fetch
                    Photosets for all Flickr users that have Accounts.
    limit -- Maximum number to fetch. Default is 10.
    """
    photosets = Photoset.objects.all()
    if nsid is not None:
        photosets = photosets.filter(user__nsid=nsid)
    return photosets.select_related()[:limit]


@register.simple_tag
def photo_license(n):
    """Returns the text value of the Photo's license, indicated by the number n.
    Will probably be an HTML link to more info.
    """
    licenses = dict((x,y) for x,y in Photo.LICENSES)

    if n in licenses:
        if n in Photo.LICENSE_URLS and Photo.LICENSE_URLS[n] != '':
            return format_html(
                '<a href="%(url)s" title="More about permissions">%(name)s</a>' % {
                    'url': Photo.LICENSE_URLS[n],
                    'name': licenses[n],
                })
        else:
            return licenses[n]
    else:
        return '[missing]'

