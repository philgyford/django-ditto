from datetime import datetime
from django import template
from django.core.urlresolvers import reverse


register = template.Library()


@register.simple_tag(takes_context=True)
def query_string(context, key, value):
    """
    For adding/replacing a key=value pair to the GET string for a URL.

    eg, if we're viewing ?p=3 and we do {% url_replace order 'taken' %}
    then this returns "p=3&order=taken"

    And, if we're viewing ?p=3&order=uploaded and we do the same thing, we get
    the same result (ie, the existing "order=uploaded" is replaced).
    """
    request = context['request']
    args = request.GET.copy()
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

    return 'width="%s" height="%s"' % (width, height)


@register.simple_tag
def display_time(dt, link_to_day=False):
    """Return the HTML to display the time a Photo, Tweet, etc.

    dt -- The datetime.
    view -- Nothing or 'detail' or 'day', probably.

    For a 'day' view, just returns the date/time as text.
    For other views returns it including a link to the ditto:day_archive page
        for that date.
    Both wrapped in a <time> tag.
    """

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

    return '<time datetime="%(stamp)s">%(visible)s</time>' % {
                'stamp': dt.strftime('%Y-%m-%d %H:%M:%S'),
                'visible': visible_time
            }


@register.filter
def split_by(items, n):
    """Splits a list into chunks of n items."""

    def make_chunks(items, n):
        """Yield successive n-sized chunks from items."""
        for i in range(0, len(items), n):
            yield items[i:i+n]

    return list(make_chunks(items, n))

