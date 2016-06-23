import codecs
import os
from setuptools import setup

with open(os.path.join(os.path.dirname(__file__), 'README.rst')) as readme:
    README = readme.read()

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

read = lambda filepath: codecs.open(filepath, 'r', 'utf-8').read()

# Load package meta from the pkgmeta module without loading ditto.
pkgmeta = {}
# Python 3 replacement for execfile(pkgmeta_path, pkgmeta):
pkgmeta_path = os.path.join(os.path.dirname(__file__), 'ditto', 'pkgmeta.py')
with open(pkgmeta_path, 'r') as f:
    code = compile(f.read(), pkgmeta_path, 'exec')
    exec(code, pkgmeta)

setup(
    name=pkgmeta['__title__'],
    version=pkgmeta['__version__'],
    packages=['ditto'],
    install_requires=[
        'django-imagekit>=3.3,<3.4',
        'django-sortedm2m>=1.2.2,<1.3',
        'django-taggit',
        'flickrapi',
        'pillow>=3.2.0,<3.3',
        'pytz',
        'twitter-text-python',
        'twython>=3.4.0,<3.5',
    ],
    dependency_links=[
    ],
    tests_require=[
        'factory-boy',
        'freezegun',
        'responses',
    ],
    test_suite='runtests.runtests',
    include_package_data=True,
    license=pkgmeta['__license__'],
    description='A Django app to copy stuff from your accounts on Flickr, Pinboard and Twitter.',
    long_description=read(os.path.join(os.path.dirname(__file__), 'README.rst')),
    url='https://github.com/philgyford/django-ditto',
    author=pkgmeta['__author__'],
    author_email=pkgmeta['__author_email__'],
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
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
    ],
    keywords='ditto twitter flickr pinboard',
)
