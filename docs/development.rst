###########
Development
###########


*************************
Creating a Django project
*************************

How I would create a new project to work on django-ditto's code.

1. Check out django-ditto
2. Create an empty directory at the same level as django-ditto, like ``django-ditto-devproject``.
3. On the command line do the following:

   .. code-block:: shell

      cd django-ditto-devproject
      uv init
      rm hello.py  # Created by uv init but we don't need it
      uv add --editable ./../django-ditto
      uv run django-admin startproject devsite .

4. In ``devsite/settings.py`` add these to ``INSTALLED_APPS``:

   .. code-block:: python

       "sortedm2m",
       "taggit",
       "ditto.core",
       "ditto.flickr",
       "ditto.lastfm",
       "ditto.pinboard",
       "ditto.twitter",

5. On the command line o:

   .. code-block:: shell

      uv run manage.py migrate

6. In ``devproject/urls.py`` add these to ``urlpatterns``:

   .. code-block:: python

       path(r"flickr/", include("ditto.flickr.urls")),
       path(r"lastfm/", include("ditto.lastfm.urls")),
       path(r"pinboard/", include("ditto.pinboard.urls")),
       path(r"twitter/", include("ditto.twitter.urls")),
       path(r"", include("ditto.core.urls")),

7. On the command line do:

   .. code-block:: shell

      uv run manage.py runserver

8. You can then visit http://127.0.0.1:8000 to view the Django-spectator front page. Use ``uv run manage.py createsuperuser`` as normal with a Django project to create a superuser.

**********
pre-commit
**********

pre-commit will run flake8, black, isort and prettier across all files on commit.
I think you just need to do this first:

.. code-block:: shell

    $ pre-commit install

*****
Tests
*****

Run tests with tox. Install it with:

.. code-block:: shell

    $ pip install tox

You'll need to have all versions of python available that are tested against (see ``tox.ini``). This might mean deactivating a virtualenv if you're using one with ``devproject/``. Then run all tests in all environments like:

.. code-block:: shell

    $ tox

To run tests in only one environment, specify it. In this case, Python 3.13 and
Django 4.2:

.. code-block:: shell

    $ tox -e py313-django51

To run a specific test, add its path after ``--``, eg:

.. code-block:: shell

    $ tox -e py313-django51 -- tests.flickr.test_views.HomeViewTests.test_home_templates

Running the tests in all environments will generate coverage output. There will
also be an ``htmlcov/`` directory containing an HTML report. You can also
generate these reports without running all the other tests:

.. code-block:: shell

    $ tox -e coverage


***************************
Other notes for development
***************************

Documentation
=============

You'll need `sphinx <http://www.sphinx-doc.org/en/master/>`_ installed. You
could do this using pip and the ``requirements.txt`` file:

.. code-block:: shell

    $ cd docs
    $ virtualenv --prompt ditto-docs venv
    $ source venv/bin/activate
    (ditto-docs)$ python -m pip install -r requirements.txt

Build the documentation:

.. code-block:: shell

    (ditto-docs)$ make html

Packaging
=========

Replace ``4.0.1`` with current version number:

1. Put new changes on ``main``.
2. Set version number in ``src/ditto/__init__.py``
3. Rebuild documentation (which includes the version number).
4. Update ``CHANGELOG.md``.
5. Commit code.
6. ``git tag -a 4.0.1 -m 'version 4.0.1'``
7. ``git push --tags``
8. ``uv build``
9. ``uv publish dist/django_ditto-4.0.1*``
