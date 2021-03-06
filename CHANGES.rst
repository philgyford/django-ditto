Changelog (Django Ditto)
========================

NOTE: 2020-06-20: Renamed ``master`` branch to ``main``
-------------------------------------------------------


Unreleased
----------

- None


1.3.9 - 2020-12-23
------------------

- Add missing update migration for Pinboard.


1.3.0 - 2020-11-20
------------------

- Update Flickr Photo models, fetchers and imagegenerators to include the
  X-Large 3K, X-Large 4K, X-Large 5K and X-Large 6K sizes.

  A data migration will populate the model fields for any Photos that have this
  size data already fetched in their raw API data. It does the same for the
  Medium 800, Large, Large 1600, and Large 2048 sizes too.

- Fix ordering of Tweets posted at the same time (as in some threads).

- Update included Bootstrap from 4.5.2 to 4.5.3.

- Update python dependencies, including Pillow v8, freezegun v1, and
  django-debug-toolbar v3.



1.2.0 - 2020-08-22
------------------

- Fix Factory Boy imports and allow for Factory Boy v3


1.1.0 - 2020-08-10
------------------

- Move all static files from ``static/`` to ``static/ditto-core/``.


1.0.0 - 2020-08-10
------------------

- About time we went to version 1.

- Allow for use of Django 3.1, django-taggit 1.3, pillow 7.2.

- Update included Bootstrap CSS from 4.5.0 to 4.5.2.


0.11.2
------

- Add flake8 to tests

- Upgrade Bootstrap CSS  and JS from v4.4 to v4.5, and jQuery from 3.4.1 to 3.5.1.

- Fix BOM/encoding error when fetching data from the Pinboard API


0.11.1
------

- Fix character encoding issue with fetched Last.fm data

- Update devproject python dependencies

- Update Bootstrap CSS and JS from 4.1.1 to 4.4.1, Popper to 1.16, and jQuery
  from 3.3.1 to 3.4.1.


0.11.0
------

- Requires either Django 2.2 or 3.0; dropped support for 2.1.


0.10.3
------

- Allow for use of Pillow 6.2 as well as 6.1.

- Update devproject dependencies.


0.10.2
------

- Fix error when fetching Flickr photos that have location data, as Flickr
  currently isn't returning ``place_id`` or ``woeid`` fields.
  (0.10.1 was a poor attempt at fixing this.)


0.10.0
------

- No new features, but upgrades of requirements.

- Add support for Django 2.2, drop support for Django 2.0

- Switch from django-sortedm2m to django-sorted-m2m, which contains Django 2.2
  support.

- Upgrade pillow requirement from 4.3 to 6.1.

- Also upgrade requirements for django-taggit (from 0.22 to 1.1) and flickrapi
  (from 2.3 to 2.4).

- Upgrade Bootstrap in devproject from 4.1 to 4.3.

- Upgrade Django used in devproject from 2.1 to 2.2.


0.9.0
-----

- Add support for Django 2.1 (no code changes required).

- Change to use pipenv, instead of pip, for devproject requirements.


0.8.1
-----

- Upgrade Twython requirement to 3.7.0 from custom version.

- Upgrade Django used in devproject from 2.0.4 to 2.0.5.

- Upgrade Bootstrap from v4.1.0 to v4.1.1.


0.8.0
-----

- Upgrade Bootstrap from v4-beta-3 to v4.1.

- Add optional settings for the date and time formats used in default templates.

- Upgraded Twython (and added a migration) to fix formatting of some Tweets.


0.7.6
-----

- Fix an error when fetching a Flickr user's data if they didn't have 'location'
  or 'timezone' data set.


0.7.5
-----

- Fix display of images (Twitter avatars and images, Flickr avatars and images)
  in the Django Admin pages.


0.7.4
-----

- When fetching Twitter favorites, fetches the extended version of the tweets
  and includes entities.

- Temporarily use a different specific version of Twython (see README or docs).


0.7.3
-----

- Handles tweets longer than 255 characters without Postgres complaining (SQLite
  quietly carried on).

- Fetches extended tweet data when fetching recent tweets.

- Temporarily requires manual inclusion of a specific version of Twython in your
  project's pip requirements (see README or docs).


0.7.2
-----

- Add missing migrations for Flickr and Last.fm.


0.7.1
-----

- For Last.fm template tags, rely on the ``FIRST_DAY_OF_WEEK`` Django setting,
  instead of the now unused ``DITTO_WEEK_START`` setting.


0.7.0
-----

- Add support Django 2.0; drop support for Django 1.10.

- Upgrade Bootstrap from v4 beta 1 to v4 beta 3.


0.6.5
-----

- Increase the maximum length of a Twitter User's display name to 50 characters.


0.6.4
-----

- The Flickr ``day_photos`` template tag can now fetch photos taken on
  a particular day, as well as posted on a day.


0.6.3
-----

- The Last.fm template tags for the top albums, artists and tracks can now
  display the top list for a week, as well as day, month and year.


0.6.2
-----

- Added the ``popular_bookmark_tags`` template tag to the ``pinboard`` app.


0.6.1
-----

- Fix bug when importing Flickr photos and there's already a tag with a
  different ``slug`` but the same ``name``.


0.6.0
-----

- The ditto context_processor is no longer required, and now does nothing.

- Replaced its ``enabled_apps`` with a ``get_enabled_apps`` template tag.


0.5.2
-----

- Fix screenshots URL in README and documentation.


0.5.0
-----

- Upgrade Bootstrap to v4-beta #189, #180

- Add Bootstrap and jQuery to make navigation bar collapsible

- Test it works in Django 1.11 #185

- Label the ``core`` app as ``ditto_core`` #186

- Upgrade dependencies #188

- Removed ``current_url_name`` from context processor and made it a template tag
  #184

- Moved Bootsrap CSS into a ``css`` directory #182

- Change 'scrobbles' to 'listens' on day archive #181
