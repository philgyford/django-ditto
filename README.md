# Django Ditto

![PyPI - Python Version](https://img.shields.io/pypi/pyversions/django-ditto)
[![image](https://github.com/philgyford/django-ditto/actions/workflows/tests.yml/badge.svg)](https://github.com/philgyford/django-ditto/actions/workflows/tests.yml "Tests status")
[![codecov](https://codecov.io/gh/philgyford/django-ditto/branch/main/graph/badge.svg?token=T7TMMDS64A)](https://codecov.io/gh/philgyford/django-ditto)
[![image](https://readthedocs.org/projects/django-ditto/badge/?version=stable)](https://django-ditto.readthedocs.io/en/stable/?badge=stable "Documentation status")
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](https://github.com/pre-commit/pre-commit)

A collection of Django apps for copying things from third-party sites and services. Requires Python 3.9 to 3.12, and Django 4.1, 4.2 or 5.0.

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
