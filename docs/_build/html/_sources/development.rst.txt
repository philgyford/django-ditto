###########
Development
###########


There's a basic Django project in ``devproject/`` to make it easier to work on
the app. This might be enough to get things up and running (assumes pipenv is
installed):

.. code-block:: shell

    $ cd devproject
    $ virtualenv --prompt ditto-devproject venv
    $ source venv/bin/activate
    (ditto-devproject)$ pyenv local 3.10.5
    (ditto-devproject)$ python -m pip install -r requirements.txt

Then run migrations and start the server:

.. code-block:: shell

    (ditto-devproject)$ ./manage.py migrate
    (ditto-devproject)$ ./manage.py runserver

pre-commit will run flake8, black, isort and prettier across all files on commit.
I think you just need to do this first:

.. code-block:: shell

    $ pre-commit install

You can add a `.env` file in `devproject/` and its environment variables will be
read in `devproject/devproject/settings.py`. e.g.:

.. code-block:: shell

    DJANGO_SECRET_KEY="your-secret-key"
    DJANGO_LOG_LEVEL="INFO"


*****
Tests
*****

Run tests with tox. Install it with:

.. code-block:: shell

    $ pip install tox

You'll need to have all versions of python available that are tested against (see ``tox.ini``). This might mean deactivating a virtualenv if you're using one with ``devproject/``. Then run all tests in all environments like:

.. code-block:: shell

    $ tox

To run tests in only one environment, specify it. In this case, Python 3.5 and
Django 1.9:

.. code-block:: shell

    $ tox -e py310-django41

To run a specific test, add its path after ``--``, eg:

.. code-block:: shell

    $ tox -e py35-django19 -- tests.flickr.test_views.HomeViewTests.test_home_templates

Running the tests in all environments will generate coverage output. There will
also be an ``htmlcov/`` directory containing an HTML report. You can also
generate these reports without running all the other tests:

.. code-block:: shell

    $ tox -e coverage


***************************
Other notes for development
***************************

Coverage
========

Using coverage.py to check test coverage:

.. code-block:: shell

    $ coverage run --source='.' ./manage.py test
    $ coverage report

Instead of the in-terminal report, get an HTML version:

.. code-block:: shell

    $ coverage html
    $ open -a "Google Chrome" htmlcov/index.html

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

Set version number in ``ditto/__init__.py``.

Rebuild documentation (which includes the version number).

Ensure ``CHANGELOG.md`` is up-to-date for new version.

Commit changes to git.

Ensure GitHub Actions still build OK.

Add a version tag:

.. code-block:: shell

    $ python setup.py tag

Then:

.. code-block:: shell

    $ python setup.py publish
