#######
Twitter
#######

You can fetch, store and display data about your own Tweets and Liked Tweets for one or more `Twitter <https://twitter.com/>`_ accounts. By default the included models and templates will link to image and video files at Twitter, but you can also download the original files to store locally. These can then be used to serve different sizes of images locally. See the `Fetch Files management command <#fetch-files-media>`_ below.

******
Set-up
******

In the Django admin, add a new ``Account`` in the Twitter app, with your API credentials from https://apps.twitter.com/ .

Then you *must* do:

.. code-block:: shell

    $ ./manage.py fetch_twitter_accounts

which will fetch the data for that Account's Twitter user. You'll be able to see it in the Users section of the Twitter admin screens.

Once this is done you'll need to import a downloaded archive of Tweets, and/or
fetch Tweets from the Twitter API. See :ref:`twitter-management-commands` below.

******
Models
******

The models available in ``ditto.twitter.models`` are:

``Account``
    Representing a Twitter account that has API credentials and that we fetch Tweets and/or Likes for. It has a one-to-one relationship with a ``User`` model.

``Media``
    A photo, video or Animated GIF that was attached to one or more Tweets. Its ``media_type`` property differentiates between ``'photo'``, ``'video'`` and ``'animated_gif'``. (Yes, the plural model name is a bit confusing, sorry.) The files for photos and animated GIFs can be fetched from Twitter and used locally, although this isn't the default. See the `Fetch Files management command <#fetch-files-media>`_ below.

``Tweet``
    A Tweet. It may have been posted by one of the Users with an ``Account`` that we fetch Twets for. Or it might have been posted by a different ``User`` and favorited/liked by one of the Users with an ``Account``.

``User``
    A Twitter user. Every time a Tweet is fetched a new ``User`` object is created/updated for the person who posted it. One or more of these Users will have an associated ``Account``, as these are the user(s) we fetch data for.

So, you will end up with many ``User`` objects in the system. But only one (or a few) will be associated with ``Account`` objects -- these are the Users for which you fetch Tweets or favorited/liked Tweets.


********
Managers
********

Media
=====

For ``Media`` objects there is only the standard manager available:

``Media.objects.all()``
    Fetches all ``Media`` objects, attached to Tweets by anyone, whether public or private.

There is no concept in Twitter of a 'private' photo or video. The same photo
could be posted by different public and private Twitter users. Exercise caution
when displaying ``Media`` objects to public webpages.

Tweet
=====

``Tweet`` models have several managers. There are two main differentiators we want to restrict things by:

* **Public vs private:** Whether a Tweet was posted by a public or private Twitter user.
* **Posted Tweet vs Favorited Tweet:** Sometimes we'll want to only fetch Tweets posted by one of the Users with an API-credentialed Account. Sometimes we'll want to only fetch Tweets those Accounts have favorited/liked. Sometimes we'll want to fetch ALL Tweets, whether posted or favorited.

On public-facing web pages you should only use the managers starting ``Tweet.public_`` as these will filter out all Tweets posted by private Twitter users.

``Tweet.objects.all()``
    The default manager fetches *all* Tweets in the system, posted by all Users, whether they're public or private, and whether posted by an Account's User or favorited by them.

``Tweet.public_objects.all()``
    Only gets Tweets posted by any Users who are not private. This includes Tweets that have simply been favorited/liked by one of your Accounts.

``Tweet.tweet_objects.all()``
    Only gets Tweets posted by a User with an Account, not favorited by them.  And from both public and private Users.

``Tweet.public_tweet_objects.all()``
    Only gets Tweets posted by a User with an Account, not favorited by them, but only for Users who aren't private. For use on public pages.

``Tweet.favorite_objects.all()``
    Only gets Tweets favorited by a User with an Account, whether those Tweets are posted by public or private Users.

``Tweet.public_favorite_objects.all()``
    Only gets Tweets favorited by a User with an Account, and only Tweets posted by Users who aren't private.


Of course, these can all be filtered as usual. So, if you wanted to get all the public Tweets posted by a particular ``User``::

    from ditto.twitter.models import User, Tweet

    user = User.objects.get(screen_name='philgyford')
    tweets = Tweet.public_tweet_objects.filter(user=user)

And to get public Tweets that user has favorited::

    favorites = Tweet.public_favorite_objects.filter(user=user)


*************
Template tags
*************

There are four assigment template tags available for displaying Tweets in your templates.

Recent Tweets
=============

To display the most recent Tweets posted by any of the non-private Users with an API-credentialled Account. By default the most recent 10 are fetched:

.. code-block:: django

    {% load ditto_twitter %}

    {% recent_tweets as tweets %}

    {% for tweet in tweets %}
        <p>
            <b>{{ tweet.user.name }} (@{{ tweet.user.screen_name }})</b><br>
            {{ tweet.text_html|safe }}
        </p>
    {% endfor %}

