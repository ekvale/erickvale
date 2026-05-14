"""
Site-wide middleware for optional public "coming soon" mode.

When SITE_COMING_SOON is True, anonymous requests are redirected to the
coming-soon page (except auth, admin, static assets, and similar).
Authenticated users always reach the real site.
"""

from __future__ import annotations

from urllib.parse import quote

from django.conf import settings
from django.shortcuts import redirect


def _path_allowed(path: str) -> bool:
    """Paths that anonymous users may hit while the curtain is up."""
    if path in ("/favicon.ico", "/robots.txt"):
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
    return any(path.startswith(p) for p in prefixes)


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
