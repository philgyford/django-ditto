###########
Development
###########


There's a basic Django project in ``devproject/`` to make it easier to work on
the app. This might be enough to get things up and running:

.. code-block:: shell

    $ pip install -r devproject/requirements.txt
    $ python setup.py develop
    $ ./devproject/manage.py runserver


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

    $ tox -e py35-django19 -- tests.ditto.tests.test_views.DittoViewTests.test_home_templates

Running the tests in all environments will generate coverage output. There will
also be an ``htmlcov/`` directory containing an HTML report. You can also
generaet these reports without running all the other tests:

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

Build the documentation:

.. code-block:: shell

    $ cd docs
    $ make html

Packaging
=========

Set version number in `ditto/pkgmeta.py`.

Rebuild documentation (which includes the version number).

Commit changes to git.

Add a version tag:

.. code-block:: shell

    $ git tag -a v0.2.6 -m "My message"
    $ git push origin --tags

Then, I think:

.. code-block:: shell

    $ python setup.py sdist upload

Maybe just to have the README update on pypi::

    $ python setup.py register


