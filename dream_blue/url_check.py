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


def source_url_is_reachable(url: str, **_: Any) -> bool:
    """
    Return True if the URL responds with a likely-success status after redirects.

    Uses GET with stream=True (small download) and a browser-like User-Agent.
    Rejects 404, 410, and 5xx. Accepts 2xx/3xx. Keeps 401/403 when the server
    may block automated clients but the page can be fine in a browser (logged).
    """
    timeout = _timeout()
    try:
        with requests.get(
            url,
            timeout=timeout,
            allow_redirects=True,
            headers=_BROWSER_HEADERS,
            stream=True,
        ) as r:
            code = r.status_code
    except requests.RequestException as e:
        logger.info('URL check failed (network): %s — %s', url[:120], e)
        return False

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
        return True
    logger.info('URL check: %s — unexpected HTTP %s', url[:120], code)
    return False


def pause_between_checks() -> None:
    d = _delay()
    if d > 0:
        time.sleep(d)
