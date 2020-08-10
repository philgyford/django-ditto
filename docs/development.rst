###########
Development
###########


There's a basic Django project in ``devproject/`` to make it easier to work on
the app. This might be enough to get things up and running (assumes pipenv is
installed):

.. code-block:: shell

    $ cd devproject
    $ pipenv install
    $ pipenv run ./manage.py migrate
    $ pipenv run ./manage.py runserver

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

    $ tox -e py35-django19

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
could do this using pipenv and the Pipfiles:

.. code-block:: shell

    $ cd docs
    $ pipenv install

Build the documentation (assuming usage of pipenv):

.. code-block:: shell

    $ cd docs
    $ pipenv run make html

Packaging
=========

Set version number in ``ditto/__init__.py``.

Rebuild documentation (which includes the version number).

Ensure ``CHANGES.rst`` is up-to-date for new version.

Commit changes to git.

Add a version tag:

.. code-block:: shell

    $ python setup.py tag

Ensure Travis still builds OK.

Then:

.. code-block:: shell

    $ python setup.py publish
