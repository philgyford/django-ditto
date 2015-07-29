=====
Ditto
=====

A collection of Django apps for copying things from third-party sites and
services. Very much in-progress.

Currently only copies bookmarks from `Pinboard <https://pinboard.in/>`_. See possible future services in `this issue <https://github.com/philgyford/django-ditto/issues/23>`_.

There is a demo Django project website for viewing fetched items in the ``/demo/`` directory.


Getting started
###############

Development with the demo website::

    $ pip install -r demo/requirements.txt
    $ python setup.py develop
    $ ./demo/manage.py test
    $ ./demo/manage.py runserver


Add to INSTALLED_APPS
*********************

To use Ditto in your own project (untested as yet), add the core ``ditto.ditto`` application to your project's ``INSTALLED_APPS`` in your ``settings.py``, and add the appropriate application for which services you need. eg, to use Pinboard::

    INSTALLED_APPS = (
        ...
        'taggit',
        'ditto.ditto',
        'ditto.pinboard',
    )

Note that ``ditto.pinboard`` also requires ``taggit`` to be included, as shown.

Add to urls.py
**************

To use Ditto's views you can include each app's URLs in your project's own
``urls.py``. eg::

    from django.conf.urls import include, url
    from django.contrib import admin

    urlpatterns = [
        url(r'^admin/', include(admin.site.urls)),

        # If you're using the ditto.pinbaord app:
        url(r'^ditto/pinboard/', include('ditto.pinboard.urls', namespace='pinboard')),
        # To include the overall, aggregated views:
        url(r'ditto/', include('ditto.ditto.urls', namespace='ditto')),
    ]

Change the URL include paths (eg, ``r'^ditto/pinboard/'`` as appropriate) to
suit your project.

Add your Accounts
*****************
Then add your Pinboard account(s) in Django's admin screens, and use the
management commands to fetch some or all of your bookmarks. Copying is one way
- changes made to bookmarks in your Django admin will not be copied back to
Pinboard, and changes might be overridden when you next fetch bookmarks.

Other things
************

To have large numbers formatted nicely, ensure these are in your ``settings.py``::

    USE_L10N = True
    USE_THOUSAND_SEPARATOR = True


Other notes for development
###########################

Using coverage.py to check test coverage::

    $ coverage run --source='.' ./demo/manage.py test
    $ coverage report

Instead of the in-terminal report, get an HTML version::

    $ coverage html
    $ open -a "Google Chrome" htmlcov/index.html