(There's a lot more to displaying Tweets in full; see the included templates for examples.)

The tag can also fetch a different number of Tweets and/or only get Tweets from a single User-with-an-Account. Here we only get the 5 most recent Tweets posted by the User with a ``screen_name`` of ``'philgyford'``:

.. code-block:: django

    {% recent_tweets screen_name='philgyford' limit=5 as tweets %}

Recent Favorites
================

This works like ``recent_tweets`` except it only fetches Tweets favorited/liked
by our Users-with-Accounts, which were posted by public Twitter users:

.. code-block:: django

    {% load ditto_twitter %}

    {% recent_favorites as favorites %}

Similarly, we can change the number of Tweets returned (10 by default), and only return Tweets favorited by a particular User:

.. code-block:: django

    {% recent_favorites screen_name='philgyford' limit=5 as favorites %}

Day Tweets
==========

Gets Tweets posted on a particular day by any of the non-private Users-with-Accounts. In this example, ``my_date`` is a `datetime.datetime.date <https://docs.python.org/3.5/library/datetime.html#datetime.date>`_ type:

.. code-block:: django

    {% load ditto_twitter %}

    {% day_tweets my_date as tweets %}

Or we can restrict this to Tweets posted by a single User-with-an-Account:

.. code-block:: django

    {% day_tweets my_date screen_name='philgyford' as tweets %}

Day Favorites
=============

Use this to fetch Tweets posted on a particular day by non-private Users, which
have been favorited/liked by any of the Users-with-Accounts. Again, ``my_date`` is a `datetime.datetime.date <https://docs.python.org/3.5/library/datetime.html#datetime.date>`_ type:

.. code-block:: django

    {% load ditto_twitter %}

    {% day_favorites my_date as favorites %}

NOTE: The date is the date the Tweets were posted on, not the date on which they were favorited.

Again, we can restrict this to Tweets favorited by a single User-with-an-Account:

.. code-block:: django

    {% day_favorites my_date screen_name='philgyford' as favorites %}


.. _twitter-management-commands:

*******************
Management commands
*******************

Fetch Accounts
==============

This only needs to be used whenever a new ``Account`` is added to the system.  It fetches the ``User`` data for each ``Account`` that has API credentials, and associates the two objects.

.. code-block:: shell

    $ ./manage.py fetch_twitter_accounts

Import Tweets
=============

If you have more than 3,200 Tweets, you can only include older Tweets by downloading your archive and importing it. To do so, request your archive at https://twitter.com/settings/account . When you've downloaded it, do:

.. code-block:: shell

    $ ./manage.py import_twitter_tweets --path=/Users/phil/Downloads/12552_dbeb4be9b8ff5f76d7d486c005cc21c9faa61f66

using the correct path to the directory you've downloaded and unzipped (in this case, the unzipped directory is ``12552_dbeb4be9b8ff5f76d7d486c005cc21c9faa61f66``). This will import all of the Tweets found in the archive.

Update Tweets
=============

If you've imported your Tweets (above), you won't yet have complete data about each one. To fully-populate those Tweets you should run this (replacing ``philgyford`` with your Twitter screen name):

.. code-block:: shell

    $ ./manage.py update_twitter_tweets --account=philgyford

This will fetch data for up to 6,000 Tweets. If you have more than that in your archive, run it every 15 minutes to avoid rate limiting, until you've fetched all of the Tweets. This command will fetch data for the least-recently fetched. It's worth running every so often in the future, to fetch the latest data (such as Retweet and Like counts).

Fetch Tweets
============

Periodically you'll want to fetch the latest Tweets. This will fetch only those Tweets posted since you last fetched any:

.. code-block:: shell

    $ ./manage.py fetch_twitter_tweets --account=philgyford --recent=new

You might also, or instead, want to fetch more than that. Here we fetch the most recent 200:

.. code-block:: shell

    $ ./manage.py fetch_twitter_tweets --account=philgyford --recent=200

This would update data such as the Retweet and Like counts for all of the 200 fetched Tweets, even if they're older than your last fetch. It's fine to fetch data about Tweets you've already fetched; their data will be updated.

If you have more than one Twitter Account in Ditto, the above commands can be run across all of them by omitting the ``--account`` option. eg:

.. code-block:: shell

    $ ./manage.py fetch_twitter_tweets --recent=new


Fetch Favorites
===============

To fetch recent Tweets that all your Accounts have favorited/liked, run one of these:

.. code-block:: shell

    $ ./manage.py fetch_twitter_favorites --recent=new
    $ ./manage.py fetch_twitter_favorites --recent=200

Or restrict to Tweets favorited/liked by a single Account:

.. code-block:: shell

    $ ./manage.py fetch_twitter_favorites --account=philgyford --recent=new
    $ ./manage.py fetch_twitter_favorites --account=philgyford --recent=200


Update Users
============

When a Tweet of any kind is fetched, its User data is also stored, and the User's profile photo (avatar) is downloaded and stored in your project's ``MEDIA_ROOT`` directory. You can optionally set the ``DITTO_TWITTER_DIR_BASE`` setting to change the location. The default is::

   DITTO_TWITTER_DIR_BASE = 'twitter'

If your ``MEDIA_ROOT`` was set to ``/var/www/example.com/media/`` then the above setting would save the profile image for the user with a Twitter ID ``12345678`` to something like this:

.. code-block:: shell

    /var/www/example.com/media/twitter/avatars/56/78/12345678/my_avatar.jpg

You may periodically want to update the stored data about all the Twitter users stored in Ditto. (quantity of Tweets, descriptions, etc). Do it like this:

.. code-block:: shell

    $ ./manage.py update_twitter_users --account=philgyford

This requires an ``account`` as the data is fetched from that Twitter user's point of view, when it comes to privacy etc.


Fetch Files (Media)
===================

Fetching Tweets (whether your own or your favorites/likes) fetches all the data *about* them, but does not fetch any media files uploaded with them. There's a separate command for fetching images and the MP4 video files created from animated GIFs. (There's no way to fetch the videos, or original GIF files.)

