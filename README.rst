==============
 Django Ditto
==============

.. image:: https://travis-ci.org/philgyford/django-ditto.svg?branch=main
  :target: https://travis-ci.org/philgyford/django-ditto?branch=main

.. image:: https://coveralls.io/repos/github/philgyford/django-ditto/badge.svg?branch=main
  :target: https://coveralls.io/github/philgyford/django-ditto?branch=main

A collection of Django apps for copying things from third-party sites and services. Requires Python 3.6, 3.7 or 3.8, and Django 2.2, 3.0 or 3.1.

`Read the documentation. <http://django-ditto.readthedocs.io/en/latest/>`_

`See screenshots of a site using the supplied templates. <https://github.com/philgyford/django-ditto/tree/main/screenshots>`_

Install using `pip <https://pip.pypa.io/en/stable/>`_::

    $ pip install django-ditto

NOTE: It will install `Pillow <http://pillow.readthedocs.io/en/latest/>`_, among other things, which has prerequisites of its own, such as libjpeg and zlib. Sorry.

Currently, Ditto can copy these things from these services:

- `Flickr <https://flickr.com/>`_
    - Photos
    - Photosets
    - Original image and video files
    - Users
- `Last.fm <https://www.last.fm/>`_
    - Scrobbles (Artist, Track and Album)
- `Pinboard <https://pinboard.in/>`_
    - Bookmarks
- `Twitter <https://twitter.com/>`_
    - Tweets
    - Favorites/Likes
    - Images and Animated GIFs (but not videos)
    - Users

The Ditto apps provide:

- Models
- Admin
- Management commands to fetch the data/files
- Views and URLs
- Templates (that use `Bootstrap 4 <https://getbootstrap.com>`_, CSS only (no JavaScript))
- Template tags for common things (eg, most recent Tweets, or Flickr photos uploaded on a particular day)
