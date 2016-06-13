==============
 Django Ditto
==============

.. image:: https://travis-ci.org/philgyford/django-ditto.svg?branch=master
  :target: https://travis-ci.org/philgyford/django-ditto?branch=master

.. image:: https://coveralls.io/repos/github/philgyford/django-ditto/badge.svg?branch=master
  :target: https://coveralls.io/github/philgyford/django-ditto?branch=master

A collection of Django apps for copying things from third-party sites and services. This is still in-progress and things may change. Requires Python 3.4 or 3.5, and Django 1.8 or 1.9.

Currently, Ditto can copy these things from these services:

- `Flickr <https://flickr.com/>`_
    - Photos
    - Photosets
    - Original image and video files
    - Users
- `Pinboard <https://pinboard.in/>`_
    - Bookmarks
- `Twitter <https://twitter.com/>`_
    - Tweets
    - Favorites/Likes
    - Users

It can save these things for one or more account on each service. See possible future services, and overall progress, in `this issue <https://github.com/philgyford/django-ditto/issues/23>`_.

Public and private Photos, Bookmarks and Tweets are saved, but only public ones are displayed in the included Django views and templates; non-public ones are only visible in the Django admin.

The Ditto app provides:

- Models
- Admin
- Management commands to fetch the data/files
- Views and URLs
- Templates (that use `Bootstrap 4 <http://v4-alpha.getbootstrap.com>`_)
- Template tags for common things (eg, most recent Tweets, or Flickr photos uploaded on a particular day)


##############
 Installation
##############

******
Pillow
******

Ditto uses `Pillow <http://pillow.readthedocs.io/en/latest/>`_ which has some prerequisites of its own. You may need to install libjpeg and zlib. (On a Mac, zlib was installed for me by XCode, and I used `Homebrew <http://brew.sh>`_ to install libjpeg.)


*********************
Add to INSTALLED_APPS
*********************

To use Ditto in your own project (untested as yet), add the core ``ditto.core`` application to your project's ``INSTALLED_APPS`` in your ``settings.py``, and add the applications for the services you need. This example includes Flickr, Pinboard and Twitter::

    INSTALLED_APPS = (
        # other apps listed here.
        # ...
        'imagekit',       # Required only to use locally-stored ditto.flickr images.
        'sortedm2m',      # Required only for ditto.flickr
        'taggit',         # Required only for ditto.flickr and ditto.pinboard
        'ditto.core',
        'ditto.flickr',
        'ditto.pinboard',
        'ditto.twitter',
    )

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

Change the URL include paths (eg, ``r'^ditto/pinboard/'`` as appropriate) to
suit your project. See the ``urls.py`` in the ``devproject/`` project for a full
example.


##########
 Services
##########

As well as including the apps and URLs, you need to link each one with your account(s) on the related services. Each app has an ``Account`` model, which parallels an account on the related service (eg, a Twitter account). The method of linking the two varies with each service.


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


Photo data
==========

Now you can fetch data about your Photos. This will fetch data for ALL Photos for ALL Accounts (for me it took about 75 minutes for 3,000 photos)::

    $ ./manage.py fetch_flickr_photos --days=all

This will only fetch Photos uploaded in the past 3 days::

    $ ./manage.py fetch_flickr_photos --days=3

Both options can be restricted to only fetch for a single Account by adding the NSID of the Account's Flickr User, eg::

    $ ./manage.py fetch_flickr_photos --account=35034346050@N01 --days=3

Photo files
===========

The above only fetches data about the photos (title, locations, EXIF, tags, etc). To download the original photo and video files themselves, use the ``fetch_flickr_originals`` command, *after* fetching the photos' data::

    $ ./manage.py fetch_flickr_originals

This took over 90 minutes for about 3,000 photos for me. By default this command will fetch all the original files that haven't yet been downloaded (so the first time, it will fetch all of them). To force it to download *all* the files again (if you've deleted them locally, but they're still on Flickr) then::

    $ ./manage.py fetch_flickr_originals --all

Both variants can be restricted to fetching files for a single account::

    $ ./manage.py fetch_flickr_originals --account=35034346050@N01

Files will be saved within your project's ``MEDIA_ROOT`` directory, as defined in ``settings.py``. There are two optional settings to customise the directories in which the files are saved. Their default values are as shown here::

   DITTO_FLICKR_DIR_BASE = 'flickr'
   DITTO_FLICKR_DIR_PHOTOS_FORMAT = '%Y/%m/%d'

These values are used if you don't specify your own settings.

If your ``MEDIA_ROOT`` was set to ``/var/www/example.com/media/`` then the above settings would save the Flickr photo ``1234567_987654_o.jpg`` to something like this, depending on the Flickr user's NSID and the date the photo was taken (not uploaded)::

    /var/www/example.com/media/flickr/35034346050N01/photos/2016/08/31/1234567_987654_o.jpg

Note that videos will have *two* "original" files downloaded: the video itself and a JPG image that Flickr created for it.

Once you've downloaded the original image files, you can use these to generate all the different sizes of image required for your site, instead of linking direct to the image files on flickr.com. To do this, ensure ``imagekit`` is in your ``INSTALLED_APPS`` setting::

    INSTALLED_APPS = (
        # ...
        'imagekit',
        # ...
    )

