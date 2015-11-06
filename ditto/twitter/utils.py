# coding: utf-8
import re

from django.utils.html import urlize


def htmlify_tweet(json_data):
    """Passed the raw JSON data about a Tweet from Twitter's API, it returns
    an HTMLified version of the Tweet's text. It:
    * Replaces linebreaks with '<br>'s.
    * Replaces @mentions with clickable @mentions.
    * Replaces #hashtags with clickable #hashtags.
    * Replaces t.co URLs with clickable, full links.
    """

    text = json_data['text']

    # Replace newlines with <br>s
    text = re.sub(r'\n', '<br>', text.strip())

    try:
        ents = json_data['entities']
    except KeyError:
        ents = {}

    # We must do this before linkifying URLs, in case the URLs we put in
    # contain a @usermention.
    if 'user_mentions' in ents and len(ents['user_mentions']):
        for user in ents['user_mentions']:
            text = text.replace('@%s' % user['screen_name'],
                '<a href="https://twitter.com/%s" rel="external">@%s</a>' % (
                                    user['screen_name'], user['screen_name']))

    if 'hashtags' in ents and len(ents['hashtags']):
        for tag in ents['hashtags']:
            text = text.replace('#%s' % tag['text'],
                '<a href="https://twitter.com/hashtag/%s" rel="external">#%s</a>'
                                            % (tag['text'], tag['text']))

    # Try to work out if we're going to deal with linkifying URLs using the
    # entities['urls'] and entities['media'] elements, or if there aren't any.
    urls_count = len(ents['urls']) if 'urls' in ents else 0
    media_count = len(ents['media']) if 'media' in ents else 0

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
    else:
        # Older Tweets might contain links but have no 'urls'/'media' entities.
        # So just make their links into clickable links:
        text = urlize(text)

    text = text.strip()

    return text

