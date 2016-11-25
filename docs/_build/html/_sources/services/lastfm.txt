#######
Last.fm
#######

You can fetch all your Scrobbles (listens) from one or more `Last.fm <https://www.last.fm/>`_ accounts. You can then view: recent Scrobbles; the most popular Artists, Tracks and Albums (for different time periods); number of Scrobbles per year; all Scrobbles for a single day; etc.


******
Set-up
******

In the Django admin, create a new ``Account`` in the Last.fm app. Enter your Last.fm username, your full name, and a Last.fm API key from http://www.last.fm/api/account/create

Now you can download your scrobbles. See :ref:`lastfm-management-commands`.


******
Models
******

The models available in ``ditto.lastfm.models`` are:

``Account``
    Representing a Last.fm account with an API key.

``Scrobble``
    A single listen to a particular ``Track`` by an ``Artist`` at a certain time
    (``post_time``), optionally on an ``Album``.

``Track``
    A track by an ``Artist``. Its ``scrobbles`` property is a set of
    ``Scrobble`` s; all the times it has been listened to. Tracks have no direct
    relationship to ``Album`` s.

``Artist``
    A music artist. Its ``scrobbles`` property is a set of ``Scrobble`` s; all the times ``Track`` s by this artist have been listened to.

``Album``
    An album by an ``Artist``. Its ``scrobbles`` property is a set of ``Scrobble`` s; all the times ``Tracks`` on this album have been listened to.

When the Last.fm API provides it, we store an ``mbid`` (MusicBrainz Identifier)
for each ``Track``, ``Artist`` and ``Album``.

