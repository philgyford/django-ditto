=====
Ditto
=====


Development::

    $ pip install -r demo/requirements.txt
    $ python setup.py develop
    $ ./demo/manage.py test
    $ ./demo/manage.py runserver


Well.

Currently getting this error a lot:

/Users/phil/.virtualenvs/django-ditto/lib/python2.7/site-packages/django/db/models/base.py:309: RuntimeWarning: Model 'dittoitem.ditto' was already registered. Reloading models is not advised as it can lead to inconsistencies, most notably with related models.
  new_class._meta.apps.register_model(new_class._meta.app_label, new_class)

Maybe because:
    
    * have the pinboard app inside ditto? Maybe we should make a ditto/core
      app?
    * Can't use django-polymorphic across apps?

So. Maybe should forget the django-polymorphic thing? Just have an Abstract
Base Class, and worry about how best to display lists of different Items later?
Might just be simpler after all. It's only really the 'front' page that we'll
need to do that on I think, and it's currently making everything else much
harder.

