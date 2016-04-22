import os
from setuptools import setup

with open(os.path.join(os.path.dirname(__file__), 'README.rst')) as readme:
    README = readme.read()

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name='django-ditto',
    version='0.1',
    packages=['ditto'],
    install_requires=[
        'django-taggit',
        'flickrapi',
        'pytz',
        'twython==3.3.0',
    ],
    dependency_links=[
        # The v3.3.0 of twython on pypi isn't as up-to-date as the v3.3.0
        # on GitHub, and we want the GitHub version.
        'git+ssh://github.com/ryanmcgrath/twython.git@3.3.0#egg=twython-3.3.0',
    ],
    tests_require=[
        'factoryboy',
    ],
    include_package_data=True,
    license='MIT License',
    description='A Django app to copy stuff from your accounts on other services.',
    long_description=README,
    url='https://github.com/philgyford/django-ditto',
    author='Phil Gyford',
    author_email='phil@gyford.com',
    classifiers=[
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3 :: Only',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
    ],
)
