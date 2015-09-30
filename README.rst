=====
Ditto
=====

A collection of Django apps for copying things from third-party sites and
services. Very much in-progress.

Currently only copies bookmarks from `Pinboard <https://pinboard.in/>`_ and tweets from Twitter. See possible future services in `this issue <https://github.com/philgyford/django-ditto/issues/23>`_.

There is a demo Django project website for viewing fetched items in the ``/demo/`` directory.

Docs below are hasty; I'm not expecting anyone else to use this yet.


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


Services
########


Pinboard
********

In the Django admin, add your Pinboard account(s) with API token from https://pinboard.in/settings/password .

Import all of your bookmarks::

    $ ./demo/manage.py fetch_pinboard_bookmarks --all

Periodically fetch the most recent bookmarks, eg 20 of them::

    $ ./demo/manage.py fetch_pinboard_bookmarks --recent=20

Or fetch bookmarks posted on one date::

    $ ./demo/manage.py fetch_pinboard_bookmarks --date=2015-06-20

Or fetch a single bookmark by its URL (eg, if you've changed the description
of a particular bookmark you've alread fetched)::

    $ ./demo/manage.py fetch_pinboard_bookmarks --url=http://new-aesthetic.tumblr.com/

The above fetch those bookmark(s) for all Accounts you've added. To restrict to
a single account use ``--account``, eg::

    $ ./demo/manage.py fetch_pinboard_bookmarks --all --account=philgyford

Be aware of the rate limits: https://pinboard.in/api/#limits


Twitter
*******

In the Django admin, add a new Account, with Twitter API credentials.

Then you *must* do::

    $ ./demo/manage.py fetch_accounts

which will fetch the data for that account's Twitter user.

Request your Twitter archive at https://twitter.com/settings/account . When
you've downloaded it, do::

    $ ./demo/manage.py import_tweets --path=/Users/phil/Downloads/12552_dbeb4be9b8ff5f76d7d486c005cc21c9faa61f66

using the correct path to the directory you've downloaded and unzipped. This
will import all of the tweets found in the archive.

Run this periodically to fetch the most recent tweets::

    $ ./demo/manage.py fetch_twitter_tweets --recent

And this to fetch recent tweets that your accounts have favorited::

    $ ./demo/manage.py fetch_twitter_tweets --favorites

Those will both fetch tweets for all Accounts with API credentials. To restrict
to a single account add `--account` with the Twitter username. eg::

    $ ./demo/manage.py fetch_twitter_tweets --recent --account=philgyford

Fetching recent and favorite tweets will fetch as many tweets as the API allows (currently around 3200). Subsequent fetches will get tweets newer since the last time.


Other things
############

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



