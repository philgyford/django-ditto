import datetime
import pytz

from django import template

from ..models import Tweet, User
from ...core.utils import get_annual_item_counts


register = template.Library()


@register.simple_tag
def recent_tweets(screen_name=None, limit=10):
    """Returns a QuerySet of recent public Tweets, in reverse-chronological
    order.

    Keyword arguments:
    screen_name -- A Twitter user's screen_name. If not supplied, we fetch
                    Tweets for all Twitter users that have Accounts.
    limit -- Maximum number to fetch. Default is 10.
    """
    tweets = Tweet.public_tweet_objects.all()
    if screen_name is not None:
        tweets = tweets.filter(user__screen_name=screen_name)
    return tweets.prefetch_related("user")[:limit]


@register.simple_tag
def recent_favorites(screen_name=None, limit=10):
    """Returns a QuerySet of recent Tweets favorited by the Account associated
    with the Twitter User with screen_name.

    Keyword arguments:
    screen_name -- A Twitter user's screen_name. If not supplied, we fetch
                    Tweets favorited by all public Accounts.
    limit -- Maximum number to fetch. Default is 10.
    """
    if screen_name is None:
        tweets = Tweet.public_favorite_objects.all()
    else:
        user = User.objects.get(screen_name=screen_name)
        if user.is_private:
            tweets = Tweet.objects.none()
        else:
            tweets = Tweet.public_favorite_objects.filter(favoriting_users=user)
    return tweets.prefetch_related("user")[:limit]


@register.simple_tag
def day_tweets(date, screen_name=None):
    """Returns a QuerySet of Tweets posted on a specific date by public
    Accounts.

    Arguments:
    date -- A date object.

    Keyword arguments:
    screen_name -- A Twitter user's screen_name. If not supplied, we fetch
                    all public Tweets.
    """
    start = datetime.datetime.combine(date, datetime.time.min).replace(tzinfo=pytz.utc)
    end = datetime.datetime.combine(date, datetime.time.max).replace(tzinfo=pytz.utc)
    tweets = Tweet.public_tweet_objects.filter(post_time__range=[start, end])
    if screen_name is not None:
        tweets = tweets.filter(user__screen_name=screen_name)
    tweets = tweets.prefetch_related("user")
    return tweets


@register.simple_tag
def day_favorites(date, screen_name=None):
    """Returns a QuerySet of Tweets posted on a specific date that have been
    favorited by public Accounts.

    NOTE: It is not the date on which the Tweets were favorited.
          The Twitter API doesn't supply that.

    Arguments:
    date -- A date object.

    Keyword arguments:
    screen_name -- A Twitter user's screen_name. If not supplied, we fetch
                    all public Tweets.
    """
    start = datetime.datetime.combine(date, datetime.time.min).replace(tzinfo=pytz.utc)
    end = datetime.datetime.combine(date, datetime.time.max).replace(tzinfo=pytz.utc)
    if screen_name is None:
        tweets = Tweet.public_favorite_objects.filter(post_time__range=[start, end])
    else:
        user = User.objects.get(screen_name=screen_name)
        if user.is_private:
            tweets = Tweet.objects.none()
        else:
            tweets = Tweet.public_favorite_objects.filter(
                post_time__range=[start, end]
            ).filter(favoriting_users=user)
    tweets = tweets.prefetch_related("user")
    return tweets


@register.simple_tag
def annual_tweet_counts(screen_name=None):
    """
    Get the number of public Tweets per year.
    Returns a list of dicts, sorted by year, like:
        [ {'year': 2015, 'count': 1234}, {'year': 2016, 'count': 9876} ]

    Keyword arguments:
    screen_name -- A Twitter user's screen_name. If not supplied, we fetch
                    all public Tweets.
    """

    tweets = Tweet.public_tweet_objects

    if screen_name is not None:
        tweets = tweets.filter(user__screen_name=screen_name)

    return get_annual_item_counts(tweets)


@register.simple_tag
def annual_favorite_counts(screen_name=None):
    """
    Get the number of public Favorites per year.
    (i.e. the Tweets are from those years, not that they were favorited then.)
    Returns a list of dicts, sorted by year, like:
        [ {'year': 2015, 'count': 1234}, {'year': 2016, 'count': 9876} ]

    Keyword arguments:
    screen_name -- A Twitter user's screen_name. If not supplied, we fetch
                    all public favorited Tweets.
    """

    if screen_name is None:
        tweets = Tweet.public_favorite_objects
    else:
        user = User.objects.get(screen_name=screen_name)
        if user.is_private:
            tweets = Tweet.objects.none()
        else:
            tweets = Tweet.public_favorite_objects.filter(favoriting_users=user)

    return get_annual_item_counts(tweets)