You *must* first download the Tweet data (above), and then you can fetch the files for all those Tweets:

.. code-block:: shell

    $ ./manage.py fetch_twitter_files

This will fetch the files for all Tweets whose files haven't already been fetched. So, the first time, it's *all* the Tweets' files, which can take a while.

If you want to force a re-fetching of all files, whether they've already been downloaded or not:

.. code-block:: shell

    $ ./manage.py fetch_twitter_files --all

Each image/MP4 is associated with the relevant Tweet(s) and saved within your project's ``MEDIA_ROOT`` directory, as defined in ``settings.py``. There's one optional setting to customise the directory in which the files are saved. Its default value is as shown here::

   DITTO_TWITTER_DIR_BASE = 'twitter'

Files are organised into separate directories according to the final characters
of their file names (so as not to have too many in one directory). eg, an image
might be saved in:

.. code-block:: shell

    /var/www/example.com/media/twitter/media/6T/ay/CRXEfBEWUAA6Tay.png

Every uploaded image, animated GIF and video should have a single image.  Animated GIFs will also have an MP4 file.

Once you've downloaded the original files, you can use these to generate all the different sizes of image required for your site, instead of linking direct to the image files on Twitter. To do this, ensure ``imagekit`` is in your ``INSTALLED_APPS`` setting::

    INSTALLED_APPS = (
        # ...
        'imagekit',
        # ...
    )

And add this to your `settings.py` (its default value is ``False``)::

    DITTO_TWITTER_USE_LOCAL_MEDIA = True

Any requests in your templates for the URLs of photo files of any size will now use resized versions of your downloaded original files, generated by Imagekit.  The first time you load a page (especially if it lists many images) it will be slow, but the images are cached (in a ``CACHE`` directory in your media folder).

For example, before changing this setting, the URL of small image (``Media.small_url``) would be something like this:

.. code-block:: shell

    https://pbs.twimg.com/media/CjuCDVLXIAALhYz.jpg:small

After choosing to use local photos, it would be something like this:

.. code-block:: shell

    /media/CACHE/images/twitter/media/Lh/Yz/CjuCDVLXIAALhYz/5a726ea25d3bbd1b35b21b8b61b98c4c.jpg

If you change your mind you can switch back to using the images hosted on Twitter by removing the ``DITTO_TWITTER_USE_LOCAL_MEDIA`` setting or changing it to ``False``.

Animated GIFs are converted into MP4 videos when first uploaded to Twitter.  Ditto downloads and uses these in a similar way to images. ie, by default the ``video_url`` property of a ``Media`` object that's an Animated GIF would be like:

.. code-block:: shell

    https://pbs.twimg.com/tweet_video/CRXEfBEWUAA6Tay.mp4

If it's been downloaded and ``DITTO_TWITTER_USE_LOCAL_MEDIA`` is ``True`` then
calling ``video_url`` would return a URL like:

.. code-block:: shell

    /media/twitter/media/6T/ay/CRXEfBEWUAA6Tay.mp4

However, there's no way to download actual videos that were uploaded to Twitter, and so Ditto will always try to use videos hosted on Twitter, no matter what the value of ``DITTO_TWITTER_USE_LOCAL_MEDIA``.


