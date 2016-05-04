=====
Ditto
=====

.. image:: https://travis-ci.org/philgyford/django-ditto.svg?branch=master
  :target: https://travis-ci.org/philgyford/django-ditto?branch=master

.. image:: https://coveralls.io/repos/github/philgyford/django-ditto/badge.svg?branch=master
  :target: https://coveralls.io/github/philgyford/django-ditto?branch=master

A collection of Django apps for copying things from third-party sites and
services. Very much in-progress. Requires Python 3.4 or 3.5, and Django 1.8 or
1.9.

Currently, it copies your Bookmarks from `Pinboard <https://pinboard.in/>`_, your Tweets and Favorites from `Twitter <https://twitter.com/>`_, and your Photos from `Flickr <https://flickr.com/>`_. See possible future services in `this issue <https://github.com/philgyford/django-ditto/issues/23>`_. These work well, but there may be changes as this is still in development.

Public and private Tweets, Photos and Bookmarks are copied, but only public
ones are displayed in the included views and templates; non-public ones are
only visible in the Django admin.

The docs below are hasty; I'm not expecting anyone else to use this yet.


############
Installation
############

*********************
Add to INSTALLED_APPS
*********************

To use Ditto in your own project (untested as yet), add the core ``ditto.core`` application to your project's ``INSTALLED_APPS`` in your ``settings.py``, and add the applications for the services you need. This includes Flickr, Pinboard and Twitter::

    INSTALLED_APPS = (
        # other apps listed here.
        'taggit',
        'ditto.core',
        'ditto.flickr',
        'ditto.pinboard',
        'ditto.twitter',
    )

Note that both ``ditto.flickr`` and ``ditto.pinboard`` also require ``taggit`` to be included, as shown.

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

To use Ditto's views you can include each app's URLs in your project's own
``urls.py``. Note that each app requires the correct namespace (``flickr``,
``pinboard`` or ``twitter``), eg::

    from django.conf.urls import include, url
    from django.contrib import admin

    urlpatterns = [
        url(r'^admin/', include(admin.site.urls)),

        # If you're using the ditto.pinboard app:
        url(r'^ditto/pinboard/', include('ditto.pinboard.urls', namespace='pinboard')),

        # To include the overall, aggregated views:
        url(r'ditto/', include('ditto.core.urls', namespace='ditto')),
    ]

Change the URL include paths (eg, ``r'^ditto/pinboard/'`` as appropriate) to
suit your project. See the ``urls.py`` in the ``demo/`` project for a full
example.


########
Services
########

As well as including the apps and URLs, you need to link each one with your
account(s) on the related services. Each app has an ``Account`` model, which
parallels an account on the related service (eg, a Twitter account). The method of linking the two varies with each service.


******
Flickr
******

In the Django admin, create a new Account in the Flickr app, and add your Flickr API key and secret from https://www.flickr.com/services/apps/create/apply/

By default this will only allow the fetching of fully public photos. To fetch
all photos your Flickr account can access, you'll need to do this:

1. Enter your API key and secret in the indicated place in the file
   ``scripts/flickr_authorize.py``.

2. Run the script on the command line::

   $ python scripts/flickr_authorize.py

3. Follow the instructions. A new browser window should open for you to
   authorize your Flickr account. You'll then get a code to paste into your
   Terminal.

Finally, for each of those Accounts, note its ID from the Django admin, and do this to fetch information about its associated Flickr user (replacing ``1`` with your ID, if different)::

    $ ./manage.py fetch_flickr_account_user --id=1

