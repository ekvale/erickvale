from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory

from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from .models import DocumentType, Facet, Publication, Tag, TopicGroup
from .permissions import ADMINISTRATOR_GROUP_NAME, EMPLOYEE_GROUP_NAME, bootstrap_publication_groups


class PublicationPermissionTests(TestCase):
    def test_group_bootstrap_assigns_expected_permissions(self):
        employee_group, administrator_group = bootstrap_publication_groups()

        self.assertEqual(employee_group.name, EMPLOYEE_GROUP_NAME)
        self.assertEqual(administrator_group.name, ADMINISTRATOR_GROUP_NAME)
        self.assertTrue(employee_group.permissions.filter(codename="add_publication").exists())
        self.assertFalse(employee_group.permissions.filter(codename="change_publication").exists())
        self.assertTrue(administrator_group.permissions.filter(codename="manage_publication_taxonomy").exists())

    def test_employee_inherits_create_but_not_edit_permissions(self):
        employee_group, _ = bootstrap_publication_groups()
        user = User.objects.create_user(username="employee", password="secret")
        user.groups.add(employee_group)

        self.assertTrue(user.has_perm("mdh_publications.add_publication"))
        self.assertFalse(user.has_perm("mdh_publications.change_publication"))
        self.assertFalse(user.has_perm("mdh_publications.delete_publication"))
        self.assertFalse(user.has_perm("mdh_publications.manage_publication_taxonomy"))


class PublicationModelTests(TestCase):
    def test_publication_slug_is_generated_uniquely(self):
        first = Publication.objects.create(title="Annual Report")
        second = Publication.objects.create(title="Annual Report")

        self.assertEqual(first.slug, "annual-report")
        self.assertEqual(second.slug, "annual-report-2")


class TaxonomyImportCommandTests(TestCase):
    def test_command_imports_taxonomy_and_document_types(self):
        with TemporaryDirectory() as temp_dir:
            base_path = Path(temp_dir)
            (base_path / "facets.csv").write_text(
                "facet_code,facet_name,description\nA,Audience,Audience topics\n",
                encoding="utf-8",
            )
            (base_path / "tags_by_facet.csv").write_text(
                "facet_code,facet_name,tag,parent_category,description\nA,Audience,students,age-groups,Student audiences\n",
                encoding="utf-8",
            )
            (base_path / "tags.csv").write_text(
                "tag,facet_code,facet_name,description,parent,examples\nstudents,A,Audience,Student audiences,age-groups,[]\n",
                encoding="utf-8",
            )
            (base_path / "document_types.csv").write_text(
                "document_type\nReport\n",
                encoding="utf-8",
            )

            output = StringIO()
            call_command("seed_mdh_publications_taxonomy", base_dir=str(base_path), stdout=output)

        self.assertEqual(Facet.objects.count(), 1)
        self.assertEqual(TopicGroup.objects.count(), 1)
        self.assertEqual(Tag.objects.count(), 1)
        self.assertEqual(DocumentType.objects.count(), 1)
        self.assertIn("Imported 1 facets", output.getvalue())

    def test_command_imports_from_markdown_when_csv_files_missing(self):
        with TemporaryDirectory() as temp_dir:
            base_path = Path(temp_dir)
            (base_path / "mdh_taxonomy_hierarchical.md").write_text(
                "\n".join(
                    [
                        "## LEVEL 2: TYPES (Document Formats)",
                        "- Report",
                        "## LEVEL 3: TAGS (Faceted Taxonomy)",
                        "### FACET A: DEMOGRAPHICS & POPULATIONS",
                        "#### Age Groups",
                        "- **children**: Pediatric populations",
                    ]
                ),
                encoding="utf-8",
            )

            call_command("seed_mdh_publications_taxonomy", base_dir=str(base_path))

        self.assertEqual(Facet.objects.count(), 1)
        self.assertEqual(TopicGroup.objects.count(), 1)
        self.assertEqual(Tag.objects.count(), 1)
        self.assertEqual(DocumentType.objects.count(), 1)


class PublicationFilterTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_superuser(
            username="admin_filter",
            password="secret",
            email="admin_filter@example.com",
        )

        self.facet_a = Facet.objects.create(code="A", name="Demographics", sort_order=1)
        self.facet_b = Facet.objects.create(code="B", name="Conditions", sort_order=2)
        self.group_a = TopicGroup.objects.create(facet=self.facet_a, slug="age-groups", name="Age Groups")
        self.group_b = TopicGroup.objects.create(facet=self.facet_b, slug="cancer", name="Cancer")
        self.tag_a = Tag.objects.create(
            facet=self.facet_a,
            topic_group=self.group_a,
            slug="children",
            name="Children",
        )
        self.tag_b = Tag.objects.create(
            facet=self.facet_b,
            topic_group=self.group_b,
            slug="cancer-screening",
            name="Cancer Screening",
        )
        self.report_type = DocumentType.objects.create(name="Report", slug="report")

        self.publication_a = Publication.objects.create(
            title="Child Health Access Report",
            document_type=self.report_type,
            status=Publication.Status.PUBLISHED,
        )
        self.publication_a.tags.add(self.tag_a)
        self.publication_a.facets.add(self.facet_a)

        # Must be PUBLISHED: the public search view filters to published
        # rows, so a draft here would be invisible regardless of tag/facet.
        self.publication_b = Publication.objects.create(
            title="Cancer Screening Brief",
            document_type=self.report_type,
            status=Publication.Status.PUBLISHED,
        )
        self.publication_b.tags.add(self.tag_b)
        self.publication_b.facets.add(self.facet_b)

    def test_filter_by_tag_returns_expected_publication(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("mdh_publications:publication_list"), {"tag": self.tag_a.slug})

        self.assertContains(response, self.publication_a.title)
        self.assertNotContains(response, self.publication_b.title)

    def test_filter_by_multiple_tags_returns_union(self):
        self.client.force_login(self.user)
        response = self.client.get(
            reverse("mdh_publications:publication_list"),
            {"tag": [self.tag_a.slug, self.tag_b.slug]},
        )

        self.assertContains(response, self.publication_a.title)
        self.assertContains(response, self.publication_b.title)

    def test_filter_by_facet_returns_expected_publication(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("mdh_publications:publication_list"), {"facet": self.facet_b.code})

        self.assertContains(response, self.publication_b.title)
        self.assertNotContains(response, self.publication_a.title)


