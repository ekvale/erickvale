from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory

from django.contrib.auth.models import Group, User
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase
from django.urls import reverse

from .models import DocumentType, Facet, Publication, Tag, TopicGroup
from .management.commands.seed_mdh_publications_demo import DEMO_PUBLICATIONS
from .permissions import (
    ADMINISTRATOR_GROUP_NAME,
    EMPLOYEE_GROUP_NAME,
    bootstrap_publication_groups,
    publications_only_group_name,
)


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


class PublicationsOnlyConfinementTests(TestCase):
    """Accounts like Nan's and Dan's must reach the library and nothing else.

    Most of this site guards views with only ``login_required``, so these
    assertions are the thing standing between a library account and the
    owner's projects, contacts, calendar, and business dashboards.
    """

    def setUp(self):
        bootstrap_publication_groups()
        out = StringIO()
        call_command(
            "create_publications_user",
            "nan",
            "--email", "nan@example.com",
            "--password", "library-pw-9137",
            stdout=out,
        )
        self.nan = User.objects.get(username="nan")

    def test_command_creates_confined_employee(self):
        group_names = set(self.nan.groups.values_list("name", flat=True))
        self.assertEqual(
            group_names,
            {EMPLOYEE_GROUP_NAME, publications_only_group_name()},
        )
        self.assertFalse(self.nan.is_staff)
        self.assertFalse(self.nan.is_superuser)
        self.assertTrue(self.nan.check_password("library-pw-9137"))

    def test_command_admin_role_and_rerun_replaces_role(self):
        call_command(
            "create_publications_user",
            "dan",
            "--role", "admin",
            "--password", "library-pw-4471",
            stdout=StringIO(),
        )
        dan = User.objects.get(username="dan")
        self.assertEqual(
            set(dan.groups.values_list("name", flat=True)),
            {ADMINISTRATOR_GROUP_NAME, publications_only_group_name()},
        )

        # Re-running with a different role must move, not accumulate.
        call_command(
            "create_publications_user",
            "dan",
            "--role", "employee",
            "--password", "library-pw-4471",
            stdout=StringIO(),
        )
        dan.refresh_from_db()
        self.assertEqual(
            set(dan.groups.values_list("name", flat=True)),
            {EMPLOYEE_GROUP_NAME, publications_only_group_name()},
        )

    def test_confined_user_reaches_the_library(self):
        self.client.force_login(self.nan)
        for name in ("publication_landing", "publication_list", "publication_taxonomy"):
            response = self.client.get(reverse(f"mdh_publications:{name}"))
            self.assertEqual(response.status_code, 200, name)

    def test_confined_user_is_redirected_away_from_the_rest_of_the_site(self):
        self.client.force_login(self.nan)
        # Real routes guarded by login_required alone, i.e. exactly what a
        # logged-in account would otherwise reach.
        for path in (
            "/",
            "/projects/",
            "/projects/dashboard/",
            "/contacts/",
            "/calendar/",
            "/apps/contacts/",
            "/apps/dream-blue/",
            "/apps/braindump/",
            "/admin/",
            "/about/",
        ):
            response = self.client.get(path)
            self.assertEqual(response.status_code, 302, f"{path} was not redirected")
            self.assertEqual(
                response["Location"], "/apps/mdh-publications/", f"{path} went elsewhere"
            )

    def test_superuser_is_never_confined(self):
        """Guards against locking the owner out by mis-assigning the group."""
        owner = User.objects.create_superuser("owner", "owner@example.com", "pw-8823")
        owner.groups.add(Group.objects.get(name=publications_only_group_name()))
        self.client.force_login(owner)
        self.assertEqual(self.client.get("/projects/").status_code, 200)

    def test_unconfined_user_is_unaffected(self):
        plain = User.objects.create_user("plain", "plain@example.com", "pw-5512")
        self.client.force_login(plain)
        response = self.client.get("/apps/mdh-publications/")
        self.assertEqual(response.status_code, 200)


