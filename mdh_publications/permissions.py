from django.conf import settings
from django.contrib.auth.models import Group, Permission


EMPLOYEE_GROUP_NAME = "MDH Publications Employees"
EDITOR_GROUP_NAME = "MDH Publications Editors"
ADMINISTRATOR_GROUP_NAME = "MDH Publications Administrators"

# Editors do the editorial work -- approve submissions, curate the taxonomy --
# without inheriting manage_publication_roles, which grants control over every
# site user's access. Keeping that one permission with administrators is the
# whole point of having a middle role.
ROLE_MANAGEMENT_PERMISSION = "manage_publication_roles"


def publications_only_group_name():
    """Group that confines an account to /apps/mdh-publications/.

    Carries no permissions of its own — enforcement lives in
    erickvale.middleware.PublicationsOnlyMiddleware. Pair it with one of the
    two groups above to grant what the account may actually do in the library.
    """
    return getattr(settings, "PUBLICATIONS_ONLY_GROUP", "MDH Publications Only")


def bootstrap_publication_groups():
    employee_group, _ = Group.objects.get_or_create(name=EMPLOYEE_GROUP_NAME)
    editor_group, _ = Group.objects.get_or_create(name=EDITOR_GROUP_NAME)
    administrator_group, _ = Group.objects.get_or_create(name=ADMINISTRATOR_GROUP_NAME)
    Group.objects.get_or_create(name=publications_only_group_name())

    employee_permissions = Permission.objects.filter(
        content_type__app_label="mdh_publications",
        codename__in={
            "add_publication",
            "view_publication",
            "view_facet",
            "view_topicgroup",
            "view_tag",
            "view_documenttype",
        },
    )

    administrator_permissions = Permission.objects.filter(
        content_type__app_label="mdh_publications"
    )

    # Everything an administrator has, minus control over user roles.
    editor_permissions = administrator_permissions.exclude(
        codename=ROLE_MANAGEMENT_PERMISSION
    )

    employee_group.permissions.set(employee_permissions)
    editor_group.permissions.set(editor_permissions)
    administrator_group.permissions.set(administrator_permissions)

    return employee_group, administrator_group