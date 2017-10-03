Changelog (Django Ditto)
========================

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

