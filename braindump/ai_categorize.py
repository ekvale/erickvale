"""
GTD capture categorization via Anthropic and/or Perplexity: preferred provider first,
then the other on failure. JSON object in the response (parsed from text).
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

_SYSTEM = (
    'You classify a personal GTD-style inbox capture. Reply with ONE JSON object only, no markdown fences. '
    'Keys: title (string <=120 chars), category (short area like Work or Home), '
    'gtd_bucket one of: next_action, project, waiting, someday, reference, calendar, '
    'initial_status one of: open, waiting, '
    'calendar_date (ISO date YYYY-MM-DD for when this should appear on a monthly calendar — '
    'use a sensible day this month or next for deadlines mentioned; else use today), '
    'waiting_for (string, only if waiting). '
    'If the text implies blocked on someone, use initial_status waiting and waiting_for.'
)

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


def _anthropic_model() -> str:
    m = (getattr(settings, 'BRAINDUMP_ANTHROPIC_MODEL', '') or '').strip()
    if m:
        return m
    m = (getattr(settings, 'GRANTSCOUT_ANTHROPIC_MODEL', '') or '').strip()
    return m or 'claude-3-5-haiku-20241022'


def _perplexity_model() -> str:
    m = (getattr(settings, 'BRAINDUMP_PERPLEXITY_MODEL', '') or '').strip()
    if m:
        return m
    m = (getattr(settings, 'GRANTSCOUT_PERPLEXITY_MODEL', '') or '').strip()
    return m or 'sonar'


def _call_anthropic(system: str, user_block: str, timeout: int = 60) -> str:
    key = (getattr(settings, 'ANTHROPIC_API_KEY', '') or '').strip()
    if not key:
        raise RuntimeError('ANTHROPIC_API_KEY not set')
    url = getattr(settings, 'ANTHROPIC_API_URL', 'https://api.anthropic.com/v1/messages')
    version = getattr(settings, 'ANTHROPIC_VERSION', '2023-06-01')
    model = _anthropic_model()
    resp = requests.post(
        url,
        headers={
            'x-api-key': key,
            'anthropic-version': str(version),
            'Content-Type': 'application/json',
        },
        json={
            'model': model,
            'max_tokens': 2048,
            'system': system,
            'messages': [{'role': 'user', 'content': user_block}],
        },
        timeout=timeout,
    )
    if resp.status_code >= 400:
        logger.warning(
            'braindump Anthropic HTTP %s: %s', resp.status_code, resp.text[:500]
        )
        resp.raise_for_status()
    body = resp.json()
    parts = body.get('content') or []
    texts: list[str] = []
    for block in parts:
        if isinstance(block, dict) and block.get('type') == 'text':
            texts.append(block.get('text') or '')
    if not texts:
        raise RuntimeError('Anthropic response missing text content')
    return ''.join(texts)


def _call_perplexity(system: str, user_block: str, timeout: int = 60) -> str:
    key = (getattr(settings, 'PERPLEXITY_API_KEY', '') or '').strip()
    if not key:
        raise RuntimeError('PERPLEXITY_API_KEY not set')
    url = getattr(
        settings,
        'PERPLEXITY_API_URL',
        'https://api.perplexity.ai/chat/completions',
    )
    model = _perplexity_model()
    resp = requests.post(
        url,
        headers={
            'Authorization': f'Bearer {key}',
            'Content-Type': 'application/json',
        },
        json={
            'model': model,
            'temperature': 0.3,
            'max_tokens': 400,
            'messages': [
                {'role': 'system', 'content': system},
                {'role': 'user', 'content': user_block},
            ],
        },
        timeout=timeout,
    )
    if resp.status_code >= 400:
        logger.warning(
            'braindump Perplexity HTTP %s: %s', resp.status_code, resp.text[:500]
        )
        resp.raise_for_status()
    body = resp.json()
    choices = body.get('choices') or []
    if not choices:
        raise RuntimeError('Perplexity response missing choices')
    content = (choices[0].get('message') or {}).get('content')
    if not content:
        raise RuntimeError('Perplexity response missing content')
    return str(content)


def _provider_order() -> list[str]:
    raw = (getattr(settings, 'BRAINDUMP_LLM_PROVIDER', '') or 'anthropic').strip().lower()
    if raw not in ('anthropic', 'perplexity'):
        raw = 'anthropic'
    other = 'perplexity' if raw == 'anthropic' else 'anthropic'
    return [raw, other]


def _parsed_ok(parsed: dict) -> bool:
    return bool(parsed) and (
        parsed.get('title')
        or parsed.get('gtd_bucket')
        or parsed.get('calendar_date')
        or parsed.get('initial_status')
    )


def _apply_parsed_to_item(item: CaptureItem, parsed: dict, today: date) -> None:
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
        y, m_, d = [int(x) for x in cds.split('-')[:3]]
        item.calendar_date = date(y, m_, d)
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


def _fallback_defaults(item: CaptureItem, today: date, error_note: str) -> None:
    item.title = (item.body or '')[:200] or 'Capture'
    item.calendar_date = item.calendar_date or today
    item.ai_error = error_note[:2000]
    item.save(
        update_fields=[
            'title',
            'calendar_date',
            'ai_error',
            'updated_at',
        ]
    )


def categorize_capture_item(item: CaptureItem) -> None:
    """
    Fills title, category_label, gtd_bucket, calendar_date, status, waiting_for on ``item``.
    Tries BRAINDUMP_LLM_PROVIDER first (anthropic or perplexity), then the other if it fails.
    """
    today = timezone.localdate()
    user_block = f'Today is {today.isoformat()}.\n\nCapture:\n{item.body}'

    anthropic_key = (getattr(settings, 'ANTHROPIC_API_KEY', '') or '').strip()
    perplexity_key = (getattr(settings, 'PERPLEXITY_API_KEY', '') or '').strip()

    if not anthropic_key and not perplexity_key:
        _fallback_defaults(
            item,
            today,
            'Set ANTHROPIC_API_KEY and/or PERPLEXITY_API_KEY; using defaults.',
        )
        return

    errors: list[str] = []
    for provider in _provider_order():
        if provider == 'anthropic' and not anthropic_key:
            errors.append('anthropic: skipped (no ANTHROPIC_API_KEY)')
            continue
        if provider == 'perplexity' and not perplexity_key:
            errors.append('perplexity: skipped (no PERPLEXITY_API_KEY)')
            continue
        try:
            if provider == 'anthropic':
                raw = _call_anthropic(_SYSTEM, user_block)
            else:
                raw = _call_perplexity(_SYSTEM, user_block)
            parsed = _parse_json_object(raw)
            if _parsed_ok(parsed):
                _apply_parsed_to_item(item, parsed, today)
                logger.info('braindump categorized via %s', provider)
                return
            errors.append(f'{provider}: empty or unparseable JSON')
        except Exception as e:
            logger.warning('braindump %s categorize failed: %s', provider, e)
            errors.append(f'{provider}: {e}')

    _fallback_defaults(item, today, ' | '.join(errors) or 'All providers failed.')