class ShippedTaxonomyTests(TestCase):
    """The taxonomy CSVs shipped in mdh_publications/data/ must import cleanly."""

    def test_seed_command_populates_from_shipped_data_by_default(self):
        call_command("seed_mdh_publications_taxonomy", stdout=StringIO())

        self.assertEqual(Facet.objects.count(), 5)
        self.assertEqual(TopicGroup.objects.count(), 23)
        self.assertEqual(Tag.objects.count(), 127)
        self.assertEqual(DocumentType.objects.count(), 15)

        # Every tag must be wired to both a facet and a topic group, or the
        # taxonomy browser and the search facet filter render gaps.
        self.assertFalse(Tag.objects.filter(facet__isnull=True).exists())
        self.assertFalse(Tag.objects.filter(topic_group__isnull=True).exists())
        self.assertFalse(Tag.objects.filter(description="").exists())
        self.assertFalse(Facet.objects.filter(description="").exists())

        # Topic groups must hang off the same facet as their tags.
        for tag in Tag.objects.select_related("facet", "topic_group__facet"):
            self.assertEqual(tag.facet_id, tag.topic_group.facet_id, tag.slug)

    def test_reseeding_revises_rather_than_duplicates(self):
        call_command("seed_mdh_publications_taxonomy", stdout=StringIO())
        call_command("seed_mdh_publications_taxonomy", stdout=StringIO())

        self.assertEqual(Facet.objects.count(), 5)
        self.assertEqual(TopicGroup.objects.count(), 23)
        self.assertEqual(Tag.objects.count(), 127)
        self.assertEqual(DocumentType.objects.count(), 15)

    def test_taxonomy_browser_renders_the_shipped_taxonomy(self):
        call_command("seed_mdh_publications_taxonomy", stdout=StringIO())
        response = self.client.get(reverse("mdh_publications:publication_taxonomy"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Demographics &amp; Populations")
        self.assertContains(response, "Older Adults")

    def test_sample_seeder_runs_against_the_shipped_taxonomy(self):
        call_command("seed_mdh_publications_taxonomy", stdout=StringIO())
        call_command("seed_mdh_publications_samples", "--count", "5", stdout=StringIO())

        self.assertEqual(Publication.objects.count(), 5)
        self.assertTrue(Publication.objects.filter(tags__isnull=False).exists())


class LibraryChromeTests(TestCase):
    """Guards the CSS framework the page templates actually depend on.

    Every page 200s whether or not its stylesheet resolves, so the original
    route check passed while the pages rendered with no cards, grid, or
    buttons. These assertions pin the specific thing that was broken: the
    templates are Bootstrap 4, and the base must deliver Bootstrap 4.
    """

    def setUp(self):
        self.publication = Publication.objects.create(
            title="Chrome Test Report",
            status=Publication.Status.PUBLISHED,
        )

    def test_pages_load_bootstrap_4_and_the_library_stylesheet(self):
        for url in (
            reverse("mdh_publications:publication_landing"),
            reverse("mdh_publications:publication_list"),
            reverse("mdh_publications:publication_taxonomy"),
            reverse("mdh_publications:publication_about"),
            reverse(
                "mdh_publications:publication_detail",
                kwargs={"slug": self.publication.slug},
            ),
        ):
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200, url)
            body = response.content.decode()
            self.assertIn("bootstrap@4.6", body, f"{url} lost Bootstrap 4")
            self.assertIn("mdh_publications/css/library.css", body, url)

    def test_pages_do_not_load_tailwind(self):
        """Bootstrap 4 and Tailwind both reset globally; never ship both."""
        response = self.client.get(reverse("mdh_publications:publication_list"))
        self.assertNotIn("erickvale/css/tw.css", response.content.decode())


    def test_pages_do_not_leak_template_comments(self):
        """Django's {# #} comment is single-line only.

        Wrapping one across lines makes it render as literal text; that is
        exactly how a note about the mdh-app body class ended up printed at
        the top of every page, above the banner.
        """
        for url in (
            reverse("mdh_publications:publication_landing"),
            reverse("mdh_publications:publication_list"),
            reverse("mdh_publications:publication_taxonomy"),
            reverse("mdh_publications:publication_about"),
            reverse(
                "mdh_publications:publication_detail",
                kwargs={"slug": self.publication.slug},
            ),
        ):
            body = self.client.get(url).content.decode()
            for marker in ("{#", "#}", "{% comment", "{% endcomment"):
                self.assertNotIn(marker, body, f"{url} leaked {marker!r}")


    def test_generic_link_colour_stays_scoped_to_main(self):
        """An unscoped `.pub-body a` rule outranks the component styles.

        At 0-1-1 it beats Bootstrap's .btn-* (0-1-0), painting anchor buttons
        navy on their navy fill. Adding :not(.btn) lifts it to 0-2-1, which
        then beats .pub-nav a and .pub-brand and blanks the masthead. Scoping
        to main is what keeps it clear of both.
        """
        from pathlib import Path

        css = (
            Path(__file__).resolve().parent
            / "static" / "mdh_publications" / "css" / "library.css"
        ).read_text(encoding="utf-8")

        self.assertIn(".pub-body main a:not(.btn)", css)
        for line in css.splitlines():
            selector = line.strip()
            self.assertNotEqual(
                selector, ".pub-body a {", "generic link rule must stay scoped to main"
            )
            self.assertNotEqual(
                selector,
                ".pub-body a:not(.btn) {",
                "unscoped :not(.btn) rule blanks the masthead links",
            )

    def test_every_page_template_extends_the_app_base(self):
        """One template left on base_site.html would silently lose Bootstrap."""
        from pathlib import Path

        template_dir = (
            Path(__file__).resolve().parent / "templates" / "mdh_publications"
        )
        for path in sorted(template_dir.glob("*.html")):
            if path.name == "base.html":
                continue
            first_line = path.read_text(encoding="utf-8").splitlines()[0]
            self.assertIn("mdh_publications/base.html", first_line, path.name)


class DemoContentTests(TestCase):
    def setUp(self):
        call_command("seed_mdh_publications_taxonomy", stdout=StringIO())

    def test_demo_seeder_creates_publications_with_real_tags(self):
        out = StringIO()
        call_command("seed_mdh_publications_demo", stdout=out)

        # Every curated tag slug must exist in the shipped taxonomy, or the
        # demo silently loses the filtering it is meant to show off.
        self.assertNotIn("Tag slugs not found", out.getvalue())

        self.assertEqual(Publication.objects.count(), len(DEMO_PUBLICATIONS))
        self.assertTrue(Publication.objects.filter(is_featured=True).exists())
        self.assertTrue(
            Publication.objects.filter(status=Publication.Status.PUBLISHED).exists()
        )
        for publication in Publication.objects.all():
            self.assertTrue(publication.tags.exists(), publication.title)
            self.assertTrue(publication.summary, publication.title)
            self.assertTrue(publication.abstract, publication.title)
            # facets are derived from tags, so they must agree
            self.assertEqual(
                set(publication.facets.values_list("id", flat=True)),
                set(publication.tags.values_list("facet_id", flat=True)),
                publication.title,
            )

    def test_demo_seeder_is_idempotent(self):
        call_command("seed_mdh_publications_demo", stdout=StringIO())
        call_command("seed_mdh_publications_demo", stdout=StringIO())
        self.assertEqual(Publication.objects.count(), len(DEMO_PUBLICATIONS))

    def test_demo_content_drives_search_and_facet_filtering(self):
        call_command("seed_mdh_publications_demo", stdout=StringIO())
        url = reverse("mdh_publications:publication_list")

        hit = self.client.get(url, {"q": "opioid"})
        self.assertContains(hit, "Opioid Overdose Deaths")

        tagged = self.client.get(url, {"tag": "rural-communities"})
        self.assertContains(tagged, "Rural Primary Care Workforce Capacity")
        self.assertNotContains(tagged, "Language Access in Clinical Settings")

    def test_demo_seeder_requires_taxonomy(self):
        Tag.objects.all().delete()
        DocumentType.objects.all().delete()
        with self.assertRaises(CommandError):
            call_command("seed_mdh_publications_demo", stdout=StringIO())


class PublicationApprovalTests(TestCase):
    """The review workflow: submit, approve, send back.

    publish_publication was declared on the model but enforced nowhere, and
    no view moved a publication out of In Review, so a submission had no
    route to being published.
    """

    def setUp(self):
        employee_group, admin_group = bootstrap_publication_groups()
        self.employee = User.objects.create_user("emp", "emp@example.com", "pw-1122")
        self.employee.groups.add(employee_group)
        self.admin = User.objects.create_user("adm", "adm@example.com", "pw-3344")
        self.admin.groups.add(admin_group)

        self.publication = Publication.objects.create(
            title="Draft Awaiting Review",
            status=Publication.Status.DRAFT,
            created_by=self.employee,
        )

    def test_author_can_submit_own_draft_for_review(self):
        self.client.force_login(self.employee)
        self.client.post(
            reverse(
                "mdh_publications:publication_submit_review",
                kwargs={"slug": self.publication.slug},
            )
        )
        self.publication.refresh_from_db()
        self.assertEqual(self.publication.status, Publication.Status.IN_REVIEW)

    def test_other_user_cannot_submit_someone_elses_draft(self):
        stranger = User.objects.create_user("stranger", "s@example.com", "pw-9911")
        self.client.force_login(stranger)
        response = self.client.post(
            reverse(
                "mdh_publications:publication_submit_review",
                kwargs={"slug": self.publication.slug},
            )
        )
        self.assertEqual(response.status_code, 403)
        self.publication.refresh_from_db()
        self.assertEqual(self.publication.status, Publication.Status.DRAFT)

    def test_administrator_can_approve_and_send_back(self):
        self.publication.status = Publication.Status.IN_REVIEW
        self.publication.save()
        self.client.force_login(self.admin)
        url = reverse(
            "mdh_publications:publication_review_action",
            kwargs={"slug": self.publication.slug},
        )

        self.client.post(url, {"action": "publish"})
        self.publication.refresh_from_db()
        self.assertEqual(self.publication.status, Publication.Status.PUBLISHED)
        self.assertEqual(self.publication.updated_by, self.admin)

        self.client.post(url, {"action": "send_back"})
        self.publication.refresh_from_db()
        self.assertEqual(self.publication.status, Publication.Status.DRAFT)

    def test_employee_cannot_approve(self):
        self.publication.status = Publication.Status.IN_REVIEW
        self.publication.save()
        self.client.force_login(self.employee)
        response = self.client.post(
            reverse(
                "mdh_publications:publication_review_action",
                kwargs={"slug": self.publication.slug},
            ),
            {"action": "publish"},
        )
        self.assertEqual(response.status_code, 403)
        self.publication.refresh_from_db()
        self.assertEqual(self.publication.status, Publication.Status.IN_REVIEW)

    def test_employee_cannot_self_publish_through_the_form(self):
        """add_publication alone used to allow setting status straight to Published."""
        from mdh_publications.forms import PublicationForm

        form = PublicationForm(
            data={
                "title": "Sneaky Self Publish",
                "status": Publication.Status.PUBLISHED,
                "summary": "",
                "abstract": "",
            },
            user=self.employee,
        )
        self.assertFalse(form.is_valid())
        self.assertIn("status", form.errors)

        offered = {value for value, _label in form.fields["status"].choices}
        self.assertEqual(
            offered, {Publication.Status.DRAFT, Publication.Status.IN_REVIEW}
        )

    def test_administrator_may_still_publish_through_the_form(self):
        from mdh_publications.forms import PublicationForm

        form = PublicationForm(
            data={
                "title": "Admin Published",
                "status": Publication.Status.PUBLISHED,
                "summary": "",
                "abstract": "",
            },
            user=self.admin,
        )
        self.assertTrue(form.is_valid(), form.errors)
