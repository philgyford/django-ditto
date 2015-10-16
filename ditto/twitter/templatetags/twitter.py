from django import template

from ..models import Tweet, User


register = template.Library()


@register.assignment_tag
def recent_tweets(screen_name=None, limit=10):
    """Returns a QuerySet of recent public Tweets, in reverse-chronological
    order.

    Keyword arguments:
    screen_name -- A Twitter user's screen_name. If not supplied, we fetch
                    Tweets for all Twitter users that have Accounts.
    limit -- Maximum number to fetch. Default is 10.
    """
    if screen_name is None:
        users = User.objects_with_accounts.all()
        tweets = Tweet.public_objects.filter(user=users).select_related()
    else:
        tweets = Tweet.public_objects.filter(user__screen_name=screen_name)
    return tweets[:limit]

