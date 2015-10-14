# coding: utf-8
import re


def htmlify_tweet(json_data):
    """Passed the raw JSON data about a Tweet from Twitter's API, it returns
    an HTMLified version of the Tweet's text. It:
    * Replaces linebreaks with '<br>'s.
    * Replaces t.co URLs with clickable, full links.
    * Replaces @mentions with clickable @mentions.
    * Replaces #hashtags with clickable #hashtags.
    """

    text = json_data['text']

    # Replace newlines with <br>s
    text = re.sub(r'\n', '<br>', text.strip())

    try:
        ents = json_data['entities']
    except KeyError:
        ents = {}

    if 'urls' in ents and len(ents['urls']):
        for url in ents['urls']:
            text = text.replace(url['url'],
                            '<a href="%s" rel="external">%s</a>' % (
                                    url['expanded_url'], url['display_url']))

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

    return text

