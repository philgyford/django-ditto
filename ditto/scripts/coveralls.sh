set -e

# Called from .travis.yml after the coverage bulid of the tests has run.
# This should then run the `coveralls` command to get coverage on coveralls.io.

if [ "$TRAVIS_BRANCH" == "master" ] && [ "$TOX_ENV" == "coverage" ] && [ "$TRAVIS_PULL_REQUEST" == "false" ]; then
  coveralls
fi

