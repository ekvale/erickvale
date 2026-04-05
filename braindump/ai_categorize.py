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

from .models import (
    CaptureItem,
    CaptureStatus,
    EngagementChoice,
    GTDBucket,
    NonActionableDisposition,
)

logger = logging.getLogger(__name__)

_SYSTEM = (
    'You classify a personal inbox capture using Getting Things Done (GTD). '
    'Reply with ONE JSON object only, no markdown fences.\n'
    'Keys:\n'
    '- title (string <=120 chars)\n'
    '- category (short area like Work or Home)\n'
    '- is_actionable (boolean): true if something must be done; false for pure reference, '
    'ideas for someday, noise to discard, or FYI with no action.\n'
    '- non_actionable_disposition (only if is_actionable is false): one of trash, someday, reference.\n'
    '- gtd_bucket (only if actionable): next_action, project, waiting, someday, reference, calendar — '
    'use calendar only for time-specific items (appointment/deadline at a specific day).\n'
    '- is_project (boolean): true if multi-step outcome; else false.\n'
    '- next_action (string): one concrete physical next step if actionable; else empty.\n'
    '- engagement: do_now | defer | delegate — do_now if it fits the 2-minute rule or should be done '
    'immediately; delegate if blocked on someone; defer for next-action list.\n'
    '- two_minute_candidate (boolean): true only if likely completable in under 2 minutes.\n'
    '- initial_status: open or waiting (waiting if blocked on someone).\n'
    '- waiting_for (string, only if waiting).\n'
    '- time_specific_calendar (boolean): true only for a real appointment, meeting, or hard deadline on a '
    'specific day. Do NOT use true for vague "this week" tasks — those belong on next-action lists, not the calendar.\n'
    '- calendar_date (ISO YYYY-MM-DD): include ONLY when time_specific_calendar is true; pick the actual day '
    'mentioned or a sensible deadline day; omit this key entirely if not time-specific.\n'
    'GTD rule: generic to-dos do not get calendar_date. If blocked on someone, use initial_status waiting and waiting_for.'
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

_ENGAGEMENT_MAP = {
    'do_now': EngagementChoice.DO_NOW,
    'defer': EngagementChoice.DEFER,
    'delegate': EngagementChoice.DELEGATE,
}

_DISPOSITION_MAP = {
    'trash': NonActionableDisposition.TRASH,
    'someday': NonActionableDisposition.SOMEDAY,
    'reference': NonActionableDisposition.REFERENCE,
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


def _coerce_bool(v) -> bool | None:
    if v is True or v is False:
        return v
    if isinstance(v, str):
        s = v.strip().lower()
        if s in ('true', '1', 'yes'):
            return True
        if s in ('false', '0', 'no'):
            return False
    return None


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
            'max_tokens': 900,
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


def _infer_actionable_from_bucket(bkey: str) -> bool | None:
    if bkey in ('reference', 'someday'):
        return False
    if bkey in ('next_action', 'project', 'waiting', 'calendar'):
        return True
    return None


def _disposition_from_bucket(bkey: str) -> str:
    if bkey == 'reference':
        return NonActionableDisposition.REFERENCE
    if bkey == 'someday':
        return NonActionableDisposition.SOMEDAY
    return NonActionableDisposition.SOMEDAY


def _parsed_ok(parsed: dict) -> bool:
    if not parsed:
        return False
    if parsed.get('title') or parsed.get('gtd_bucket') or parsed.get('initial_status'):
        return True
    if 'is_actionable' in parsed:
        return True
    if parsed.get('next_action'):
        return True
    return False


def _apply_parsed_to_item(item: CaptureItem, parsed: dict, today: date) -> None:
    item.ai_payload = parsed
    item.ai_error = ''

    title = (parsed.get('title') or '').strip() or (item.body or '')[:120]
    item.title = title[:200]
    item.category_label = (parsed.get('category') or '')[:120]

    bkey = (parsed.get('gtd_bucket') or 'next_action').strip().lower()
    item.gtd_bucket = _BUCKET_MAP.get(bkey, GTDBucket.NEXT_ACTION)

    actionable = _coerce_bool(parsed.get('is_actionable'))
    if actionable is None:
        actionable = _infer_actionable_from_bucket(bkey)
    if actionable is None:
        actionable = True
    item.is_actionable = actionable

    if not actionable:
        disp = (parsed.get('non_actionable_disposition') or '').strip().lower()
        item.non_actionable_disposition = _DISPOSITION_MAP.get(
            disp, _disposition_from_bucket(bkey)
        )
        item.is_project = False
        item.next_action = ''
        item.engagement = ''
        item.two_minute_rule_suggested = False
        item.status = CaptureStatus.OPEN
        item.waiting_for = ''
        item.calendar_date = None
        item.calendar_is_hard_date = False
    else:
        item.non_actionable_disposition = NonActionableDisposition.NONE
        item.is_project = bool(_coerce_bool(parsed.get('is_project'))) or (
            item.gtd_bucket == GTDBucket.PROJECT
        )
        item.next_action = (parsed.get('next_action') or '').strip()[:2000]
        eng = (parsed.get('engagement') or 'defer').strip().lower()
        item.engagement = _ENGAGEMENT_MAP.get(eng, EngagementChoice.DEFER)
        t2 = _coerce_bool(parsed.get('two_minute_candidate'))
        item.two_minute_rule_suggested = bool(t2) if t2 is not None else False

        st = (parsed.get('initial_status') or 'open').strip().lower()
        item.status = _STATUS_MAP.get(st, CaptureStatus.OPEN)
        wf = (parsed.get('waiting_for') or '').strip()
        if item.status == CaptureStatus.WAITING:
            item.waiting_for = wf[:255]
        else:
            item.waiting_for = ''

        ts_in_payload = 'time_specific_calendar' in parsed
        ts_cal = (
            _coerce_bool(parsed.get('time_specific_calendar'))
            if ts_in_payload
            else None
        )
        cal_in_payload = 'calendar_date' in parsed

        if cal_in_payload:
            cds = parsed.get('calendar_date')
            if cds is None or (isinstance(cds, str) and not str(cds).strip()):
                item.calendar_date = None
                item.calendar_is_hard_date = False
            else:
                cds = str(cds).strip()
                try:
                    y, m_, d = [int(x) for x in cds.split('-')[:3]]
                    item.calendar_date = date(y, m_, d)
                except (ValueError, TypeError, AttributeError):
                    item.calendar_date = None
                    item.calendar_is_hard_date = False
                else:
                    if ts_cal is True:
                        item.calendar_is_hard_date = True
                    elif ts_cal is False:
                        item.calendar_is_hard_date = False
                    else:
                        item.calendar_is_hard_date = item.calendar_date is not None and (
                            item.gtd_bucket == GTDBucket.CALENDAR
                        )
        elif ts_in_payload:
            if ts_cal is True and item.calendar_date:
                item.calendar_is_hard_date = True
            elif ts_cal is False:
                item.calendar_is_hard_date = False

        if item.gtd_bucket == GTDBucket.CALENDAR and item.calendar_date:
            item.calendar_is_hard_date = True

    item.save(
        update_fields=[
            'title',
            'category_label',
            'gtd_bucket',
            'status',
            'waiting_for',
            'calendar_date',
            'calendar_is_hard_date',
            'is_actionable',
            'non_actionable_disposition',
            'is_project',
            'next_action',
            'engagement',
            'two_minute_rule_suggested',
            'ai_payload',
            'ai_error',
            'updated_at',
        ]
    )


def _fallback_defaults(item: CaptureItem, error_note: str) -> None:
    item.title = (item.body or '')[:200] or 'Capture'
    item.ai_error = error_note[:2000]
    item.save(
        update_fields=[
            'title',
            'ai_error',
            'updated_at',
        ]
    )


def categorize_capture_item(item: CaptureItem) -> None:
    """
    Fills GTD clarify/organize fields on ``item``.
    Tries BRAINDUMP_LLM_PROVIDER first (anthropic or perplexity), then the other if it fails.
    """
    today = timezone.localdate()
    user_block = f'Today is {today.isoformat()}.\n\nCapture:\n{item.body}'

    anthropic_key = (getattr(settings, 'ANTHROPIC_API_KEY', '') or '').strip()
    perplexity_key = (getattr(settings, 'PERPLEXITY_API_KEY', '') or '').strip()

    if not anthropic_key and not perplexity_key:
        _fallback_defaults(
            item,
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

    _fallback_defaults(item, ' | '.join(errors) or 'All providers failed.')
