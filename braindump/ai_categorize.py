"""
OpenAI JSON categorization for a single capture (title, bucket, calendar_date, status hint).
"""

from __future__ import annotations

import json
import logging
import re
from datetime import date

import requests
from django.conf import settings
from django.utils import timezone

from .models import CaptureItem, CaptureStatus, GTDBucket

logger = logging.getLogger(__name__)

_BUCKET_MAP = {
    'next_action': GTDBucket.NEXT_ACTION,
    'project': GTDBucket.PROJECT,
    'waiting': GTDBucket.WAITING,
    'someday': GTDBucket.SOMEDAY,
    'reference': GTDBucket.REFERENCE,
    'calendar': GTDBucket.CALENDAR,
}

_STATUS_MAP = {
    'open': CaptureStatus.OPEN,
    'waiting': CaptureStatus.WAITING,
    'done': CaptureStatus.DONE,
}


def _parse_json_object(raw: str) -> dict:
    raw = (raw or '').strip()
    if not raw:
        return {}
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        m = re.search(r'\{[\s\S]*\}', raw)
        if m:
            try:
                return json.loads(m.group(0))
            except json.JSONDecodeError:
                pass
    return {}


def categorize_capture_item(item: CaptureItem) -> None:
    """
    Fills title, category_label, gtd_bucket, calendar_date, status, waiting_for on ``item``.
    Safe to call multiple times; overwrites AI fields from latest response.
    """
    key = (getattr(settings, 'OPENAI_API_KEY', '') or '').strip()
    today = timezone.localdate()
    if not key:
        item.title = (item.body or '')[:200] or 'Capture'
        item.calendar_date = item.calendar_date or today
        item.ai_error = 'OPENAI_API_KEY not set; using defaults.'
        item.save(
            update_fields=[
                'title',
                'calendar_date',
                'ai_error',
                'updated_at',
            ]
        )
        return

    model = (getattr(settings, 'BRAINDUMP_OPENAI_MODEL', '') or 'gpt-4o-mini').strip()
    url = getattr(
        settings,
        'OPENAI_CHAT_COMPLETIONS_URL',
        'https://api.openai.com/v1/chat/completions',
    )

    system = (
        'You classify a personal GTD-style inbox capture. Reply with ONE JSON object only, no markdown. '
        'Keys: title (string <=120 chars), category (short area like Work or Home), '
        'gtd_bucket one of: next_action, project, waiting, someday, reference, calendar, '
        'initial_status one of: open, waiting, '
        'calendar_date (ISO date YYYY-MM-DD for when this should appear on a monthly calendar — '
        'use a sensible day this month or next for deadlines mentioned; else use today), '
        'waiting_for (string, only if waiting). '
        'If the text implies blocked on someone, use initial_status waiting and waiting_for.'
    )
    user_block = f'Today is {today.isoformat()}.\n\nCapture:\n{item.body}'

    payload = {
        'model': model,
        'messages': [
            {'role': 'system', 'content': system},
            {'role': 'user', 'content': user_block},
        ],
        'temperature': 0.3,
        'max_tokens': 400,
        'response_format': {'type': 'json_object'},
    }
    try:
        r = requests.post(
            url,
            headers={'Authorization': f'Bearer {key}', 'Content-Type': 'application/json'},
            json=payload,
            timeout=60,
        )
        r.raise_for_status()
        data = r.json()
        raw = (data.get('choices') or [{}])[0].get('message', {}).get('content') or ''
        parsed = _parse_json_object(raw)
    except Exception as e:
        logger.exception('braindump AI categorize failed')
        item.title = (item.body or '')[:200] or 'Capture'
        item.calendar_date = item.calendar_date or today
        item.ai_error = str(e)[:2000]
        item.save(
            update_fields=['title', 'calendar_date', 'ai_error', 'updated_at']
        )
        return

    item.ai_payload = parsed
    item.ai_error = ''

    title = (parsed.get('title') or '').strip() or (item.body or '')[:120]
    item.title = title[:200]
    item.category_label = (parsed.get('category') or '')[:120]

    bkey = (parsed.get('gtd_bucket') or 'next_action').strip().lower()
    item.gtd_bucket = _BUCKET_MAP.get(bkey, GTDBucket.NEXT_ACTION)

    st = (parsed.get('initial_status') or 'open').strip().lower()
    item.status = _STATUS_MAP.get(st, CaptureStatus.OPEN)

    wf = (parsed.get('waiting_for') or '').strip()
    if item.status == CaptureStatus.WAITING:
        item.waiting_for = wf[:255]
    else:
        item.waiting_for = ''

    cds = (parsed.get('calendar_date') or '').strip()
    try:
        y, m, d = [int(x) for x in cds.split('-')[:3]]
        item.calendar_date = date(y, m, d)
    except (ValueError, TypeError, AttributeError):
        item.calendar_date = today

    item.save(
        update_fields=[
            'title',
            'category_label',
            'gtd_bucket',
            'status',
            'waiting_for',
            'calendar_date',
            'ai_payload',
            'ai_error',
            'updated_at',
        ]
    )
