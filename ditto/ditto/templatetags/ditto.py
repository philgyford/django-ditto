from datetime import datetime
from django import template
from django.core.urlresolvers import reverse


register = template.Library()

@register.simple_tag
def time_link(dt, view_type):
    """Return the HTML to display the time a Photo, Tweet, etc.

    dt -- The datetime.
    view -- Nothing or 'detail' or 'day', probably.

    For a 'day' view, just returns the date/time as text.
    For other views returns it including a link to the ditto:day_archive page
        for that date.
    Both wrapped in a <time> tag.
    """

    # The date and time formats for display:
    d_fmt = '%-d %b %Y'
    t_fmt = '%H:%M'

    if view_type == 'day':
        visible_time = dt.strftime(t_fmt + ' on ' + d_fmt)
    else:
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

    return '<time datetime="%(stamp)s">%(visible)s</time>' % {
                'stamp': dt.strftime('%Y-%m-%d %H:%M:%S'),
                'visible': visible_time
            }


@register.filter
def split_by(items, n):
    """Splits a list into n chunks. Returns a list of n lists."""

    def make_chunks(items, n):
        """Yield successive n-sized chunks from items."""
        for i in range(0, len(items), n):
            yield items[i:i+n]

    return list(make_chunks(items, n))

