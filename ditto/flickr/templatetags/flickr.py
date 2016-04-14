from django import template

from ..models import Photo
from ...ditto.templatetags.ditto import display_time


register = template.Library()

@register.simple_tag
def taken_time(dt, granularity):
    """Returns a string for the taken on date time of a photo, based on its
    granularity.

    dt is a datetime.
    granularity is a number from 0 to 10. ish.
    """
    s = ''
    if granularity == 0:
        s = "Taken at %s" % display_time(dt, True)
    elif granularity == 4:
        s = "Taken some time in %s" % dt.strftime('%B %Y')
    elif granularity == 6:
        s = "Taken some time in %s" % dt.strftime('%Y')
    elif granularity == 8:
        s = "Taken circa %s" % dt.strftime('%Y')

    return s

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

