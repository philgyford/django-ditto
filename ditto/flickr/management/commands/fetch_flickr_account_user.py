from django.core.management.base import BaseCommand, CommandError

from ...fetch.fetchers import UserIdFetcher, UserFetcher
from ...models import Account, User


class Command(BaseCommand):
    """For fetching data about an Account's Flickr user.

    Should create/update them in our DB, and associate the User with the Account.

        ./manage.py fetch_flickr_account_user --id=1
    """

    help = "Fetches data for an Account's Flickr User"

    def add_arguments(self, parser):
        parser.add_argument(
            "--id",
            action="store",
            default=False,
            help="The ID of the Account in the Django database.",
            type=int,
        )

    def handle(self, *args, **options):
        if options["id"] is False:
            raise CommandError("Specify an Account ID like --id=1")

        # First we need the Account object we're fetching for.
        account = False
        try:
            account = Account.objects.get(id=options["id"])
        except Account.DoesNotExist:
            self.stderr.write("No Account found with an id of '%s'" % options["id"])

        if account:
            # Then get the ID of the Flicker user for this Account's API creds.
            id_result = UserIdFetcher(account=account).fetch()

            if (
                "success" in id_result
                and id_result["success"] is True
                and "id" in id_result
            ):
                # We've got a Flickr ID, so we can get and save the user data.
                result = UserFetcher(account=account).fetch(nsid=id_result["id"])
                if "success" in result and result["success"] is True:
                    # Now we'll associate this User with the Account:
                    user = User.objects.get(nsid="35034346050@N01")
                    account.user = user
                    account.save()
                    if options.get("verbosity", 1) > 0:
                        self.stdout.write(
                            "Fetched and saved user '%s'" % result["user"]["name"]
                        )
                else:
                    if options.get("verbosity", 1) > 0:
                        self.stderr.write(
                            "Failed to fetch a user using Flickr ID '%s': %s"
                            % (id_result["id"], result["messages"][0])
                        )
            else:
                if options.get("verbosity", 1) > 0:
                    self.stderr.write(
                        "Failed to fetch a Flickr ID for this Account: %s"
                        % id_result["messages"][0]
                    )
