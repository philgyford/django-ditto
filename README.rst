=====
Ditto
=====


Development::

    $ pip install -r demo/requirements.txt
    $ python setup.py develop
    $ ./demo/manage.py test
    $ ./demo/manage.py runserver


Pinboard rate limits: https://pinboard.in/api/#limits

To have numbers formatted nicely, ensure these are in your `settings.py`::

    USE_L10N = True
    USE_THOUSAND_SEPARATOR = True


Using coverage.py::

    $ coverage run --source='.' ./demo/manage.py test
    $ coverage report

Instead of the in-terminal report, get HTML version:

    $ coverage html
    $ open -a "Google Chrome" htmlcov/index.html


