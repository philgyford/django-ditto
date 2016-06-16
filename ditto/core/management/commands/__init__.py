from django.core.management.base import BaseCommand, CommandError


class DittoBaseCommand(BaseCommand):
    """
    Should probably be used as a parent by all other management commands,
    assuming they follow the usual pattern.

    Provides an output_results() method for our usual format of results.
    """

    # What we're fetching:
    singular_noun = 'Thing'
    plural_noun = 'Things'

    def add_arguments(self, parser):
        "We may add stuff for handling verbosity here."
        pass

    def output_results(self, results, verbosity=1):
        """results should be a list of dicts.

        Each dict is for one account.
        Each dict will look like either:

          { 'account': 'Phil Gyford',
            'success': True,
            'fetched': 200, # The number of things fetched
          }

        or:

          { 'account': 'Phil Gyford',
            'success': False,
            'messages': ['There was an error fetching data because blah'],
          }

        Or, it might not have an 'account'.
        """
        if verbosity == 0:
            return

        for result in results:
            prefix = '%s: ' % result['account'] if 'account' in result else ''
            if 'fetched' in result:
                noun = self.singular_noun if result['fetched'] == 1 else self.plural_noun
                self.stdout.write('%sFetched %s %s' % (
                                            prefix, result['fetched'], noun))

            if result['success'] == False:
                self.stderr.write('%sFailed to fetch %s: %s' % (
                                    prefix,
                                    self.plural_noun,
                                    self.format_messages(result['messages'])
                                ))

    def format_messages(self, messages):
        if len(messages) == 1:
            return messages[0]
        else:
            # On separate lines, and start a newline first.
            return "%s%s" % ("\n", "\n".join(messages))


