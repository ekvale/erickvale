"""Optional HTTP reachability check for GrantScout source_url (filter 404s / dead links)."""

from __future__ import annotations

import logging
import time
from typing import Any

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

_BROWSER_HEADERS: dict[str, str] = {
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
        '(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'
    ),
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
}


def _timeout() -> float:
    try:
        return float(getattr(settings, 'GRANTSCOUT_URL_CHECK_TIMEOUT', 15))
    except (TypeError, ValueError):
        return 15.0


def _delay() -> float:
    try:
        return max(0.0, float(getattr(settings, 'GRANTSCOUT_URL_CHECK_DELAY_SEC', 0.25)))
    except (TypeError, ValueError):
        return 0.25


def _content_peek_max_bytes() -> int:
    try:
        return max(8192, int(getattr(settings, 'GRANTSCOUT_URL_CONTENT_PEEK_BYTES', 98304)))
    except (TypeError, ValueError):
        return 98304


def url_body_suggests_page_moved(text: str) -> bool:
    """
    True when HTML/text looks like a generic “this URL moved / new website” page.

    Many agencies return HTTP 200 with a short placeholder instead of 404 after
    a redesign (e.g. Minnesota Commerce).
    """
    if not text or len(text) < 80:
        return False
    t = text.lower()
    markers = (
        'page you are looking for has moved',
        'please update your bookmarks',
        'update your bookmarks',
        'this page has moved',
        'the page you requested has been moved',
        'page has been moved',
        'content has moved to a new location',
        'you can either search for the page or go to the homepage',
    )
    if any(m in t for m in markers):
        return True
    if 'we have a new website' in t and (
        'bookmark' in t or 'homepage' in t or 'search for the page' in t
    ):
        return True
    return False


def _read_response_prefix(response: requests.Response, max_bytes: int) -> bytes:
    out = bytearray()
    try:
        for chunk in response.iter_content(chunk_size=16384):
            if not chunk:
                continue
            out.extend(chunk)
            if len(out) >= max_bytes:
                break
    except requests.RequestException:
        pass
    return bytes(out)


def source_url_is_reachable(url: str, **_: Any) -> bool:
    """
    Return True if the URL responds with a likely-useful page after redirects.

    Uses GET with stream=True (bounded read) and a browser-like User-Agent.
    Rejects 404, 410, and 5xx. For 2xx (except 204), scans the first part of the
    body for common “page moved / update bookmarks” placeholders that still use
    HTTP 200. Treats 401/403 as OK when the site may block bots (logged).
    """
    timeout = _timeout()
    peek = _content_peek_max_bytes()
    try:
        with requests.get(
            url,
            timeout=timeout,
            allow_redirects=True,
            headers=_BROWSER_HEADERS,
            stream=True,
        ) as r:
            code = r.status_code

            if code == 404 or code == 410:
                logger.info('URL check: %s — HTTP %s', url[:120], code)
                return False
            if code >= 500:
                logger.info('URL check: %s — HTTP %s', url[:120], code)
                return False
            if code in (401, 403):
                logger.warning(
                    'URL check: %s — HTTP %s (keeping link; site may block bots)',
                    url[:120],
                    code,
                )
                return True
            if 200 <= code < 400:
                if code == 204:
                    return True
                prefix = _read_response_prefix(r, peek)
                text = prefix.decode('utf-8', errors='ignore')
                if url_body_suggests_page_moved(text):
                    logger.info(
                        'URL check: %s — HTTP %s but body looks like moved/placeholder page',
                        url[:120],
                        code,
                    )
                    return False
                return True
            logger.info('URL check: %s — unexpected HTTP %s', url[:120], code)
            return False
    except requests.RequestException as e:
        logger.info('URL check failed (network): %s — %s', url[:120], e)
        return False


def pause_between_checks() -> None:
    d = _delay()
    if d > 0:
        time.sleep(d)