And add this to your `settings.py` (its default value is ``False``)::

    DITTO_FLICKR_USE_LOCAL_PHOTOS = True

Any requests in your templates for the URLs of photo files of any size will now use resized versions of your downloaded original files, generated by Imagekit.  The first time you load a page (especially if it lists many Flickr images) it will be slow, but the images are cached (in a ``CACHE`` directory in your media folder).

For example, before changing this setting, the URL of small image (``Photo.small_url``) would be something like this::

    https://farm8.static.flickr.com/7442/27289611500_d0debff24e_m.jpg

After choosing to use local photos, it would be something like this::

    /media/CACHE/images/flickr/35034346050N01/photos/2016/06/09/27289611500_d21f6f47a0_o/0ee894a3438233848e6e9d85e1985260.jpg

If you change your mind you can switch back to using the images hosted on flickr.com by removing the ``DITTO_FLICKR_USE_LOCAL_PHOTOS`` setting or changing it to ``False``.

Note that Ditto currently can't do the same for videos, even if the original video file has been downloaded. No matter what the  value of ``DITTO_FLICKR_USE_LOCAL_PHOTOS`` the flickr.com URL for videos is always used.


Photosets
=========

You can fetch data about your Photosets (also known as Albums) any time, but
this won't fetch complete data for any Photos. So any Photos not already
fetched will not be fetched by this process.

So, for best results, ensure all Photos are downloaded before fetching Photoset
data.

To fetch Photosets for all Accounts::

    $ ./manage.py fetch_flickr_photosets

Or fetch for only one Account::

    $ ./manage.py fetch_flickr_photosets --account=35034346050@N01

Users
=====

Profile photos of Flickr Users are downloaded and stored in your project's ``MEDIA_ROOT`` directory. You can optionally set the ``DITTO_FLICKR_DIR_BASE`` setting to change the location. The default is::

   DITTO_FLICKR_DIR_BASE = 'flickr'

If your ``MEDIA_ROOT`` was set to ``/var/www/example.com/media/`` then the above setting would save the profile image for the user with NSID ``35034346050@N01`` to something like this::

    /var/www/example.com/media/flickr/35034346050N01/avatars/35034346050N01.jpg


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

Tweets
======

If you have more than 3,200 Tweets, you can only include older Tweets by downloading your archive and importing it. To do so, request your archive at https://twitter.com/settings/account . When you've downloaded it, do::

    $ ./manage.py import_twitter_tweets --path=/Users/phil/Downloads/12552_dbeb4be9b8ff5f76d7d486c005cc21c9faa61f66

using the correct path to the directory you've downloaded and unzipped. This will import all of the Tweets found in the archive. The data in the archive isn't complete, so to fully-populate those Tweets you should run this (replacing ``philgyford`` with your Twitter screen name)::

    $ ./manage.py update_twitter_tweets --account=philgyford

This will fetch data for up to 6000 Tweets. You can run it every 15 minutes if you have more than 6000 Tweets in your archive. It will fetch data for the least-recently fetched.  It's worth running every so often in the future, to fetch the latest data (such as Retweet and Like counts).

If there are newer Tweets, not in your downloaded archive, then run this::

    $ ./manage.py fetch_twitter_tweets --account=philgyford --recent=3200

The ``3200`` is the number of recent Tweets to fetch, with ``3200`` being the maximum allowed in one go.

Run this version periodically to fetch the Tweets since you last fetched any::

    $ ./manage.py fetch_twitter_tweets --account=philgyford --recent=new

You might also, or instead, want to fetch more than that, eg::

    $ ./manage.py fetch_twitter_tweets --account=philgyford --recent=200

This would update data such as the Retweet and Like counts for all of the 200
fetched Tweets, even if they're older than your last fetch.

If you have more than one Twitter Account in Ditto, the above commands can be
run across all of them by omitting the ``--account`` option. eg::

    $ ./manage.py fetch_twitter_tweets --recent=new

Favorites/Likes
===============

And one or both of these to fetch recent Tweets that all your Accounts have liked::

    $ ./manage.py fetch_twitter_favorites --recent=new
    $ ./manage.py fetch_twitter_favorites --recent=200

Or restrict to a single Account::

    $ ./manage.py fetch_twitter_favorites --account=philgyford --recent=new
    $ ./manage.py fetch_twitter_favorites --account=philgyford --recent=200

Users
=====

When a Tweet of any kind is fetched, its User data is also stored, and the User's profile photo (avatar) is downloaded and stored in your project's ``MEDIA_ROOT`` directory. You can optionally set the ``DITTO_TWITTER_DIR_BASE`` setting to change the location. The default is::

   DITTO_TWITTER_DIR_BASE = 'twitter'

If your ``MEDIA_ROOT`` was set to ``/var/www/example.com/media/`` then the above setting would save the profile image for the user with a Twitter ID ``12345678`` to something like this::

    /var/www/example.com/media/twitter/12345678/avatars/my_avatar.jpg

You may periodically want to update the stored data about all the Twitter users
stored in Ditto. (quantity of Tweets, descriptions, etc). Do it like this::

    $ ./manage.py update_twitter_users --account=philgyford

This requires an ``account`` as the data is fetched from that Twitter user's point of view, when it comes to privacy etc.


##############
 Other things
##############


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



