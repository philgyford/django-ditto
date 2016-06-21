Twitter
#######

You can fetch, store and display data about your own Tweets and Liked Tweets for one or more `Twitter <https://twitter.com/>`_ accounts. By default the included models and templates will link to image and video files at Twitter, but you can also download the original files to store locally. These can then be used to serve different sizes of images locally.


Set-up
******

In the Django admin, add a new Account in the Twitter app, with your API credentials from https://apps.twitter.com/ .

Then you *must* do:

.. code-block:: shell

    $ ./manage.py fetch_twitter_accounts

which will fetch the data for that Account's Twitter user.


Tweets
******

If you have more than 3,200 Tweets, you can only include older Tweets by downloading your archive and importing it. To do so, request your archive at https://twitter.com/settings/account . When you've downloaded it, do:

.. code-block:: shell

    $ ./manage.py import_twitter_tweets --path=/Users/phil/Downloads/12552_dbeb4be9b8ff5f76d7d486c005cc21c9faa61f66

using the correct path to the directory you've downloaded and unzipped (in this case, the unzipped directory is ``12552_dbeb4be9b8ff5f76d7d486c005cc21c9faa61f66``). This will import all of the Tweets found in the archive. The data in the archive isn't complete, so to fully-populate those Tweets you should run this (replacing ``philgyford`` with your Twitter screen name):

.. code-block:: shell

    $ ./manage.py update_twitter_tweets --account=philgyford

This will fetch data for up to 6,000 Tweets. If you have more than that in your archive, run it every 15 minutes to avoid rate limiting, until you've fetched all of the Tweets. This command will fetch data for the least-recently fetched. It's worth running every so often in the future, to fetch the latest data (such as Retweet and Like counts).

If there are newer Tweets, not in your downloaded archive, then run this:

.. code-block:: shell

    $ ./manage.py fetch_twitter_tweets --account=philgyford --recent=3200

The ``3200`` is the number of recent Tweets to fetch, with ``3200`` being the maximum allowed in one go.

Run this version periodically to fetch the Tweets since you last fetched any:

.. code-block:: shell

    $ ./manage.py fetch_twitter_tweets --account=philgyford --recent=new

You might also, or instead, want to fetch more than that, eg:

.. code-block:: shell

    $ ./manage.py fetch_twitter_tweets --account=philgyford --recent=200

This would update data such as the Retweet and Like counts for all of the 200
fetched Tweets, even if they're older than your last fetch.

If you have more than one Twitter Account in Ditto, the above commands can be
run across all of them by omitting the ``--account`` option. eg:

.. code-block:: shell

    $ ./manage.py fetch_twitter_tweets --recent=new


Favorites/Likes
***************

To fetch recent Tweets that that all your Accounts have liked, run one of these:

.. code-block:: shell

    $ ./manage.py fetch_twitter_favorites --recent=new
    $ ./manage.py fetch_twitter_favorites --recent=200

Or restrict to Tweets liked by a single Account:

.. code-block:: shell

    $ ./manage.py fetch_twitter_favorites --account=philgyford --recent=new
    $ ./manage.py fetch_twitter_favorites --account=philgyford --recent=200


Users
*****

When a Tweet of any kind is fetched, its User data is also stored, and the User's profile photo (avatar) is downloaded and stored in your project's ``MEDIA_ROOT`` directory. You can optionally set the ``DITTO_TWITTER_DIR_BASE`` setting to change the location. The default is::

   DITTO_TWITTER_DIR_BASE = 'twitter'

If your ``MEDIA_ROOT`` was set to ``/var/www/example.com/media/`` then the above setting would save the profile image for the user with a Twitter ID ``12345678`` to something like this:

.. code-block:: shell

    /var/www/example.com/media/twitter/avatars/56/78/12345678/my_avatar.jpg

You may periodically want to update the stored data about all the Twitter users
stored in Ditto. (quantity of Tweets, descriptions, etc). Do it like this:

.. code-block:: shell

    $ ./manage.py update_twitter_users --account=philgyford

This requires an ``account`` as the data is fetched from that Twitter user's point of view, when it comes to privacy etc.


Images
******

Fetching Tweets (whether your own or your Likes) fetches all the data *about* them, but does not fetch any media files uploaded with them. (It's not possible to fetch video files (as far as I can tell.) There's a separate command for fetching images and the MP4 video files for animated GIFs. (There's no way to fetch the original GIF files.)

You *must* first download the Tweet data, and then fetch the files for all those Tweets:

.. code-block:: shell

    $ ./manage.py fetch_twitter_files

This will fetch the files for all Tweets whose files haven't already been fetched (so, the first time, it's all the Tweets).

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


