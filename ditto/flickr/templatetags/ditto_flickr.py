from datetime import datetime, timezone
from datetime import time as datetime_time

from django import template
from django.utils.html import format_html

from ditto.core.utils import get_annual_item_counts
from ditto.flickr.models import Photo, Photoset

register = template.Library()


@register.simple_tag
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
    photos = photos.prefetch_related("user")
    return photos[:limit]


@register.simple_tag
def day_photos(date, nsid=None, time="post_time"):
    """Returns a QuerySet of public Photos posted on a specific date.

    Arguments:
    date -- A date object.

    Keyword arguments:
    nsid -- A Flickr user's NSID. If not supplied, we fetch
                    Photos for all Flickr users that have Accounts.
    time -- A string, either 'post_time' (default) or 'taken_time'.
    """
    if time not in ["post_time", "taken_time"]:
        raise ValueError(
            "`time` must be either 'post_time' or " "'taken_time', not '%s'." % time
        )

    start = datetime.combine(date, datetime_time.min).replace(tzinfo=timezone.utc)
    end = datetime.combine(date, datetime_time.max).replace(tzinfo=timezone.utc)
    photos = Photo.public_photo_objects

    if time == "taken_time":
        photos = photos.filter(taken_time__range=[start, end])
    else:
        photos = photos.filter(post_time__range=[start, end])

    if nsid is not None:
        photos = photos.filter(user__nsid=nsid)

    photos = photos.prefetch_related("user")
    return photos


@register.simple_tag
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
    return photosets.prefetch_related("primary_photo", "user")[:limit]


@register.simple_tag
def photo_license(n):
    """Returns the text value of the Photo's license, indicated by the number n.
    Will probably be an HTML link to more info.
    """
    licenses = {x: y for x, y in Photo.LICENSES}

    if n in licenses:
        if n in Photo.LICENSE_URLS and Photo.LICENSE_URLS[n] != "":
            return format_html(
                '<a href="{}" title="More about permissions">{}</a>'.format(
                    Photo.LICENSE_URLS[n], licenses[n]
                )
            )
        else:
            return licenses[n]
    else:
        return "[missing]"


@register.simple_tag
def annual_photo_counts(nsid=None, count_by="post_time"):
    """
    Get the number of public Photos per year.
    Returns a list of dicts, sorted by year, like:
        [ {'year': 2015, 'count': 1234}, {'year': 2016, 'count': 9876} ]

    Keyword arguments:
    nsid -- A Flickr user's NSID or None (for Photos by all Users).
    count_by -- A string, either 'post_time' (default) or 'taken_time'.
    """

    if count_by not in ["post_time", "taken_time"]:
        raise ValueError(
            "`count_by` must be either 'post_time' or "
            "'taken_time', not '%s'." % count_by
        )

    qs = Photo.public_photo_objects

    if nsid is not None:
        qs = qs.filter(user__nsid=nsid)

    field_name = "taken_year" if count_by == "taken_time" else "post_year"

    return get_annual_item_counts(qs, field_name)
