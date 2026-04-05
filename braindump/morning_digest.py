"""Build and send the daily braindump morning digest email."""

from __future__ import annotations

import logging
from datetime import date, timedelta
from pathlib import Path

from django.template.loader import render_to_string
from django.utils import timezone

from dream_blue.emailing import DreamBlueEmailConfigError, send_html_digest

from .email_common import get_braindump_owner, get_braindump_recipients
from .gtd_partition import partition_active_items
from .models import CaptureItem, TaskPriority

logger = logging.getLogger(__name__)

_PRIORITY_ORDER = {
    TaskPriority.URGENT: 0,
    TaskPriority.HIGH: 1,
    TaskPriority.NORMAL: 2,
    TaskPriority.LOW: 3,
}


def _prio_rank(x: CaptureItem) -> int:
    return _PRIORITY_ORDER.get(x.priority, 2)


def _sort_pri_created(items: list[CaptureItem]) -> list[CaptureItem]:
    return sorted(
        items,
        key=lambda x: (_prio_rank(x), -x.created_at.timestamp()),
    )


def build_morning_digest_context(owner, today: date | None = None) -> dict:
    """Template context for the morning HTML email."""
    if today is None:
        today = timezone.localdate()
    tomorrow = today + timedelta(days=1)

    active = list(
        CaptureItem.objects.filter(user=owner, archived=False).order_by('-created_at')
    )
    parts = partition_active_items(active)

    cal_hard = parts['calendar_hard']
    cal_today = [i for i in cal_hard if i.calendar_date == today]
    cal_tomorrow = [i for i in cal_hard if i.calendar_date == tomorrow]

    soft_today = [
        i
        for i in active
        if i.is_actionable is True
        and i.calendar_date == today
        and not i.calendar_is_hard_date
    ]
    soft_tomorrow = [
        i
        for i in active
        if i.is_actionable is True
        and i.calendar_date == tomorrow
        and not i.calendar_is_hard_date
    ]

    next_actions = _sort_pri_created(parts['next_actions'])[:35]
    waiting = _sort_pri_created(parts['waiting'])[:20]
    projects = _sort_pri_created(parts['projects'])[:15]
    unclear = _sort_pri_created(parts['unclear'])[:15]

    someday_n = len(parts['someday'])

    return {
        'today': today,
        'tomorrow': tomorrow,
        'calendar_today': _sort_pri_created(cal_today),
        'calendar_tomorrow': _sort_pri_created(cal_tomorrow),
        'soft_today': _sort_pri_created(soft_today),
        'soft_tomorrow': _sort_pri_created(soft_tomorrow),
        'next_actions': next_actions,
        'waiting': waiting,
        'projects': projects,
        'unclear': unclear,
        'someday_count': someday_n,
        'active_total': len(active),
    }


def _fmt_date(d: date) -> str:
    try:
        return f"{d.strftime('%A')}, {d.strftime('%B')} {d.day}, {d.year}"
    except (ValueError, TypeError):
        return d.isoformat()


def render_morning_digest_html(owner, today: date | None = None) -> tuple[str, str]:
    from django.conf import settings

    ctx = build_morning_digest_context(owner, today=today)
    today = ctx['today']
    ctx['today_label'] = _fmt_date(today)
    ctx['tomorrow_label'] = _fmt_date(ctx['tomorrow'])
    base = (
        (getattr(settings, 'BRAINDUMP_DIGEST_BASE_URL', '') or '')
        or (getattr(settings, 'DREAM_BLUE_DIGEST_BASE_URL', '') or '')
    ).strip().rstrip('/')
    ctx['braindump_url'] = f'{base}/apps/braindump/' if base else ''
    html = render_to_string('braindump/emails/morning_digest.html', ctx)
    subject = f'Brain dump - morning digest ({today.isoformat()})'
    return subject, html


def run_morning_digest_send(
    *,
    dry_run: bool = False,
    output_html_path: str | None = None,
    today: date | None = None,
) -> dict:
    """
    Send (or dry-run) the morning digest for the braindump owner.

    Returns dict: ok, message, subject, recipients (list), item_count (active captures).
    """
    from braindump.authz import braindump_configured

    if not braindump_configured():
        return {
            'ok': False,
            'message': 'Brain dump is not configured (owner username / id).',
            'subject': '',
            'recipients': [],
            'item_count': 0,
        }

    owner = get_braindump_owner()
    if not owner:
        return {
            'ok': False,
            'message': 'Brain dump owner user not found in the database.',
            'subject': '',
            'recipients': [],
            'item_count': 0,
        }

    subject, html = render_morning_digest_html(owner, today=today)
    recipients = get_braindump_recipients(owner)
    item_count = CaptureItem.objects.filter(user=owner, archived=False).count()

    if output_html_path:
        Path(output_html_path).write_text(html, encoding='utf-8')
        return {
            'ok': True,
            'message': f'Wrote HTML to {output_html_path}',
            'subject': subject,
            'recipients': recipients,
            'item_count': item_count,
        }

    if dry_run:
        rec_msg = ', '.join(recipients) if recipients else '(none — configure email)'
        return {
            'ok': True,
            'message': f'Dry run: {subject!r} -> {rec_msg}; {item_count} active item(s).',
            'subject': subject,
            'recipients': recipients,
            'item_count': item_count,
        }

    if not recipients:
        return {
            'ok': False,
            'message': 'No recipients: set the owner user email or BRAINDUMP_CALENDAR_EMAIL_RECIPIENTS.',
            'subject': subject,
            'recipients': [],
            'item_count': item_count,
        }

    try:
        send_html_digest(subject, html, recipients=recipients)
    except DreamBlueEmailConfigError as e:
        return {
            'ok': False,
            'message': str(e),
            'subject': subject,
            'recipients': recipients,
            'item_count': item_count,
        }

    logger.info(
        'braindump morning digest sent',
        extra={
            'recipient_count': len(recipients),
            'item_count': item_count,
        },
    )
    return {
        'ok': True,
        'message': f'Sent "{subject}" to {len(recipients)} recipient(s).',
        'subject': subject,
        'recipients': recipients,
        'item_count': item_count,
    }