Now you can fetch data about your Photos (it doesn't currently fetch the photo files themselves). This will fetch ALL Photos for ALL Accounts (for me it took about 75 minutes for 3,000 photos)::

    $ ./manage.py fetch_flickr_photos --days=all

This will only fetch Photos uploaded in the past 3 days::

    $ ./manage.py fetch_flickr_photos --days=3

Both options can be restricted to only fetch for a single Account by adding the NSID of the Account's Flickr User, eg::

    $ ./manage.py fetch_flickr_photos --account=35034346050@N01 --days=3


********
Pinboard
********

In the Django admin, add an Account in the Pinboard app with your API token from https://pinboard.in/settings/password .

Import all of your bookmarks::

    $ ./manage.py fetch_pinboard_bookmarks --all

Periodically fetch the most recent bookmarks, eg 20 of them::

    $ ./manage.py fetch_pinboard_bookmarks --recent=20

Or fetch bookmarks posted on one date::

    $ ./manage.py fetch_pinboard_bookmarks --date=2015-06-20

Or fetch a single bookmark by its URL (eg, if you've changed the description
of a particular bookmark you've alread fetched)::

    $ ./manage.py fetch_pinboard_bookmarks --url=http://new-aesthetic.tumblr.com/

The above commands fetch bookmark(s) for all Accounts you've added. To restrict to a single account use ``--account`` with the Pinboard username, eg::

    $ ./manage.py fetch_pinboard_bookmarks --all --account=philgyford

Be aware of the rate limits: https://pinboard.in/api/#limits


*******
Twitter
*******

In the Django admin, add a new Account in the Twitter app, with your API credentials from https://apps.twitter.com/ .

Then you *must* do::

    $ ./manage.py fetch_twitter_accounts

which will fetch the data for that Account's Twitter user.

If you have more than 3,200 Tweets, you can only include older Tweets by downloading your archive and importing it. To do so, request your archive at https://twitter.com/settings/account . When you've downloaded it, do::

    $ ./manage.py import_twitter_tweets --path=/Users/phil/Downloads/12552_dbeb4be9b8ff5f76d7d486c005cc21c9faa61f66

using the correct path to the directory you've downloaded and unzipped. This will import all of the Tweets found in the archive. The data in the archive isn't complete, so to fully-populate those Tweets you should run this (replacing ``philgyford`` with your Twitter screen name)::

    $ ./manage.py update_twitter_tweets --account=philgyford

This will fetch data for up to 6000 Tweets. You can run it every 15 minutes if you have more than 6000 Tweets in your archive. It will fetch data for the least-recently fetched.  It's worth running every so often in the future, to fetch the latest data (such as Retweet and Like counts).

If there are newer Tweets, not in your downloaded archive, then run this::

    $ ./manage.py fetch_twitter_tweets --recent=3200

The ``3200`` is the number of recent Tweets to fetch, with ``3200`` being the maximum allowed in one go.

Run this version periodically to fetch the Tweets since you last fetched any::

    $ ./manage.py fetch_twitter_tweets --recent=new

You might also, or instead, want to fetch more than that, eg::

    $ ./manage.py fetch_twitter_tweets --recent=200

This would update data such as the Retweet and Like counts for all of the 200
fetched Tweets, even if they're older than your last fetch.

And one or both of these to fetch recent Tweets that your accounts have liked::

    $ ./manage.py fetch_twitter_favorites --recent=new
    $ ./manage.py fetch_twitter_favorites --recent=200

All of the above commands will fetch Tweets and favorites for all Accounts that have API credentials set. To restrict to a single Account add `--account` with the Twitter screen name. eg::

    $ ./manage.py fetch_twitter_tweets --recent=new --account=philgyford

You may periodically want to update the stored data about all Twitter users
(numbers of Tweets, descriptions, etc). This will fetch the latest data::

    $ ./manage.py fetch_twitter_users --account=philgyford


############
Other things
############


*****************
Optional settings
*****************

To have large numbers formatted nicely, ensure these are in your ``settings.py``::

    USE_L10N = True
    USE_THOUSAND_SEPARATOR = True


***********
Development
***********

There's a basic Django project in ``devproject/`` to make it easier to work on
the app. This might be enough to get things up and running::

    $ pip install -r devproject/requirements.txt
    $ python setup.py develop
    $ ./devproject/manage.py runserver


*****
Tests
*****

Run tests with tox. Install it with::

    $ pip install tox

You'll need to have all versions of python available that are tested against (see ``tox.ini``). This might mean deactivating a virtualenv if you're using one with ``devproject/``. Then run all tests in all environments like::

    $ tox

To run tests in only one environment, specify it. In this case, Python 3.5 and
Django 1.9::

    $ tox -e py35-django19

To run a specific test, add its path after ``--``, eg::

    $ tox -e py35-django19 -- tests.ditto.tests.test_views.DittoViewTests.test_home_templates

Running the tests in all environments will generate coverage output. There will
also be an ``htmlcov/`` directory containing an HTML report. You can also
generaet these reports without running all the other tests::

    $ tox -e coverage


***************************
Other notes for development
***************************

Using coverage.py to check test coverage::

    $ coverage run --source='.' ./manage.py test
    $ coverage report

Instead of the in-terminal report, get an HTML version::

    $ coverage html
    $ open -a "Google Chrome" htmlcov/index.html



