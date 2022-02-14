Django Ditto
============

[![image](https://github.com/philgyford/django-ditto/actions/workflows/tests.yml/badge.svg)](https://github.com/philgyford/django-ditto/actions/workflows/tests.yml "Tests status")
[![image](https://coveralls.io/repos/github/philgyford/django-ditto/badge.svg?branch=main)](https://coveralls.io/github/philgyford/django-ditto?branch=main "Test coverage")
[![image](https://readthedocs.org/projects/django-ditto/badge/?version=stable)](https://django-ditto.readthedocs.io/en/stable/?badge=stable "Documentation status")

A collection of Django apps for copying things from third-party sites and services. Requires Python 3.6, 3.7, 3.8, 3.9 and 3.10, and Django 3.2 and 4.0.

[Read the documentation.](http://django-ditto.readthedocs.io/en/latest/)

[See screenshots of a site using the supplied templates.](https://github.com/philgyford/django-ditto/tree/main/screenshots)

Install using [pip](https://pip.pypa.io/en/stable/):

    $ pip install django-ditto

NOTE: It will install [Pillow](http://pillow.readthedocs.io/en/latest/), among other things, which has prerequisites of its own, such as libjpeg and zlib. Sorry.

Currently, Ditto can copy these things from these services:

- [Flickr](https://flickr.com/)
  - Photos
  - Photosets
  - Original image and video files
  - Users
- [Last.fm](https://www.last.fm/)
  - Scrobbles (Artist, Track and Album)
- [Pinboard](https://pinboard.in/)
  - Bookmarks
- [Twitter](https://twitter.com/)
  - Tweets
  - Favorites/Likes
  - Images and Animated GIFs (but not videos)
  - Users

The Ditto apps provide:

- Models
- Admin
- Management commands to fetch the data/files
- Views and URLs
- Templates (that use [Bootstrap 4](https://getbootstrap.com))
- Template tags for common things (eg, most recent Tweets, or Flickr photos uploaded on a particular day)
