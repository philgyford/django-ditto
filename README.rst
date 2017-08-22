==============
 Django Ditto
==============

.. image:: https://travis-ci.org/philgyford/django-ditto.svg?branch=master
  :target: https://travis-ci.org/philgyford/django-ditto?branch=master

.. image:: https://coveralls.io/repos/github/philgyford/django-ditto/badge.svg?branch=master
  :target: https://coveralls.io/github/philgyford/django-ditto?branch=master

A collection of Django apps for copying things from third-party sites and services. This is still in-progress and things may change. Requires Python 3.4, 3.5 or 3.6, and Django 1.10 or 1.11.

`Read the documentation. <http://django-ditto.readthedocs.io/en/latest/>`_

`See screenshots of a site using the supplied templates. <https://github.com/philgyford/django-ditto/tree/master/screenshots>`_

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
- Templates (that use `Bootstrap 4 (Alpha 6) <http://v4-alpha.getbootstrap.com>`_, CSS only (no JavaScript))
- Template tags for common things (eg, most recent Tweets, or Flickr photos uploaded on a particular day)

