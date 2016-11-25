# coding: utf-8
from django.utils.html import strip_tags
from django.utils.text import Truncator

import datetime
import pytz

from django.db.models import Count


def truncate_string(text, strip_html=True, chars=255, truncate=u'…', at_word_boundary=False):
    """Truncate a string to a certain length, removing line breaks and mutliple
    spaces, optionally removing HTML, and appending a 'truncate' string.

    Keyword arguments:
    strip_html -- boolean.
    chars -- Number of characters to return.
    at_word_boundary -- Only truncate at a word boundary, which will probably
        result in a string shorter than chars.
    truncate -- String to add to the end.
    """
    if strip_html:
        text = strip_tags(text)
    text = text.replace('\n', ' ').replace('\r', '')
    text = ' '.join(text.split())
    if at_word_boundary:
        if len(text) > chars:
            text = text[:chars].rsplit(' ', 1)[0] + truncate
    else:
        text = Truncator(text).chars(chars, html=False, truncate=truncate)
    return text


def datetime_now():
    """Just returns a datetime object for now in UTC, with UTC timezone.
    Because I was doing this a lot in various places.
    """
    return datetime.datetime.utcnow().replace(tzinfo=pytz.utc)


def datetime_from_str(s):
    """A shortcut for making a UTC datetime from a string like
    '2015-08-11 12:00:00'.
    """
    return datetime.datetime.strptime(s, '%Y-%m-%d %H:%M:%S').replace(
                                                            tzinfo=pytz.utc)

def get_annual_item_counts(qs, field_name='post_year'):
    """
    Takes a QuerySet, probably of a DittoItem child class like Photo or Tweet,
    and returns a list of dicts with 'year' and 'count' keys. eg:
        [
            {'year': 2015, 'count': 123},
            {'year': 2016, 'count': 456},
            {'year': 2017, 'count': 0},
            {'year': 2018, 'count': 789},
        ]

    Note, the first query we do here gets a QuerySet that only includes years
    in which there are any counts:
        [
            {'post_year': 2015, 'count': 123},
            {'post_year': 2016, 'count': 456},
            # Nothing included for 2017, which has count 0.
            {'post_year': 2018, 'count': 789},
        ]

    So the rest of this function is all about filling in those gaps.

    Used in all the annual_[thing]_counts() template tags.

    Arguments:
        qs -- The QuerySet.
        field_name -- Name of the key identifying the years.
    """

    qs = qs.values(field_name)\
                    .annotate(count=Count('id'))\
                    .values(field_name, 'count')\
                    .order_by(field_name)

    # Just in case. eg, trying to get counts for a private Twitter account:
    if len(qs) == 0:
        return []

    # Make a set of years like {2015, 2016, 2018}:
    years_with_counts = set(y[field_name] for y in qs)

    # Make a set of years with no gaps like {2015, 2016, 2017, 2018}:
    all_years = sorted(set(
                    range(min(years_with_counts), max(years_with_counts) + 1)
                ))

    # Translate original qs into {'2015': 123, '2016': 456, '2018': 789}:
    qs_dict = {}
    for row in qs:
        qs_dict[ str(row[field_name]) ] = row['count']

    # Make the final list of dicts.
    # An element for every year between min and max, even if it had no items,
    # in which case its count is 0.
    results = []
    for y in all_years:
        try:
            count = qs_dict[str(y)]
        except KeyError:
            count = 0
        results.append( {'year': y, 'count': count} )

    return results

