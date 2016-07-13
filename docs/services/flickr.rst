######
Flickr
######

You can fetch, store and display data about all your Photos and Photosets (Albums) for one or more `Flickr <https://flickr.com/>`_ Accounts. By default the included models and templates will link to the photo files on flickr.com, but you can also download the original files to store locally. These can then be used to generate images in all other sizes, to be served locally.  See the `Fetch Files management command <#fetch-files-media>`_ below.


******
Set-up
******

In the Django admin, create a new ``Account`` in the Flickr app, and add your Flickr API key and secret from https://www.flickr.com/services/apps/create/apply/

By default this will only allow the fetching of fully public photos. To fetch all photos your Flickr account can access, you'll need to do this:

1. Enter your API key and secret in the indicated place in the file
   ``ditto/scripts/flickr_authorize.py``. (If you've installed Ditto using pip,
   it might be easier to `download the script from GitHub <https://github.com/philgyford/django-ditto/blob/master/ditto/scripts/flickr_authorize.py>`_.)

2. Run the script on the command line (if you downloaded the file, change the path to wherever the script is):

    .. code-block:: shell

        $ python ditto/scripts/flickr_authorize.py

3. Follow the instructions. You should get a URL to paste into a web browser,
   in order to authorize your Flickr account. You'll then get a code to paste
   into your Terminal.

