import re
from django import template
from django.template.defaultfilters import stringfilter
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter
@stringfilter
def tweet(value):
    """Add links to usernames, hashtags and URLs in a tweet's text
    value is the tweet text.

    Usage:
    {{ tweet.text|tweet }}
    """
    # Make standard links clickable:
    value = re.sub(r'((mailto\:|(news|(ht|f)tp(s?))\://){1}\S+)',
            '<a href="\g<0>" rel="external nofollow">\g<0></a>', value)
    # Make Twitter usernames clickable:
    value = re.sub(r'#(?P<tag>\w+)',
            '<a href="https://twitter.com/hashtag/\g<tag>?src=hash" rel="external">#\g<tag></a>',
            value)
    # Make hashtags clickable:
    value = re.sub(r'@(?P<username>\w+)',
            '<a href="https://twitter.com/\g<username>" rel="external">@\g<username></a>',
            value)
    value = re.sub(r'\n', '<br>', value.strip())
    return mark_safe(value)


