Pinboard
########

You can fetch, store and display data about all your bookmarks for one or more `Pinboard <https://pinboard.in/>`_ accounts.


Set-up
******

In the Django admin, add an Account in the Pinboard app with your API token from https://pinboard.in/settings/password .


Bookmarks
*********

Import all of your bookmarks:

.. code-block:: shell

    $ ./manage.py fetch_pinboard_bookmarks --all

Periodically fetch the most recent bookmarks, eg 20 of them:

.. code-block:: shell

    $ ./manage.py fetch_pinboard_bookmarks --recent=20

Or fetch bookmarks posted on one date:

.. code-block:: shell

    $ ./manage.py fetch_pinboard_bookmarks --date=2015-06-20

Or fetch a single bookmark by its URL (eg, if you've changed the description
of a particular bookmark you've alread fetched):

.. code-block:: shell

    $ ./manage.py fetch_pinboard_bookmarks --url=http://new-aesthetic.tumblr.com/

The above commands fetch bookmark(s) for all Accounts you've added. To restrict to a single account use ``--account`` with the Pinboard username, eg:

.. code-block:: shell

    $ ./manage.py fetch_pinboard_bookmarks --all --account=philgyford

Be aware of the rate limits: https://pinboard.in/api/#limits