The URL slug is used to differentiate one entity from another at Last.fm. While we store these as ``original_slug`` Ditto uses a lowercase version, ``slug``, so that matching newly-fetched entities to existing ones is more reliable. (And because there's no case-insensitive searching of unicode strings in SQLite.)

``Track`` s and ``Albums`` s aren't directly related; their only connection is
through ``Scrobble`` s. This is because the data doesn't seem reliable enough
to useful construct this relationship. Each ``Album`` has a ``tracks`` property
that returns a QuerySet of ``Track`` s associated with it::

    album = Album.objects.get(slug='bang+bang+rock+&+roll')

    for track in album.tracks:
        print(track.name)

Similarly, to get the ``Album`` s on which a particular ``Track`` appears, use its ``albums`` property::

    track = Track.objects.get(slug='emily+kane')

    for album in track.albums:
        print(album.name)

See ``ditto.lastfm.models`` for more useful properties and methods.


********
Managers
********

The default manager for each of ``Track``, ``Album`` and ``Artist`` has a ``with_scrobble_counts()`` method. This gives each returned object a ``scrobble_count`` property which is an aggregated count of the number of times that thing has been scrobbled. These results are also filterable by ``Account``, minimum and maximum scrobble time, and (for ``Track`` and ``Album``) by ``Artist``.

By default, the manager behaves as expected, eg::

    # A QuerySet of all Track objects:
    tracks = Track.objects.all()

    # A QuerySet of all Track objects by Art Brut:
    artist = Artist.objects.get(slug='art+brut')
    tracks = Track.objects.filter(artist=artist)

The default ordering is by ``name``.

To add number of scrobbles, and sort with the most-scrobbled tracks first::

    tracks = Track.objects.with_scrobble_counts().order_by('-scrobble_count')

    artist = Artist.objects.get(slug='art+brut')
    tracks = Track.objects.with_scrobble_counts(artist=artist).order_by('-scrobble_count')

Here, each ``Track`` will have a ``scrobble_count`` property, an integer.

Some more examples (``d1`` and ``d2`` are both ``datetime.datetime`` s)::

    # All Artists scrobbled since d1:
    artists = Artist.objects.with_scrobble_counts(min_post_time=d1)

    # All Albums scrobbled between d1 and d2,:
    albums = Album.objects.with_scrobble_counts(min_post_time=d1,
                                                max_post_time=d2)

    # All Tracks scrobbled by this account since d1:
    account = Account.objects.get(username='gyford')
    tracks = Track.objects.with_scrobble_counts(min_post_time=d1,
                                                account=account)

    # All Tracks by this artist scrobbled by this account, between d1 and d2:
    artist = Artist.objects.get(slug='art+brut')
    tracks = Track.objects.with_scrobble_counts(artist=artist,
                                                account=account,
                                                min_post_time=d1,
                                                max_post_time=d2)


*************
Template tags
*************

There are several assignment template tags for getting common lists of things.


Annual Scrobble Counts
======================

Get the number of scrobbles per year for all or one ``Account``. This fetches totals for all ``Account`` s:

.. code-block:: django

    {% load ditto_lastfm %}

    {% annual_scrobble_counts as counts %}

    {% for row in counts %}
        <p>
            {{ row.year }}: {{ row.count }}
        </p>
    {% endfor %}

Both the ``year`` and ``count`` in each row are integers.

To restrict totals to a single ``Account`` (assuming ``account`` is an ``Account`` object):

.. code-block:: django

    {% annual_scrobble_counts account=account as counts %}


Day Scrobbles
=============

Get a QuerySet of all Scrobbles from a particular day for one or all ``Account`` s, earliest first. In these examples, ``today`` can be either a ``datetime.datetime`` or a ``datetime.date``.

.. code-block:: django

    {% load ditto_lastfm %}

    {% day_scrobbles date=today as scrobbles %}

    {% for scrobble in scrobbles %}
        <p>
            {{ scrobble.artist.name }} - {{ scrobble.track.name }}
            ({{ scrobble.post_time }})
        </p>
    {% endfor %}

To restrict scrobbles to a single ``Account`` (assuming ``account`` is an ``Account`` object):

.. code-block:: django

    {% day_scrobbles date=today account=account as scrobbles %}


Recent Scrobbles
================

Get a QuerySet of the most recent Scrobbles, by one or all ``Account`` s.  The default quantity returned is 10.

.. code-block:: django

    {% load ditto_lastfm %}

    {% recent_scrobbles as scrobbles %}

    {# Then loop as in previous example. #}

To restrict scrobbles to a single ``Account`` (assuming ``account`` is an ``Account`` object), and increase the quantity returned to 30:

.. code-block:: django

    {% recent_scrobbles account=account limit=30 as scrobbles %}


Top Albums
==========

Get a QuerySet of the most-scrobbled ``Album`` s with the most-scrobbled first. This works in exactly the same way as the ``top_tracks`` template tag, above, with identical arguments. e.g.:

.. code-block:: django

    {% load ditto_lastfm %}

    {% top_albums artist=artist account=account date=my_date period='month' limit=5 as albums %}

    {% for album in albums %}
        <p>
            {{ forloop.counter }}.
            {{ album.artist.name }} - {{ album.name }}:
            {{ album.scrobble_count }}
        </p>
    {% endfor %}


Top Artists
===========

Get a QuerySet of the most-scrobbled ``Artist`` s with the most-scrobbled first. This works in a similar way to the ``top_tracks`` and ``top_albums`` template tags, above. The only difference is that results cannot be filtered by ``artist``. e.g.:

.. code-block:: django

    {% load ditto_lastfm %}

    {% top_artists account=account date=my_date period='month' limit=5 as albums %}

    {% for artist in artists %}
        <p>
            {{ forloop.counter }}.
            {{ artist.name }}:
            {{ album.scrobble_count }}
        </p>
    {% endfor %}


Top Tracks
==========

Get a QuerySet of the most-scrobbled ``Track`` s with the most-scrobbled first. Can be restricted to: a single ``Account``; a single day, month or year; tracks by a single ``Artist``. By default 10 tracks are returned.

.. code-block:: django

    {% load ditto_lastfm %}

    {% top_tracks as tracks %}

    {% for track in tracks %}
        <p>
            {{ forloop.counter }}.
            {{ track.artist.name }} - {{ track.name }}:
            {{ track.scrobble_count }}
        </p>
    {% endfor %}

Examples of fetching for a single day, month or year, assuming ``my_date`` is either a ``datetime.datetime`` or a ``datetime.date``:

.. code-block:: django

    {% top_tracks date=my_date period='day' as tracks %}

    {% top_tracks date=my_date period='month' as tracks %}

    {% top_tracks date=my_date period='year' as tracks %}

For month and year, the calendar month/year around the date is used. e.g. if the supplied date was ``2016-03-24`` then ``period='month'`` would produce a chart for March 2016, and ``period='year'`` would produce a chart for all of 2016.

Example of only fetching tracks by a single artist, assuming ``artist`` is an ``Artist`` object:

.. code-block:: django

    {% top_tracks artist=artist as tracks %}

Example of only fetching tracks scrobbled by a single ``Account``:

.. code-block:: django

    {% top_tracks account=account as tracks %}

Example of fetching only 5 tracks by a single ``Artist``, scrobbled by a single ``Account``, during a single month:

.. code-block:: django

    {% top_tracks artist=artist account=account date=my_date period='month' limit=5 as tracks %}

Arguments can be in any order.


.. _flickr-management-commands:

*******************
Management commands
*******************

There is only one Last.fm management command.

Fetch Scrobbles
===============

Fetches Scrobbles for one or all Accounts.

To fetch ALL Scrobbles for all Accounts (this could take a long time):

.. code-block:: shell

    $ ./manage.py fetch_lastfm_scrobbles --days=all

To fetch Scrobbles for all Accounts from the past 3 days:

.. code-block:: shell

    $ ./manage.py fetch_lastfm_scrobbles --days=3

Both options can be restricted to only fetch for a single Account by adding the Last.fm username. e.g.:

.. code-block:: shell

    $ ./manage.py fetch_lastfm_scrobbles --account=gyford --days=3

It's safe to re-fetch the same data. Duplicates will only occur if an Artist/Track/Album's URL slug has changed. A change of case won't cause duplicates, but anything more will.

Subsequent fetches will update any other changed data, such as altered Artist names, new or different MBIDs, etc.

