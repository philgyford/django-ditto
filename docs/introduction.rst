############
Introduction
############

A collection of Django apps for copying things from third-party sites and services. This is still in-progress and things may change. If something doesn't make sense, `email Phil Gyford <mailto:phil@gyford.com>`_ and I'll try and clarify it.

Requires Python 3.4 or 3.5, and Django 1.8 or 1.9.


****************
Services covered
****************

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
    - Images and Animated GIFs (but not videos)
    - Users

It can save these things for one or more account on each service.

See possible future services, and overall progress, in `this issue <https://github.com/philgyford/django-ditto/issues/23>`_.

Public and private Photos, Bookmarks and Tweets are saved, but only public ones are used in the included Views, Templates and Template tags; non-public data are only visible in the Django admin.

Ditto does not *sync* data -- it's a one-way fetch of data *from* the service *to* Ditto. You can repeatedly fetch the same Photos, Tweets, etc and their data will be overwritten in Ditto. You could do a single fetch of all your data as a snapshot/archive. And/or, after that, keep fetching the latest items to keep it up-to-date.

For each item fetched, the original JSON data is saved on its object.


*******************
What Ditto includes
*******************

The Ditto apps provide:

- Models
- Admin
- Management commands to fetch the data/files
- Views and URLs
- Templates (that use `Bootstrap 4 <http://v4-alpha.getbootstrap.com>`_)
- Template tags for common things (eg, most recent Tweets, or Flickr photos uploaded on a particular day)

You could use the whole lot to create a minimal site that displays your Tweets,
photos, etc – see the ``devproject/`` for a bare-bones example.

Or you might want to use the management commands, Models and Admin to fetch and
store your data, but use that data in your own Views and Templates, maybe using
the Template tags. Or some other combination.