Finally, for each of those Accounts, note its ID from the Django admin, and run the following management command to fetch information about its associated Flickr ``User`` (replacing ``1`` with your ``Account``'s Django ID, if different):

.. code-block:: shell

    $ ./manage.py fetch_flickr_account_user --id=1

Now you can download your photos' data and, optionally, their original image/video files. See :ref:`flickr-management-commands`.


******
Models
******

The models available in ``ditto.flickr.models`` are:

``Account``
    Representing a Flickr account that has API credentials and that we fetch Photos for. It has a one-to-one relationship with a ``User`` model.

``TaggedPhoto``
    The through model relating Photos to tags.

``Photo``
    A photo (or video) on Flickr. The ``media_type`` property of ``'photo'`` or ``'video'`` indicates which type this is.

``Photoset``
    A photoset (album) containing Photos.

``User``
    A single user on Flickr. There could be lots of Users but only one (or a few) will have associated Account objects -- these are the Users we fetch Photos for.


********
Managers
********

Photos
======

There are several managers available for Photos. There are two main
differentiators we want to restrict things by:

* **Public vs private:** Whether a Photo is public or private (which includes those marked as for Friends and/or Family on Flickr.com).
* **Posted Photo vs Favorited Photo:** In the future we may fetch Photos that have been favorited, rather than posted, by our Users that have Accounts. In this case we'd want to be able to differentiate between Photos that we posted, and Photos that we favorited.

On public-facing web pages you should only use the mangaers starting ``Photo.public_`` as these will filter out all Photos that are not public.

``Photo.objects.all()``
    The default manager fetches *all* Photos in the system. Public, private, posted by you or (in the future) only favorited by you.

``Photo.public_objects.all()``
    Gets all public Photos in the system, no matter who posted them to Flickr.

``Photo.photo_objects.all()``
    Gets all Photos, public or private, that were posted by one of the Users associated with an API-credentialled Account.

``Photo.public_photo_objects.all()``
    Gets public Photos that were posted by one of the Users associated with an API-credentialled Account.

Of course, these can all be filtered as usual. So, if you wanted to get all the public Photos posted by a particular ``User``::

    from ditto.flickr.models import User, Photo

    user = User.objects.get(nsid='35034346050@N01')
    photos = Photo.public_photo_objects.filter(user=user)

NOTE: You can find a user's NSID (the ID used by Flickr) at http://idgettr.com


Users
=====

``User.objects.all()``
    The default manager fetches all Users in the system.

``User.objects_with_accounts.all()``
    This only gets Users that are associated with Accounts.


*************
Template tags
*************

There are three assigment template tags and one simple template tag available for displaying Photos, Photosets and information about a Photo.

Recent Photos
=============

To display the most recent public Photos posted by any of the Users associated
with Accounts. By default the most recent 10 are fetched:

.. code-block:: django

    {% load ditto_flickr %}

    {% recent_photos as photos %}

    {% for photo in photos %}
        <p>
            {{ photo.title }}<br>
            <img src="{{ photo.small_url }}" width="{{ photo.small_width }}" height="{{ photo.small_height }}">
        </p>
    {% endfor %}

The tag can also fetch a different number of Photos and/or only get Photos
posted by a single User-with-an-Account. Here we only get the 5 most recent
Photos posted by the User with an ``nsid`` of ``'35034346050@N01'``:

.. code-block:: django

    {% recent_photos nsid='35034346050@N01' limit=5 as photos %}

Day Photos
==========

Gets public Photos posted on a particular day by any of the Users-with-Accounts. In this example, ``my_date`` is a `datetime.datetime.date <https://docs.python.org/3.5/library/datetime.html#datetime.date>`_ type:

.. code-block:: django

    {% load ditto_flickr %}

    {% day_photos my_date as photos %}

Or we can restrict this to Photos posted by a single User-with-an-Account:

.. code-block:: django

    {% day_photos my_date nsid='35034346050@N01' as photos %}

Photosets
=========

Gets Photosets. By default they are by any User and only 10 are returned.

.. code-block:: django

    {% load ditto_flickr %}

    {% photosets as photoset_list %}

    {% for photoset in photoset_list %}
        <p>
            {{ photoset.title }}<br>
            <img src="{{ photoset.primary_photo.large_square_url }}" width="{{ photoset.primary_photo.large_square_width }}" height="{{ photoset.primary_photo.large_square_height }}">
        </p>
    {% endfor %}

You can restrict it to Photosets by a single User and/or change the number returned:

.. code-block:: django

    {% load ditto_flickr %}

    {% photosets nsid='35034346050@N01' limit=300 as photoset_list %}

Photo license
=============

When displaying information about a ``Photo`` you may want to display a user-friendly version of its ``license`` (indicating Creative Commons level, All rights reserved, etc). This tag makes that easy. Pass it the ``license`` property of a ``Photo`` object. Here, ``photo`` is a ``Photo`` object:

.. code-block:: django

    {% load ditto_flickr %}

    {{ photo_license photo.license }}

This would create HTML something like this, depending on the license:

    <a href="https://creativecommons.org/licenses/by-nc-sa/2.0/" title="More about permissions">Attribution-NonCommercial-ShareAlike License</a>


.. _flickr-management-commands:

*******************
Management commands
*******************

Fetch Account User
==================

This is only used when setting up a new ``Account`` object with API credentials. It fetches data about the Flickr User associated with this ``Account``.

Once the ``Account`` has been created in the Django admin, and its API credentials entered, run this (using the Django ID for the object instead of ``1``):

.. code-block:: shell

    $ ./manage.py fetch_flickr_account_user --id=1


Fetch Photos
============

Fetches data about Photos (including videos). This will fetch data for ALL Photos for ALL Accounts:

.. code-block:: shell

    $ ./manage.py fetch_flickr_photos --days=all

**NOTE 1:** This took about 75 minutes to fetch data for 3,000 photos on my MacBook.

**NOTE 2:** Trying to run the same thing on a 512MB Digital Ocean machine resulted in the process being killed after fetching about 1,500 photos. See `this bug <https://github.com/philgyford/django-ditto/issues/148>`_.

This will only fetch Photos uploaded in the past 3 days:

.. code-block:: shell

    $ ./manage.py fetch_flickr_photos --days=3

Both options can be restricted to only fetch for a single Account by adding the NSID of the Account's User, eg:

.. code-block:: shell

    $ ./manage.py fetch_flickr_photos --account=35034346050@N01 --days=3

Whenever a Photo is fetched, data about its User will also be fetched, if it hasn't been fetched on this occasion.

Profile photos of Users are downloaded and stored in your project's ``MEDIA_ROOT`` directory. You can optionally set the ``DITTO_FLICKR_DIR_BASE`` setting to change the location. The default is::

   DITTO_FLICKR_DIR_BASE = 'flickr'

If your ``MEDIA_ROOT`` was set to ``/var/www/example.com/media/`` then the above setting would save the profile image for the user with NSID ``35034346050@N01`` to something like this:

.. code-block:: shell

    /var/www/example.com/media/flickr/46/05/35034346050N01/avatars/35034346050N01.jpg

Fetch originals
===============

The ``fetch_flickr_photos`` management command only fetches data *about* the photos (title, locations, EXIF, tags, etc). To download the original photo and video files themselves, use the ``fetch_flickr_originals`` command, *after* fetching the photos' data:

.. code-block:: shell

    $ ./manage.py fetch_flickr_originals

This took over 90 minutes for about 3,000 photos (and very few videos) for me.

By default this command will fetch all the original files that haven't yet been downloaded (so the first time, it will fetch all of them). To force it to download *all* the files again (if you've deleted them locally, but they're still on Flickr) then:

.. code-block:: shell

    $ ./manage.py fetch_flickr_originals --all

Both variants can be restricted to fetching files for a single account:

.. code-block:: shell

    $ ./manage.py fetch_flickr_originals --account=35034346050@N01

Files will be saved within your project's ``MEDIA_ROOT`` directory, as defined in ``settings.py``. There are two optional settings to customise the directories in which the files are saved. Their default values are as shown here::

   DITTO_FLICKR_DIR_BASE = 'flickr'
   DITTO_FLICKR_DIR_PHOTOS_FORMAT = '%Y/%m/%d'

These values are used if you don't specify your own settings.

If your ``MEDIA_ROOT`` was set to ``/var/www/example.com/media/`` then the above settings would save the Flickr photo ``1234567_987654_o.jpg`` to something like this, depending on the Flickr user's NSID and the date the photo was taken (not uploaded):

.. code-block:: shell

    /var/www/example.com/media/flickr/35034346050N01/photos/2016/08/31/1234567_987654_o.jpg

Note that videos will have *two* "original" files downloaded: the video itself and a JPG image that Flickr created for it.

Once you've downloaded the original image files, you can use these to generate all the different sizes of image required for your site, instead of linking direct to the image files on flickr.com. To do this, ensure ``imagekit`` is in your ``INSTALLED_APPS`` setting::

    INSTALLED_APPS = (
        # ...
        'imagekit',
        # ...
    )

And add this to your `settings.py` (its default value is ``False``)::

    DITTO_FLICKR_USE_LOCAL_MEDIA = True

Any requests in your templates for the URLs of photo files of any size will now use resized versions of your downloaded original files, generated by Imagekit.  The first time you load a page (especially if it lists many Flickr images) it will be slow, but the images are cached (in a ``CACHE`` directory in your media folder).

For example, before changing this setting, the URL of small image (``Photo.small_url``) would be something like this:

.. code-block:: shell

    https://farm8.static.flickr.com/7442/27289611500_d0debff24e_m.jpg

After choosing to use local photos, it would be something like this:

.. code-block:: shell

    /media/CACHE/images/flickr/35034346050N01/photos/2016/06/09/27289611500_d21f6f47a0_o/0ee894a3438233848e6e9d85e1985260.jpg

If you change your mind you can switch back to using the images hosted on flickr.com by removing the ``DITTO_FLICKR_USE_LOCAL_MEDIA`` setting or changing it to ``False``.

Note that Ditto currently can't do the same for videos, even if the original video file has been downloaded. No matter what the  value of ``DITTO_FLICKR_USE_LOCAL_MEDIA`` the flickr.com URL for videos is always used.

Fetch Photosets
===============

You can fetch data about your Photosets any time, but it doesn't fetch detailed data about Photos within them.

So, for best results, only run this *after* getting running ``fetch_flickr_photos``.

To fetch Photosets for all Accounts:

.. code-block:: shell

    $ ./manage.py fetch_flickr_photosets

Or fetch for only one Account:

.. code-block:: shell

    $ ./manage.py fetch_flickr_photosets --account=35034346050@N01


