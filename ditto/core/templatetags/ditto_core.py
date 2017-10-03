from datetime import datetime
from django import template
from django.core.urlresolvers import reverse
from django.http import QueryDict
from django.utils.html import format_html

from ..apps import ditto_apps


register = template.Library()


@register.simple_tag
def get_enabled_apps():
    """
    Returns a list of strings indicating which Ditto apps are enabled.
    e.g.
        ['flickr', 'twitter',]
    """
    return ditto_apps.enabled()


@register.simple_tag(takes_context=True)
def query_string(context, key, value):
    """
    For adding/replacing a key=value pair to the GET string for a URL.

    eg, if we're viewing ?p=3 and we do {% url_replace order 'taken' %}
    then this returns "p=3&order=taken"

    And, if we're viewing ?p=3&order=uploaded and we do the same thing, we get
    the same result (ie, the existing "order=uploaded" is replaced).

    Expects the request object in context to do the above; otherwise it will
    just return a query string with the supplied key=value pair.
    """
    try:
        request = context['request']
        args = request.GET.copy()
    except KeyError:
        args = QueryDict('').copy()
    args[key] = value
    return args.urlencode()


@register.simple_tag
def width_height(w, h, max_w, max_h):
    """Returns a string like:
        width="200" height="150"
    with the values limited to max_w and max_h, and scaled appropriately.

    If both w and h are smaller than their maximums, they're returned as is.
    """
    ratio = 1

    if w > max_w and h > max_h:
        ratio = min( (max_w / w), (max_h / h) )

    elif w > max_w:
        ratio = max_w / w

    elif h > max_h:
        ratio = max_h / h

    width = int(round(w * ratio))
    height = int(round(h * ratio))

    return format_html('width="%s" height="%s"' % (width, height))


@register.simple_tag
def display_time(dt, link_to_day=False, granularity=0, case=None):
    """Return the HTML to display the time a Photo, Tweet, etc.

    dt -- The datetime.
    view -- Nothing or 'detail' or 'day', probably.
    granularity -- A number indicating how detailed the datetime is, based on
                    https://www.flickr.com/services/api/misc.dates.html
    case -- How the visible text will be treated. By default will be lowercase
                except for Month names. None, 'lower', or 'capfirst'.

    For a 'day' view, just returns the date/time as text.
    For other views returns it including a link to the ditto:day_archive page
        for that date.
    Both wrapped in a <time> tag.

    See also http://www.brucelawson.co.uk/2012/best-of-time/ for <time> tag.
    """

    if granularity == 8:
        visible_time = 'circa %s' % dt.strftime('%Y')
        stamp = dt.strftime('%Y')

    elif granularity == 6:
        visible_time = 'sometime in %s' % dt.strftime('%Y')
        stamp = dt.strftime('%Y')

    elif granularity == 4:
        visible_time = 'sometime in %s' % dt.strftime('%b&nbsp;%Y')
        stamp = dt.strftime('%Y-%m')

    else:
        # Exact time and date.
        # We can link to the date, if link_to_day=True.

        stamp = dt.strftime('%Y-%m-%d %H:%M:%S')

        # The date and time formats for display:
        d_fmt = '%-d&nbsp;%b&nbsp;%Y'
        t_fmt = '%H:%M'

        if link_to_day:
            url = reverse('ditto:day_archive', kwargs={
                        'year':     dt.strftime('%Y'),
                        'month':    dt.strftime('%m'),
                        'day':      dt.strftime('%d'),
                    })

            visible_time = '%(time)s on <a href="%(url)s" title="All items from this day">%(date)s</a>' % {
                    'time': dt.strftime(t_fmt),
                    'url': url,
                    'date': dt.strftime(d_fmt),
                }
        else:
            visible_time = dt.strftime(t_fmt + ' on ' + d_fmt)

    if case == 'lower':
        visible_time = visible_time.lower()
    elif case == 'capfirst':
        visible_time = visible_time[0].upper() + visible_time[1:]

    return format_html('<time datetime="%(stamp)s">%(visible)s</time>' % {
                'stamp': stamp,
                'visible': visible_time
            })


@register.simple_tag(takes_context=True)
def current_url_name(context):
    """
    Returns the name of the current URL, namespaced, or False.

    Example usage:

        {% current_url_name as url_name %}

        <a href="#"{% if url_name == 'myapp:home' %} class="active"{% endif %}">Home</a>

    """
    url_name = False
    if context.request.resolver_match:
        url_name = "{}:{}".format(
                                context.request.resolver_match.namespace,
                                context.request.resolver_match.url_name
                            )
    return url_name
