# Changelog (Django Ditto)
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).


## [Unreleased]

- None


## [3.0.1] - 2023-05-22

### Fixed
- Fix the `search_fields` in `lastfm`'s `AccountAdmin`.

### Added
- Added general tests for Admin classes


## [3.0.0] - 2023-05-09

### Removed
- Dropped support for Python 3.7 and 3.8. (A bit eager but hopefully it's not a problem.)
- Dropped support for Django 4.0. (Nothing changed, but removed from tests.)

### Added
- Added support for Django 4.2. (Nothing changed, but added to tests.)

### Changed
- No longer requires pytz as a dependency.
- Update dependencies including allowing for django-taggit 4.0


## [2.3.0] - 2022-11-28

### Added
- Add migration for `pinboard.BookmarkTag.slug` that addes `allow_unicode=True`. (It's the default in django-taggit and suddenly it's generating a new migration.)
- Add support for python 3.11. (Nothing changed, but added to tests.)

### Changed
- Remove black version requirements


## [2.2.0] - 2022-08-08

### Added
- Added support for Django 4.1.
- Add the latest master branch Django to the tox testing matrix.
- Added `.pre-commit-config.yaml`

### Changed
- Update dependencies, including requiring django-taggit >= 3.0.0.
- Update included Bootstrap CSS from 4.6.0 to 4.6.2.
- Update development project dependencies

### Fixed
- Errors related to tags when using Django 4.1 (#238)


## [2.1.1] - 2022-03-25

### Fixed
- Include `.map` files in `core/static/ditto-core/`. They were missing which causes issues when running `collectstatic`.


## [2.1.0] - 2022-03-24

### Removed
- The no-longer-used `ditto/core/context_processors.py` file has been removed (deprecated in v0.6.0).

### Added
- Optional `start` and `end` arguments to the `fetch_flickr_photos` management command. (Thanks @garrettc)

### Fixed
- Handle error when importing Flickr data (such as tags) created by a Flickr user who has since been deleted. (#234, thanks @garrettc)
- Handle error when importing Flickr photos that don't have all expected image sizes. (#235, thanks @garrettc)
- Allow for the `User.realname` property to be blank because the Flickr API doesn't return that field at all for some users (#237)


## [2.0.0] - 2022-02-14

### Removed
- **Backwards incompatible:** Drop support for Django 2.2 and 3.1.

### Changed
- **Backwards incompatible:** Requires django-taggit >= v2.0.0
  (It changed how `TaggableManager` sets tags: https://github.com/jazzband/django-taggit/blob/master/CHANGELOG.rst#200-2021-11-14 )

### Added
- Add support for Django 4.0 (#223)
- Add support for Python 3.10 (#225)
- Add support for importing the "new" (2019-onwwards) format of downloadable Twitter archive (#229).


## [1.4.2] - 2021-10-22

### Changed
- Update python dependences in `devproject/Pipfile` and `docs/Pipfile`.
- Update included Bootstrap CSS and JS files to v4.6.0.
- Change README and CHANGELOG from `.rst` to `.md` format.

### Fixed
- Remove hard-coded Flickr ID in `fetch_flickr_account_user` management command (thanks @garrettc).


## [1.4.1] - 2021-08-24

### Fixed
- Replace use of deprecated `django.conf.urls.url()` method.
- Fix path to `img/default_avatar.png` static file.


## [1.4.0] - 2021-04-07

### Added
- Allow for use of Django 3.2; update devproject to use it.

### Changed
- Change status in `setup.py` from Beta to Production/Stable.


## [1.3.9] - 2020-12-23

### Fixed
- Add missing update migration for Pinboard.


## [1.3.0] - 2020-11-20

### Changed
- Update Flickr Photo models, fetchers and imagegenerators to include the X-Large 3K, X-Large 4K, X-Large 5K and X-Large 6K sizes.

  A data migration will populate the model fields for any Photos that have this size data already fetched in their raw API data. It does the same for the Medium 800, Large, Large 1600, and Large 2048 sizes too.

- Update included Bootstrap from 4.5.2 to 4.5.3.

- Update python dependencies, including Pillow v8, freezegun v1, and django-debug-toolbar v3.

### Fixed
- Fix ordering of Tweets posted at the same time (as in some threads).


## [1.2.0] - 2020-08-22

### Fixed
- Fix Factory Boy imports and allow for Factory Boy v3


## [1.1.0] - 2020-08-10

### Changed
- Move all static files from `static/` to `static/ditto-core/`.


## [1.0.0] - 2020-08-10

### Changed
- About time we went to version 1.
- Allow for use of Django 3.1, django-taggit 1.3, pillow 7.2.
- Update included Bootstrap CSS from 4.5.0 to 4.5.2.


## [0.11.2]

### Changed
- Add flake8 to tests
- Upgrade Bootstrap CSS and JS from v4.4 to v4.5, and jQuery from 3.4.1 to 3.5.1.

### Fixed
- Fix BOM/encoding error when fetching data from the Pinboard API


## [0.11.1]

### Changed
- Update devproject python dependencies
- Update Bootstrap CSS and JS from 4.1.1 to 4.4.1, Popper to 1.16, and jQuery from 3.3.1 to 3.4.1.

### Fixed
- Fix character encoding issue with fetched Last.fm data


## [0.11.0]

### Removed
- Dropped support for Django 2.1. Now requires either Django 2.2 or 3.0.


## [0.10.3]

### Changed
- Allow for use of Pillow 6.2 as well as 6.1.
- Update devproject dependencies.


## [0.10.2]

### Fixed
- Fix error when fetching Flickr photos that have location data, as Flickr currently isn't returning `place_id` or `woeid` fields. (0.10.1 was a poor attempt at fixing this.)


## [0.10.0]

### Removed
- Drop support for Django 2.0

### Added
- Add support for Django 2.2

### Changed
- No new features, but upgrades of requirements.
- Switch from django-sortedm2m to django-sorted-m2m, which contains Django 2.2 support.
- Upgrade pillow requirement from 4.3 to 6.1.
- Also upgrade requirements for django-taggit (from 0.22 to 1.1) and flickrapi (from 2.3 to 2.4).
- Upgrade Bootstrap in devproject from 4.1 to 4.3.
- Upgrade Django used in devproject from 2.1 to 2.2.


## [0.9.0]

### Added
- Add support for Django 2.1 (no code changes required).

### Changed
- Change to use pipenv, instead of pip, for devproject requirements.


## [0.8.1]

### Changed
- Upgrade Twython requirement to 3.7.0 from custom version.
- Upgrade Django used in devproject from 2.0.4 to 2.0.5.
- Upgrade included Bootstrap from v4.1.0 to v4.1.1.


## [0.8.0]

### Added
- Add optional settings for the date and time formats used in default templates.

### Changed
- Upgrade Bootstrap from v4-beta-3 to v4.1.
- Upgraded Twython (and added a migration) to fix formatting of some Tweets.


## [0.7.6]

### Fixed
- Fix an error when fetching a Flickr user's data if they didn't have 'location' or 'timezone' data set.

## [0.7.5]

### Fixed
- Fix display of images (Twitter avatars and images, Flickr avatars and images) in the Django Admin pages.


## [0.7.4]

### Changed
- When fetching Twitter favorites, fetches the extended version of the tweets and includes entities.
- Temporarily use a different specific version of Twython (see README or docs).


## [0.7.3]

### Changed
- Fetches extended tweet data when fetching recent tweets.
- Temporarily requires manual inclusion of a specific version of Twython in your project's pip requirements (see README or docs).

### Fixed
- Handles tweets longer than 255 characters without Postgres complaining (SQLite quietly carried on).


## [0.7.2]

### Fixed
- Add missing migrations for Flickr and Last.fm.


## [0.7.1]

### Changed
- For Last.fm template tags, rely on the `FIRST_DAY_OF_WEEK` Django setting, instead of the now unused `DITTO_WEEK_START` setting.


## [0.7.0]

### Removed
- Drop support for Django 1.10.

### Added
- Add support Django 2.0

### Changed
- Upgrade Bootstrap from v4 beta 1 to v4 beta 3.


## [0.6.5]

### Changed
- Increase the maximum length of a Twitter User's display name to 50 characters.


## [0.6.4]

### Added
- The Flickr `day_photos` template tag can now fetch photos taken on a particular day, as well as posted on a day.


## [0.6.3]

### Added
- The Last.fm template tags for the top albums, artists and tracks can now display the top list for a week, as well as day, month and year.


## [0.6.2]

### Added
- Added the `popular_bookmark_tags` template tag to the `pinboard` app.


## [0.6.1]

### Fixed
- Fix bug when importing Flickr photos and there's already a tag with a different `slug` but the same `name`.


## [0.6.0]

### Deprecated
- The ditto context\_processor is no longer required, and now does nothing.
  Replaced its `enabled_apps` with a `get_enabled_apps` template tag.


## [0.5.2]

### Fixed
- Fix screenshots URL in README and documentation.


## [0.5.0]

### Added
- Add Bootstrap and jQuery to make navigation bar collapsible

### Changed
- Upgrade Bootstrap to v4-beta #189, #180
- Test it works in Django 1.11 #185
- Label the `core` app as `ditto_core` #186
- Upgrade dependencies #188
- Removed `current_url_name` from context processor and made it a template tag #184
- Moved Bootsrap CSS into a `css` directory #182
- Change 'scrobbles' to 'listens' on day archive #181
