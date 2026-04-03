"""
Dream Blue digest delivery: Resend HTTP API or Django SMTP.

Recipients and credentials come only from Django settings / environment variables.
"""

from __future__ import annotations

import logging
from typing import Sequence

import requests
from django.conf import settings
from django.core.mail import EmailMultiAlternatives

logger = logging.getLogger(__name__)


class DreamBlueEmailConfigError(RuntimeError):
    """Missing recipients or outbound email configuration."""


def parse_recipient_list(raw: str) -> list[str]:
    if not raw or not str(raw).strip():
        return []
    return [part.strip() for part in str(raw).split(',') if part.strip()]


def get_digest_recipients() -> list[str]:
    raw = getattr(settings, 'DREAM_BLUE_REPORT_RECIPIENTS', '') or ''
    return parse_recipient_list(raw)


def _resend_configured() -> bool:
    key = getattr(settings, 'RESEND_API_KEY', '') or ''
    from_email = getattr(settings, 'RESEND_FROM_EMAIL', '') or ''
    return bool(key.strip() and from_email.strip())


def _smtp_configured() -> bool:
    """Treat default Django email as SMTP-capable if host and from are set."""
    host = getattr(settings, 'EMAIL_HOST', '') or ''
    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', '') or ''
    return bool(str(host).strip() and str(from_email).strip())


def send_html_digest(
    subject: str,
    html_body: str,
    *,
    recipients: Sequence[str] | None = None,
    text_body: str = '',
) -> None:
    """
    Send one HTML email to all recipients.

    Uses Resend when RESEND_API_KEY and RESEND_FROM_EMAIL are set; otherwise
    Django's email backend (configure EMAIL_* and DEFAULT_FROM_EMAIL for SMTP).
    """
    to_list = list(recipients) if recipients is not None else get_digest_recipients()
    if not to_list:
        raise DreamBlueEmailConfigError(
            'No recipients: set DREAM_BLUE_REPORT_RECIPIENTS (comma-separated).'
        )

    if _resend_configured():
        _send_via_resend(subject, html_body, to_list)
        return

    if _smtp_configured():
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL')
        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_body or 'This message is HTML-only; use an HTML-capable client.',
            from_email=from_email,
            to=to_list,
        )
        msg.attach_alternative(html_body, 'text/html')
        msg.send(fail_silently=False)
        return

    raise DreamBlueEmailConfigError(
        'Configure either RESEND_API_KEY + RESEND_FROM_EMAIL, or '
        'EMAIL_HOST + DEFAULT_FROM_EMAIL (and related SMTP settings).'
    )


def _send_via_resend(subject: str, html_body: str, to_list: list[str]) -> None:
    api_key = getattr(settings, 'RESEND_API_KEY', '').strip()
    from_email = getattr(settings, 'RESEND_FROM_EMAIL', '').strip()
    url = getattr(settings, 'RESEND_API_URL', 'https://api.resend.com/emails')
    payload = {
        'from': from_email,
        'to': to_list if len(to_list) > 1 else to_list[0],
        'subject': subject,
        'html': html_body,
    }
    resp = requests.post(
        url,
        json=payload,
        headers={
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
        },
        timeout=60,
    )
    if resp.status_code >= 400:
        logger.error('Resend API error %s: %s', resp.status_code, resp.text)
        resp.raise_for_status()
