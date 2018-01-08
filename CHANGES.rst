Changelog (Django Ditto)
========================

0.7.6
-----

- Fix an error when fetching a Flickr user's data if they didn't have 'location'
  or 'timezone' data set.


0.7.5
-----

- Fix display of images (Twitter avatars and images, Flickr avatars and images)
  in the Django Admin pages.


0.7.4
-----

- When fetching Twitter favorites, fetches the extended version of the tweets
  and includes entities.

- Temporarily use a different specific version of Twython (see README or docs).


0.7.3
-----

- Handles tweets longer than 255 characters without Postgres complaining (SQLite
  quietly carried on).

- Fetches extended tweet data when fetching recent tweets.

- Temporarily requires manual inclusion of a specific version of Twython in your
  project's pip requirements (see README or docs).


0.7.2
-----

- Add missing migrations for Flickr and Last.fm.


0.7.1
-----

- For Last.fm template tags, rely on the ``FIRST_DAY_OF_WEEK`` Django setting,
  instead of the now unused ``DITTO_WEEK_START`` setting.


0.7.0
-----

- Add support Django 2.0; drop support for Django 1.10.

- Upgrade Bootstrap from v4 beta 1 to v4 beta 3.


0.6.5
-----

- Increase the maximum length of a Twitter User's display name to 50 characters.


0.6.4
-----

- The Flickr ``day_photos`` template tag can now fetch photos taken on
  a particular day, as well as posted on a day.


0.6.3
-----

- The Last.fm template tags for the top albums, artists and tracks can now
  display the top list for a week, as well as day, month and year.


0.6.2
-----

- Added the ``popular_bookmark_tags`` template tag to the ``pinboard`` app.


0.6.1
-----

- Fix bug when importing Flickr photos and there's already a tag with a
  different ``slug`` but the same ``name``.


0.6.0
-----

- The ditto context_processor is no longer required, and now does nothing.

- Replaced its ``enabled_apps`` with a ``get_enabled_apps`` template tag.


0.5.2
-----

- Fix screenshots URL in README and documentation.


0.5.0
-----

- Upgrade Bootstrap to v4-beta #189, #180

- Add Bootstrap and jQuery to make navigation bar collapsible

- Test it works in Django 1.11 #185

- Label the ``core`` app as ``ditto_core`` #186

- Upgrade dependencies #188

- Removed ``current_url_name`` from context processor and made it a template tag
  #184

- Moved Bootsrap CSS into a ``css`` directory #182

- Change 'scrobbles' to 'listens' on day archive #181
