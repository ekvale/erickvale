"""Send email to contacts via Dream Blue / Resend (same stack as digests)."""

from __future__ import annotations

import logging

from django.utils import timezone
from django.utils.html import escape

from dream_blue.emailing import DreamBlueEmailConfigError, send_html_digest

logger = logging.getLogger(__name__)


def html_body_from_plain(body: str) -> str:
    return (
        '<p style="font-family:sans-serif;white-space:pre-wrap;">'
        f'{escape(body)}</p>'
    )


def send_contact_email(*, to_email: str, subject: str, body: str) -> None:
    send_html_digest(
        subject,
        html_body_from_plain(body),
        recipients=[to_email],
        text_body=body,
    )


def process_due_scheduled_contact_emails(*, user=None, limit: int = 50) -> dict:
    """
    Send pending rows whose ``scheduled_for`` is in the past.

    Returns ``{'sent': n, 'failed': n}``.
    """
    from .models import ContactScheduledEmail

    now = timezone.now()
    qs = ContactScheduledEmail.objects.filter(
        status=ContactScheduledEmail.Status.PENDING,
        scheduled_for__lte=now,
    ).select_related('contact')
    if user is not None:
        qs = qs.filter(user=user)

    sent = 0
    failed = 0
    for row in qs.order_by('scheduled_for', 'pk')[:limit]:
        to = (row.contact.email or '').strip()
        if not to:
            row.status = ContactScheduledEmail.Status.FAILED
            row.last_error = 'Contact has no email address.'
            row.save(update_fields=['status', 'last_error'])
            failed += 1
            continue
        try:
            send_contact_email(to_email=to, subject=row.subject, body=row.body)
        except DreamBlueEmailConfigError as e:
            row.status = ContactScheduledEmail.Status.FAILED
            row.last_error = str(e)[:2000]
            row.save(update_fields=['status', 'last_error'])
            failed += 1
            logger.warning(
                'contact scheduled email failed (config)',
                extra={'scheduled_email_id': row.pk, 'error': str(e)},
            )
        except Exception as e:
            row.status = ContactScheduledEmail.Status.FAILED
            row.last_error = str(e)[:2000]
            row.save(update_fields=['status', 'last_error'])
            failed += 1
            logger.exception(
                'contact scheduled email failed',
                extra={'scheduled_email_id': row.pk},
            )
        else:
            row.status = ContactScheduledEmail.Status.SENT
            row.sent_at = timezone.now()
            row.last_error = ''
            row.save(update_fields=['status', 'sent_at', 'last_error'])
            sent += 1
    return {'sent': sent, 'failed': failed}
