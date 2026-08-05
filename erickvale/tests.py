from django.conf import settings
from django.contrib.auth.models import User
from django.test import TestCase
from django.utils.module_loading import import_string


class TemplateConfigurationTests(TestCase):
    def test_every_configured_context_processor_is_importable(self):
        """A dangling context processor 500s every page render.

        settings.py once referenced nomoar.context_processors.nomoar_site_links
        while that function existed only in an uncommitted working tree, so a
        clean checkout raised on any template render and production had to be
        hand-patched to stay up. Django resolves these lazily, so nothing
        catches it until a page is served — hence this test.
        """
        for engine in settings.TEMPLATES:
            for dotted_path in engine.get("OPTIONS", {}).get("context_processors", []):
                with self.subTest(context_processor=dotted_path):
                    import_string(dotted_path)


class SiteNavigationTests(TestCase):
    def test_homepage_renders_for_anonymous_visitor(self):
        """Exercises the real template stack, context processors included."""
        with self.settings(SITE_COMING_SOON=False):
            self.assertEqual(self.client.get("/").status_code, 200)

    def test_homepage_renders_for_authenticated_user(self):
        user = User.objects.create_user("navtest", "navtest@example.com", "pw-3391")
        self.client.force_login(user)
        with self.settings(SITE_COMING_SOON=False):
            self.assertEqual(self.client.get("/").status_code, 200)
