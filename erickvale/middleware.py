"""
Site-wide middleware.

``SiteComingSoonMiddleware`` implements the optional public "coming soon"
curtain: when SITE_COMING_SOON is True, anonymous requests are redirected to
the coming-soon page (except auth, admin, static assets, and similar).
Authenticated users always reach the real site.

``PublicationsOnlyMiddleware`` confines accounts that exist solely to use the
MDH Publications Library. Most of this site's apps (projects/, contacts/,
calendar/, dream-blue/) guard their views with nothing stronger than
``login_required``, so *any* account that can log in would otherwise reach
personal projects, contacts, and business dashboards. Rather than audit and
re-gate every one of those views, membership of a single group confines an
account to an explicit allowlist of paths.
"""

from __future__ import annotations

from urllib.parse import quote

from django.conf import settings
from django.shortcuts import redirect


def _path_allowed(path: str) -> bool:
    """Paths that anonymous users may hit while the curtain is up."""
    if path in ("/favicon.ico", "/robots.txt", "/sitemap.xml"):
        return True
    if path == "/coming-soon" or path.startswith("/coming-soon/"):
        return True
    prefixes = (
        "/admin/",
        "/login/",
        "/logout/",
        "/static/",
        "/media/",
        "/ckeditor/",
    )
    if any(path.startswith(p) for p in prefixes):
        return True
    # Calendar feeds (Google/Outlook subscribe by URL, no session cookies).
    if path.endswith(".ics"):
        return True
    return False


class SiteComingSoonMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not getattr(settings, "SITE_COMING_SOON", False):
            return self.get_response(request)
        if request.user.is_authenticated:
            return self.get_response(request)
        path = request.path
        if _path_allowed(path):
            return self.get_response(request)
        nxt = quote(request.get_full_path(), safe="/")
        return redirect(f"/coming-soon/?next={nxt}")


# Paths a confined (publications-only) account may reach. Deny by default:
# anything not matched here is redirected back into the library, so adding a
# new app to the site never silently widens what these accounts can see.
PUBLICATIONS_ONLY_ALLOWED_PREFIXES = (
    "/apps/mdh-publications/",
    "/login/",
    "/logout/",
    "/static/",
    "/media/",
    "/coming-soon/",
)

PUBLICATIONS_HOME = "/apps/mdh-publications/"


def _is_publications_only(user) -> bool:
    """True when this account is confined to the publications library.

    Superusers are never confined: that would be an easy way to lock the site
    owner out of /admin/ by mis-assigning a group.
    """
    if not user.is_authenticated or user.is_superuser:
        return False
    group_name = getattr(settings, "PUBLICATIONS_ONLY_GROUP", "")
    if not group_name:
        return False
    # Cached on the user for the life of the request; the nav template checks
    # this too and there is no reason to hit the DB twice.
    cached = getattr(user, "_publications_only", None)
    if cached is None:
        cached = user.groups.filter(name=group_name).exists()
        user._publications_only = cached
    return cached


class PublicationsOnlyMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        confined = _is_publications_only(request.user)
        # Exposed for templates (site_nav.html hides links these accounts
        # cannot follow). Always set, so the template check is never undefined.
        request.publications_only = confined

        if not confined:
            return self.get_response(request)

        path = request.path
        if any(path.startswith(p) for p in PUBLICATIONS_ONLY_ALLOWED_PREFIXES):
            return self.get_response(request)

        return redirect(PUBLICATIONS_HOME)
