Django Ditto
============

[![image](https://github.com/philgyford/django-ditto/actions/workflows/tests.yml/badge.svg)](https://github.com/philgyford/django-ditto/actions/workflows/tests.yml "Tests status")
[![codecov](https://codecov.io/gh/philgyford/django-ditto/branch/main/graph/badge.svg?token=T7TMMDS64A)](https://codecov.io/gh/philgyford/django-ditto)
[![image](https://readthedocs.org/projects/django-ditto/badge/?version=stable)](https://django-ditto.readthedocs.io/en/stable/?badge=stable "Documentation status")
[![Code style: prettier](https://img.shields.io/badge/code_style-prettier-ff69b4.svg?style=flat-square)](https://github.com/prettier/prettier)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Imports: isort](https://img.shields.io/badge/%20imports-isort-%231674b1?style=flat&labelColor=ef8336)](https://pycqa.github.io/isort/)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](https://github.com/pre-commit/pre-commit)


A collection of Django apps for copying things from third-party sites and services. Requires Python 3.9 to 3.11, and Django 3.2, 4.1, or 4.2.

[Read the documentation.](http://django-ditto.readthedocs.io/en/latest/)

[See screenshots of a site using the supplied templates.](https://github.com/philgyford/django-ditto/tree/main/screenshots)

Install using [pip](https://pip.pypa.io/en/stable/):

    $ pip install django-ditto

NOTE 1: It will install [Pillow](http://pillow.readthedocs.io/en/latest/), among other things, which has prerequisites of its own, such as libjpeg and zlib. Sorry.

NOTE 2: As of 2023 I'm unsure how well the Twitter integration still works given the state of its API etc.

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
