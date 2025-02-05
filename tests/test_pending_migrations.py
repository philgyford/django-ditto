from io import StringIO

from django.core.management import call_command
from django.test import TestCase


class PendingMigrationsTestCase(TestCase):
    def test_no_pending_migrations(self):
        # No migrations pending
        # See: https://adamj.eu/tech/2024/06/23/django-test-pending-migrations/
        out = StringIO()
        try:
            call_command(
                "makemigrations",
                "--check",
                stdout=out,
                stderr=StringIO(),
            )
        except SystemExit:  # pragma: no cover
            raise AssertionError("Pending migrations:\n" + out.getvalue()) from None
