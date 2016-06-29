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

To use Ditto in your own project (untested as yet), add the core ``ditto.core`` application to your project's ``INSTALLED_APPS`` in your ``settings.py``, and add the applications for the services you need. This example includes Flickr, Pinboard and Twitter::

    INSTALLED_APPS = (
        # other apps listed here.
        # ...
        'imagekit',       # Required only to use downloaded images and videos
        'sortedm2m',      # Required only for ditto.flickr
        'taggit',         # Required only for ditto.flickr and ditto.pinboard
        'ditto.core',
        'ditto.flickr',
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


*************************
Add to context processors
*************************

Add the project's context processor in your settings::

    TEMPLATES = [
        {
            ...
            'OPTIONS': {
                'context_processors': [
                    # other context processors listed here.
                    'ditto.core.context_processors.ditto',
                ]
            }
        }
    ]


**************
Add to urls.py
**************

To use Ditto's supplied views you can include each app's URLs in your project's own ``urls.py``. Note that each app requires the correct namespace (``flickr``, ``pinboard`` or ``twitter``), eg::

    from django.conf.urls import include, url
    from django.contrib import admin

    urlpatterns = [
        url(r'^admin/', include(admin.site.urls)),

        url(r'^flickr/', include('ditto.flickr.urls', namespace='flickr')),
        url(r'^pinboard/', include('ditto.pinboard.urls', namespace='pinboard')),
        url(r'^twitter/', include('ditto.twitter.urls', namespace='twitter')),

        # To include the overall, aggregated views:
        url(r'ditto/', include('ditto.core.urls', namespace='ditto')),
    ]

**NOTE:** The ``include`` module needs to be imported from ``django.conf.urls``.

Change the URL include paths (eg, ``r'^ditto/pinboard/'`` as appropriate) to suit your project. See the ``urls.py`` in the ``devproject/`` project for a full example.


********
Settings
********

Some of the apps have optional settings which can be put in your project's ``settings.py``. They're described in detail in each service's documentation. This is the complete list with their default values::

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

