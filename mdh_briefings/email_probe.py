"""Diagnostics for MDH digest outbound email."""

from __future__ import annotations

from django.conf import settings
from django.utils import timezone

from dream_blue.emailing import (
    DreamBlueEmailConfigError,
    email_delivery_status,
    send_html_digest,
)

from .digest import get_digest_recipients


def run_email_probe(*, send: bool = True) -> dict:
    """
    Print-ready diagnostics: recipients, backend config, optional test send.
    """
    recipients = get_digest_recipients()
    delivery = email_delivery_status()
    raw_setting = (getattr(settings, 'MDH_BRIEFINGS_DIGEST_RECIPIENTS', '') or '').strip()
    perplexity = bool((getattr(settings, 'PERPLEXITY_API_KEY', '') or '').strip())

    result = {
        'ok': False,
        'message': '',
        'recipients': recipients,
        'raw_setting': raw_setting,
        'perplexity_configured': perplexity,
        'delivery_config': delivery,
        'send_result': None,
    }

    if not recipients:
        result['message'] = (
            'No recipients parsed. Set MDH_BRIEFINGS_DIGEST_RECIPIENTS in .env '
            '(comma-separated) and re-run from ~/erickvale with venv active.'
        )
        return result

    if not delivery.get('resend_configured') and not delivery.get('smtp_configured'):
        result['message'] = (
            'Outbound email not configured. Set RESEND_API_KEY + RESEND_FROM_EMAIL, '
            'or EMAIL_HOST + DEFAULT_FROM_EMAIL in .env.'
        )
        return result

    if not send:
        backend = 'resend' if delivery.get('resend_configured') else 'smtp'
        result['ok'] = True
        result['message'] = (
            f'Config OK (would use {backend}). Recipients: {", ".join(recipients)}'
        )
        return result

    today = timezone.localdate().isoformat()
    subject = f'MDH Briefings email probe ({today})'
    html = (
        '<p>This is a <strong>test message</strong> from erickvale.com MDH briefings.</p>'
        '<p>If you received it, outbound delivery to your inbox works. '
        'The full daily digest is separate and may take several minutes to generate.</p>'
    )
    text = (
        'MDH Briefings email probe. If you received this, outbound delivery works.\n'
        'The full daily digest is generated separately.\n'
    )

    try:
        send_result = send_html_digest(
            subject,
            html,
            recipients=recipients,
            text_body=text,
        )
    except DreamBlueEmailConfigError as exc:
        result['message'] = str(exc)
        return result
    except Exception as exc:
        result['message'] = f'Send failed: {exc}'
        return result

    result['send_result'] = send_result
    result['ok'] = True
    mid = send_result.get('message_id') or '(no id returned)'
    result['message'] = (
        f"Test sent via {send_result.get('backend')} from {send_result.get('from_email')} "
        f'to {send_result.get("recipients")}. Resend/SMTP message id: {mid}'
    )
    return result
