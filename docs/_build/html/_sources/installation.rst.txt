############
Installation
############

******
Pillow
******

Ditto uses `Pillow <http://pillow.readthedocs.io/en/latest/>`_ which has some prerequisites of its own. You may need to install libjpeg and zlib. (On a Mac, zlib was installed for me by XCode, and I used `Homebrew <http://brew.sh>`_ to install libjpeg.)


********************
Install django-ditto
********************

Ditto can be installed using `pip <https://pip.pypa.io/en/stable/>`_:

.. code-block:: shell

    $ pip install django-ditto


*********************
Add to INSTALLED_APPS
*********************

To use Ditto in your own project (untested as yet), add the core ``ditto.core`` application to your project's ``INSTALLED_APPS`` in your ``settings.py``, and add the applications for the services you need. This example includes Flickr, Last.fm, Pinboard and Twitter::

    INSTALLED_APPS = (
        # other apps listed here.
        # ...
        'imagekit',       # Required only to use downloaded images and videos
        'sortedm2m',      # Required only for ditto.flickr
        'taggit',         # Required only for ditto.flickr and ditto.pinboard
        'ditto.core',
        'ditto.flickr',
        'ditto.lastfm',
        'ditto.pinboard',
        'ditto.twitter',
    )

If you only wanted to use the Flickr part, including displaying downloaded photos, you would do this::

    INSTALLED_APPS = (
        # other apps listed here.
        # ...
        'imagekit',       # Required only to use downloaded images and videos
        'sortedm2m',      # Required only for ditto.flickr
        'taggit',         # Required only for ditto.flickr and ditto.pinboard
        'ditto.core',
        'ditto.flickr',
    )

Or, to use only the Twitter part, and not worry about using local versions of
images::

    INSTALLED_APPS = (
        # other apps listed here.
        # ...
        'ditto.core',
        'ditto.twitter',
    )


**************
Add to urls.py
**************

To use Ditto's supplied views you can include each app's URLs in your project's own ``urls.py``. Note that each app requires the correct namespace (``flickr``, ``lastfm``, ``pinboard`` or ``twitter``), eg::

    from django.urls import include, path
    from django.contrib import admin

    urlpatterns = [
        path("admin/", include(admin.site.urls)),

        path("flickr/", include("ditto.flickr.urls")),
        path("lastfm/", include("ditto.lastfm.urls")),
        path("pinboard/", include("ditto.pinboard.urls")),
        path("twitter/", include("ditto.twitter.urls")),

        # To include the overall, aggregated views:
        path("ditto/', include("ditto.core.urls")),
    ]

Change the URL include paths (eg, ``r'^ditto/pinboard/'`` as appropriate) to suit your project. See the ``urls.py`` in the ``devproject/`` project for a full example.

Each app's URL conf is included under an appropriate ``app_name``:

* ``flickr``
* ``lastfm``
* ``pinboard``
* ``twitter``
* ``ditto`` (The Ditto Core URLs)


********
Settings
********

There are some optional settings that can be placed in your project's ``settings.py``.

Core settings
=============

The ``ditto.core`` app has some optional settings for customing the formats used to display dates and times in the default templates (and the ``ditto_core.display_time()`` template tag). The formats are those used for `strftime <http://strftime.org>`_. Here they are, with their default values::

    # e.g. "07:34"
    DITTO_CORE_TIME_FORMAT = '%H:%M'

    # e.g. "8 Apr 2018"
    DITTO_CORE_DATE_FORMAT = '%-d %b %Y'

    # Used when both a time and a date are displayed.
    # The [time] and [date] tokens are replaced with the formats from the
    # two settings above.
    # e.g. "07:34 on 8 Apr 2018"
    DITTO_CORE_DATETIME_FORMAT = '[time] on [date]'

    # Used when only a year is displayed.
    # e.g. "2018"
    DITTO_CORE_DATE_YEAR_FORMAT = '%Y'

    # Used when only a month and year are displayed.
    # e.g. "Apr 2018"
    DITTO_CORE_DATE_YEAR_MONTH_FORMAT = '%b %Y'


Service-specific settings
=========================

In addition, some of the other apps have their own optional settings. They're described in detail in each service's documentation.

This is the complete list of service-specific settings with their default values::

    DITTO_FLICKR_DIR_BASE = 'flickr'
    DITTO_FLICKR_DIR_PHOTOS_FORMAT = '%Y/%m/%d'
    DITTO_FLICKR_USE_LOCAL_MEDIA = False

    DITTO_TWITTER_DIR_BASE = 'twitter'
    DITTO_TWITTER_USE_LOCAL_MEDIA = False


Other optional settings
=======================

To have large numbers formatted nicely in the included templates, ensure these are in your ``settings.py``::

    USE_L10N = True
    USE_THOUSAND_SEPARATOR = True


*******************
Set up each service
*******************

Each service (such as Flickr or Twitter) you want to use will require some set-up in order to link your account(s) on the service with Django Ditto. See the documentation for each service for how to do this.
