########
Pinboard
########

You can fetch, store and display data about all your bookmarks for one or more `Pinboard <https://pinboard.in/>`_ accounts.


******
Set-up
******

In the Django admin, add an ``Account`` in the Pinboard app with your API token from https://pinboard.in/settings/password .

Then use the :ref:`pinboard-management-commands` to download your Bookmarks.


******
Models
******

The models available in ``ditto.pinboard.models`` are:

``Account``
    A single Pinboard account. (Note: other services, like Twitter and Flickr, have separate ``User`` and ``Account`` models. Pinboard is currently simpler.)

``BookmarkTag``
    A custom version of a Taggit Tag model, trying to match the way Pinboard creates slugs for tags.

``TaggedBookmark``
    The through model linking Bookmarks and BookmarkTags.

``Bookmark``
    A single URL added to Pinboard by a particular Account.


********
Managers
********

``Bookmark`` models have several managers:

``Bookmark.objects.all()``
    The default manager fetches *all* Bookmarks, posted by all Accounts, whether they're public or private.

``Bookmark.public_objects.all()``
    To display all Bookmarks on public-facing pages, ``public_objects`` should be used. It won't return Bookmarks marked as private.

``Bookmark.toread_objects.all()``
    Returns *all* Bookmarks, public and private, that are marked as 'To read'.

``Bookmark.public_toread_objects.all()``
    Returns only public 'To read' Bookmarks. Private 'To read' Bookmarks will not be included.

Of course, these can all be filtered as usual. So, to display public 'To read' Bookmarks posted by a particular Account::

    from ditto.pinboard.models import Account, Bookmark

    account = Account.objects.get(username='philgyford')
    bookmarks = Bookmark.public_to_read_objects.filter(account=account)


*************
Template tags
*************

There are two assignment template tags available for displaying Bookmarks in your templates.

Recent Bookmarks
================

To display the most recently-posted Bookmarks use ``recent_bookmarks``. By default it gets the 10 most recent Bookmarks posted by all Accounts:

.. code-block:: django

    {% load ditto_pinboard %}

    {% recent_bookmarks as bookmarks %}

    {% for bookmark in bookmarks %}
        <p><a href="{{ bookmark.url }}">{{ bookmark.title }}</a></p>
    {% endfor %}

The tag can also fetch a different number of Bookmarks and/or only get Bookmarks from a single Account. Here we only get the 5 most recent Bookmarks posted by the Account with a ``username`` of ``'philgyford'``.:

.. code-block:: django

    {% recent_bookmarks account='philgyford' limit=5 as bookmarks %}

Day Bookmarks
=============

To display Bookmarks posted to Pinboard on a particular day, use
``day_bookmarks``. By default it gets Bookmarks posted by all Accounts.
In this example, ``my_date`` is a `datetime.datetime.date <https://docs.python.org/3.5/library/datetime.html#datetime.date>`_ type:

.. code-block:: django

    {% load ditto_pinboard %}

    {% day_bookmarks my_date as bookmarks %}

    {% for bookmark in bookmarks %}
        <p><a href="{{ bookmark.url }}">{{ bookmark.title }}</a></p>
    {% endfor %}

Or we can restrict this to the Boomarks posted by a single account on that day:

.. code-block:: django

    {% day_bookmarks my_date account='philgyford' as bookmarks %}


.. _pinboard-management-commands:

*******************
Management commands
*******************

Once you have set up an Account with your Pinboard API token (see above), you
can fetch Bookmarks.

Fetch Bookmarks
===============

Import all of your bookmarks:

.. code-block:: shell

    $ ./manage.py fetch_pinboard_bookmarks --all

Periodically fetch the most recent bookmarks, eg 20 of them:

.. code-block:: shell

    $ ./manage.py fetch_pinboard_bookmarks --recent=20

Or fetch bookmarks posted on one date:

.. code-block:: shell

    $ ./manage.py fetch_pinboard_bookmarks --date=2015-06-20

Or fetch a single bookmark by its URL (eg, if you've changed the description
of a particular bookmark you've alread fetched):

.. code-block:: shell

    $ ./manage.py fetch_pinboard_bookmarks --url=http://new-aesthetic.tumblr.com/

The above commands fetch bookmark(s) for all Accounts you've added. To restrict to a single account use ``--account`` with the Pinboard username, eg:

.. code-block:: shell

    $ ./manage.py fetch_pinboard_bookmarks --recent=20 --account=philgyford

Be aware of the rate limits: https://pinboard.in/api/#limits


