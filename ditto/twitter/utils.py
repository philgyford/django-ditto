# coding: utf-8
import re

from django.utils.html import urlize


def htmlify_tweet(json_data):
    """Passed the raw JSON data about a Tweet from Twitter's API, it returns
    an HTMLified version of the Tweet's text. It:
    * Replaces linebreaks with '<br>'s.
    * Replaces @mentions with clickable @mentions.
    * Replaces #hashtags with clickable #hashtags.
    * Replaces $symbols with clickable $symbols.
    * Replaces t.co URLs with clickable, full links.
    """

    text = json_data['text']

    # Replace newlines with <br>s
    text = re.sub(r'\n', '<br>', text.strip())

    try:
        ents = json_data['entities']
    except KeyError:
        ents = {}

    urls_count = len(ents['urls']) if 'urls' in ents else 0
    media_count = len(ents['media']) if 'media' in ents else 0
    hashtags_count = len(ents['hashtags']) if 'hashtags' in ents else 0
    symbols_count = len(ents['symbols']) if 'symbols' in ents else 0
    user_mentions_count = len(ents['user_mentions']) if 'user_mentions' in ents else 0

    # We must do this before linkifying URLs, in case the URLs we put in
    # contain a @usermention.
    if user_mentions_count > 0:
        for user in ents['user_mentions']:
            text = text.replace('@%s' % user['screen_name'],
                '<a href="https://twitter.com/%s" rel="external">@%s</a>' % (
                                    user['screen_name'], user['screen_name']))

    if hashtags_count > 0:
        for tag in ents['hashtags']:
            text = text.replace('#%s' % tag['text'],
                '<a href="https://twitter.com/hashtag/%s" rel="external">#%s</a>'
                                            % (tag['text'], tag['text']))

    if symbols_count > 0:
        # Just using the regex here:
        # https://blog.twitter.com/2013/symbols-entities-for-tweets
        text = re.sub(r'\$([a-zA-Z]{1,6}(?:[._][a-zA-Z]{1,2})?)\b',
                    r'<a href="https://twitter.com/search?q=%24\1" rel="external">$\1</a>',
                    text)

    # Try to work out if we're going to deal with linkifying URLs using the
    # entities['urls'] and entities['media'] elements, or if there aren't any.

    if (urls_count + media_count) > 0:
        if urls_count > 0:
            for url in ents['urls']:
                text = text.replace(url['url'],
                            '<a href="%s" rel="external">%s</a>' % (
                                    url['expanded_url'], url['display_url']))

        if media_count > 0:
            # Remove any media links, as we'll make the photos/movies visible in
            # the page. All being well.
            for item in ents['media']:
                text = text.replace(item['url'], '')
    elif (urls_count + media_count + hashtags_count + symbols_count + user_mentions_count) == 0:
        # Older Tweets might contain links but have no 'urls'/'media' entities.
        # So just make their links into clickable links:
        # But don't do this for newer Tweets which have an entities element,
        # or we'll end up trying to make links from, say user_mentions we
        # linked earlier.
        text = urlize(text)

    text = text.strip()

    return text

