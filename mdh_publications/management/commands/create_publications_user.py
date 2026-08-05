"""Create (or update) an account confined to the MDH Publications Library.

    python manage.py create_publications_user nan --email nan@example.com
    python manage.py create_publications_user dan --role admin

The account is placed in two groups: one granting what it may do inside the
library, and the confinement group that erickvale.middleware.
PublicationsOnlyMiddleware uses to keep it out of the rest of the site.
"""

from getpass import getpass

from django.contrib.auth.models import Group, User
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.password_validation import validate_password

from mdh_publications.permissions import (
    ADMINISTRATOR_GROUP_NAME,
    EMPLOYEE_GROUP_NAME,
    bootstrap_publication_groups,
    publications_only_group_name,
)


class Command(BaseCommand):
    help = "Create or update a login confined to the MDH Publications Library."

    def add_arguments(self, parser):
        parser.add_argument("username")
        parser.add_argument("--email", default="")
        parser.add_argument(
            "--role",
            choices=["employee", "admin"],
            default="employee",
            help=(
                "employee (default): may add publications and view taxonomy. "
                "admin: full control of the library, including user roles."
            ),
        )
        parser.add_argument(
            "--password",
            default="",
            help=(
                "Set non-interactively. Prefer omitting this so the password "
                "is prompted for instead of landing in your shell history."
            ),
        )

    def handle(self, *args, **options):
        username = options["username"].strip()
        if not username:
            raise CommandError("username may not be blank.")

        # Make sure the three groups exist even if post_migrate has not run
        # on this database yet.
        bootstrap_publication_groups()

        password = options["password"]
        if not password:
            password = getpass(f"Password for {username}: ")
            if password != getpass("Password (again): "):
                raise CommandError("Passwords did not match.")
        if not password:
            raise CommandError("Password may not be blank.")

        user, created = User.objects.get_or_create(
            username=username,
            defaults={"email": options["email"]},
        )

        try:
            validate_password(password, user)
        except ValidationError as exc:
            raise CommandError("\n".join(exc.messages)) from exc

        if options["email"]:
            user.email = options["email"]
        # Confined accounts have no business in Django admin.
        user.is_staff = False
        user.is_superuser = False
        user.set_password(password)
        user.save()

        role_group_name = (
            ADMINISTRATOR_GROUP_NAME
            if options["role"] == "admin"
            else EMPLOYEE_GROUP_NAME
        )
        role_group = Group.objects.get(name=role_group_name)
        confine_group = Group.objects.get(name=publications_only_group_name())

        # set() rather than add(): re-running must not leave an account in a
        # role it was moved out of.
        user.groups.set([role_group, confine_group])

        self.stdout.write(
            self.style.SUCCESS(
                f"{'Created' if created else 'Updated'} {username} "
                f"({options['role']}); confined to the publications library."
            )
        )
