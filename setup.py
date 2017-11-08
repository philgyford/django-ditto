import codecs
import os
import re
import sys
from setuptools import setup

with open(os.path.join(os.path.dirname(__file__), 'README.rst')) as readme:
    README = readme.read()

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

read = lambda filepath: codecs.open(filepath, 'r', 'utf-8').read()

def get_entity(package, entity):
    """
    eg, get_entity('ditto', 'version') returns `__version__` value in
    `__init__.py`.
    """
    init_py = open(os.path.join(package, '__init__.py')).read()
    find = "__%s__ = ['\"]([^'\"]+)['\"]" % entity
    return re.search(find, init_py).group(1)

def get_version():
    return get_entity('ditto', 'version')

def get_license():
    return get_entity('ditto', 'license')

def get_author():
    return get_entity('ditto', 'author')

def get_author_email():
    return get_entity('ditto', 'author_email')

# Do `python setup.py tag` to tag with the current version number.
if sys.argv[-1] == 'tag':
    os.system("git tag -a %s -m 'version %s'" % (get_version(), get_version()))
    os.system("git push --tags")
    sys.exit()

# Do `python setup.py publish` to send current version to PyPI.
if sys.argv[-1] == 'publish':
    os.system("python setup.py sdist")
    os.system("twine upload --config-file=.pypirc dist/*")
    sys.exit()

# Do `python setup.py testpublish` to send current version to Test PyPI.
# OUT OF DATE
if sys.argv[-1] == 'testpublish':
    os.system("python setup.py sdist upload -r pypitest")
    # os.system("python setup.py bdist_wheel upload")
    sys.exit()

setup(
    name='django-ditto',
    version=get_version(),
    packages=['ditto'],
    install_requires=[
        'django-imagekit>=4.0,<4.1',
        'django-sortedm2m>=1.5.0,<1.6',
        'django-taggit>=0.22.0,<0.30',
        'flickrapi>=2.3,<2.4',
        'pillow>=4.2.1,<4.3',
        'pytz',
        'twitter-text-python',
        'twython>=3.6.0,<3.7',
    ],
    dependency_links=[
    ],
    tests_require=[
        'factory-boy>=2.9.2,<2.10',
        'freezegun>=0.3.9,<0.4',
        'responses>=0.7.0,<0.8',
        'coverage',
    ],
    include_package_data=True,
    license=get_license(),
    description='A Django app to copy stuff from your accounts on Flickr, Last.fm, Pinboard and Twitter.',
    long_description=read(os.path.join(os.path.dirname(__file__), 'README.rst')),
    url='https://github.com/philgyford/django-ditto',
    author=get_author(),
    author_email=get_author_email(),
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
    ],
    keywords='ditto twitter flickr pinboard last.fm',
)