class PublicationAccessTests(TestCase):
    def setUp(self):
        self.facet = Facet.objects.create(code="A", name="Demographics", sort_order=1)
        self.group = TopicGroup.objects.create(facet=self.facet, slug="age-groups", name="Age Groups")
        self.tag = Tag.objects.create(facet=self.facet, topic_group=self.group, slug="adults", name="Adults")
        self.doc_type = DocumentType.objects.create(name="Report", slug="report")
        self.publication = Publication.objects.create(title="Public Report", document_type=self.doc_type)
        self.publication.tags.add(self.tag)
        self.publication.facets.add(self.facet)

        self.employee_group, self.admin_group = bootstrap_publication_groups()
        self.employee = User.objects.create_user(username="emp_user", password="secret")
        self.employee.groups.add(self.employee_group)
        self.admin_user = User.objects.create_user(username="admin_user", password="secret")
        self.admin_user.groups.add(self.admin_group)

    def test_public_can_view_list_detail_and_taxonomy(self):
        list_response = self.client.get(reverse("mdh_publications:publication_list"))
        detail_response = self.client.get(reverse("mdh_publications:publication_detail", kwargs={"slug": self.publication.slug}))
        taxonomy_response = self.client.get(reverse("mdh_publications:publication_taxonomy"))

        self.assertEqual(list_response.status_code, 200)
        self.assertEqual(detail_response.status_code, 200)
        self.assertEqual(taxonomy_response.status_code, 200)

    def test_employee_can_add_but_cannot_edit_or_delete(self):
        self.client.force_login(self.employee)
        add_response = self.client.get(reverse("mdh_publications:publication_create"))
        edit_response = self.client.get(reverse("mdh_publications:publication_update", kwargs={"slug": self.publication.slug}))
        delete_response = self.client.get(reverse("mdh_publications:publication_delete", kwargs={"slug": self.publication.slug}))

        self.assertEqual(add_response.status_code, 200)
        self.assertEqual(edit_response.status_code, 403)
        self.assertEqual(delete_response.status_code, 403)

    def test_administrator_can_edit_and_delete(self):
        self.client.force_login(self.admin_user)
        edit_response = self.client.get(reverse("mdh_publications:publication_update", kwargs={"slug": self.publication.slug}))
        delete_response = self.client.get(reverse("mdh_publications:publication_delete", kwargs={"slug": self.publication.slug}))

        self.assertEqual(edit_response.status_code, 200)
        self.assertEqual(delete_response.status_code, 200)

    def test_dashboard_router_redirects_by_role(self):
        self.client.force_login(self.employee)
        employee_redirect = self.client.get(reverse("mdh_publications:publication_dashboard"))
        self.assertRedirects(employee_redirect, reverse("mdh_publications:publication_employee_dashboard"), fetch_redirect_response=False)

        public_user = User.objects.create_user(username="plain_user", password="secret")
        self.client.force_login(public_user)
        public_redirect = self.client.get(reverse("mdh_publications:publication_dashboard"))
        self.assertRedirects(public_redirect, reverse("mdh_publications:publication_employee_dashboard"), fetch_redirect_response=False)

        self.client.force_login(self.admin_user)
        admin_redirect = self.client.get(reverse("mdh_publications:publication_dashboard"))
        self.assertRedirects(admin_redirect, reverse("mdh_publications:publication_admin_dashboard"), fetch_redirect_response=False)

    def test_employee_dashboard_access(self):
        self.client.force_login(self.employee)
        allowed = self.client.get(reverse("mdh_publications:publication_employee_dashboard"))
        self.assertEqual(allowed.status_code, 200)

        self.client.force_login(self.admin_user)
        also_allowed = self.client.get(reverse("mdh_publications:publication_employee_dashboard"))
        self.assertEqual(also_allowed.status_code, 200)

    def test_admin_dashboard_access_and_role_update(self):
        self.client.force_login(self.admin_user)
        allowed = self.client.get(reverse("mdh_publications:publication_admin_dashboard"))
        self.assertEqual(allowed.status_code, 200)

        self.client.force_login(self.employee)
        denied = self.client.get(reverse("mdh_publications:publication_admin_dashboard"))
        self.assertEqual(denied.status_code, 403)

        self.client.force_login(self.admin_user)
        target_user = User.objects.create_user(username="public_user", password="secret")
        update_response = self.client.post(
            reverse("mdh_publications:publication_admin_dashboard"),
            {"user_id": target_user.id, "role": "employee"},
            follow=True,
        )

        target_user.refresh_from_db()
        self.assertEqual(update_response.status_code, 200)
        self.assertTrue(target_user.groups.filter(name=EMPLOYEE_GROUP_NAME).exists())
