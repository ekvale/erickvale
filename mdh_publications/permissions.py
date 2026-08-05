from django.contrib.auth.models import Group, Permission


EMPLOYEE_GROUP_NAME = "MDH Publications Employees"
ADMINISTRATOR_GROUP_NAME = "MDH Publications Administrators"


def bootstrap_publication_groups():
    employee_group, _ = Group.objects.get_or_create(name=EMPLOYEE_GROUP_NAME)
    administrator_group, _ = Group.objects.get_or_create(name=ADMINISTRATOR_GROUP_NAME)

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

    employee_group.permissions.set(employee_permissions)
    administrator_group.permissions.set(administrator_permissions)

    return employee_group, administrator_group