from urllib.parse import quote_plus


def slugify_name(name):
    """
    Takes a string and returns the version used in a Last.fm URL
    As best as we can work out how its done.

    We need to do this for Albums, because their URLs aren't provided in the
    RecentScrobbles API response.

    See tests.lastfm.test_utils for examples.
    """

    # Last.fm doesn't quote certain punctuation characters:
    name = quote_plus(name, safe='!&(),:;')

    # Some things need extra encoding for Last.fm's URLs:
    replacements = (
        ('%2B', '%252B'),   # + has an extra level of quoting.
        ('%5C', '%5C%5C'),  # \ gets encoded twice.
    )

    for find, repl in replacements:
        name = name.replace(find, repl)

    return name
