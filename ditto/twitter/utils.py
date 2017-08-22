# coding: utf-8
import re

from django.utils.html import urlize

from ttp import ttp
from twython import Twython


def htmlify_description(json_data):
    """Passed the raw JSON data about a User from Twitter's API, it returns an
    HTMLified version of the User's description.
    * Replaces t.co URLs with clickable, full links.
    * Makes #hashtags into clickable links.
    * Makes @usernames into clickable links.

    Different to htmlify_tweet() because:

        * Twitter user data only includes entities for urls, not hashtags etc.
          https://twittercommunity.com/t/why-do-user-entities-have-only-urls-field-and-not-others/59181

        * So we manually make the t.co links into their full, clickable version.
        * And then use twitter-text-python to linkify everything else.
    """

    # I don't think users in the Twitter archive JSON have description
    # elements:
    try:
        desc = json_data['description']
    except KeyError:
        return ''

    # Make t.co URLs into their original URLs, clickable.
    if 'entities' in json_data and 'description' in json_data['entities']:
        entities = json_data['entities']['description']

        if 'urls' in entities:
            for entity in entities['urls']:
                start, end = entity['indices'][0], entity['indices'][1]
                shown_url = entity['display_url']
                link_url = entity['expanded_url']

                url_html = '<a href="%s" rel="external">%s</a>'
                desc = desc.replace(json_data['description'][start:end],
                                            url_html % (link_url, shown_url))

    # Make #hashtags and @usernames clickable.
    parser = ttp.Parser()
    parsed = parser.parse(desc)

    return parsed.html


def htmlify_tweet(json_data):
    """Passed the raw JSON data about a Tweet from Twitter's API, it returns
    an HTMLified version of the Tweet's text. It:
    * Replaces linebreaks with '<br>'s.
    * Replaces @mentions with clickable @mentions.
    * Replaces #hashtags with clickable #hashtags.
    * Replaces $symbols with clickable $symbols.
    * Replaces t.co URLs with clickable, full links.
    """

    # Temporary, until Twython.html_for_tweet() can handle tweets with
    # 'full_text' attributes.
    if 'full_text' in json_data:
        json_data['text'] = json_data['full_text']

    # Some Tweets (eg from a downloaded archive) don't have entities['symbols']
    # which Twython.html_for_tweet() currently expects.
    # Not needed once github.com/ryanmcgrath/twython/pull/451 is in Twython.
    if 'entities' in json_data and 'symbols' not in json_data['entities']:
        json_data['entities']['symbols'] = []

    # This does most of the work for us:
    # https://twython.readthedocs.org/en/latest/usage/special_functions.html#html-for-tweet
    html = Twython.html_for_tweet(
                    json_data, use_display_url=True, use_expanded_url=False)

    # Need to do some tidying up:

    try:
        ents = json_data['entities']
    except KeyError:
        ents = {}

    urls_count = len(ents['urls']) if 'urls' in ents else 0
    media_count = len(ents['media']) if 'media' in ents else 0
    hashtags_count = len(ents['hashtags']) if 'hashtags' in ents else 0
    symbols_count = len(ents['symbols']) if 'symbols' in ents else 0
    user_mentions_count = len(ents['user_mentions']) if 'user_mentions' in ents else 0

    # Replace the classes Twython adds with rel="external".
    html = html.replace('class="twython-hashtag"', 'rel="external"')
    html = html.replace('class="twython-mention"', 'rel="external"')
    html = html.replace('class="twython-media"', 'rel="external"')
    html = html.replace('class="twython-symbol"', 'rel="external"')

    # Twython uses the t.co URLs in the anchor tags.
    # We want to replace those with the full original URLs.
    # And replace the class it adds with rel="external".
    if (urls_count + media_count) > 0:
        if urls_count > 0:
            for url in ents['urls']:
                html = html.replace(
                        '<a href="%s" class="twython-url">' % url['url'],
                        '<a href="%s" rel="external">' % url['expanded_url']
                    )

    if media_count > 0:
        # Remove any media links, as we'll make the photos/movies visible in
        # the page. All being well.
        for item in ents['media']:
            html = html.replace('<a href="%s" rel="external">%s</a>' % \
                                        (item['url'], item['display_url']),
                                '')

    if (urls_count + media_count + hashtags_count + symbols_count + user_mentions_count) == 0:
        # Older Tweets might contain links but have no 'urls'/'media' entities.
        # So just make their links into clickable links:
        # But don't do this for newer Tweets which have an entities element,
        # or we'll end up trying to make links from, say user_mentions we
        # linked earlier.
        html = urlize(html)

    # Replace newlines with <br>s
    html = re.sub(r'\n', '<br>', html.strip())

    return html

