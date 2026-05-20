"""Build and send the daily MDH leadership priorities + news email."""

from __future__ import annotations

import logging
from datetime import date
from pathlib import Path

from django.conf import settings
from django.template.loader import render_to_string
from django.utils import timezone

from dream_blue.emailing import DreamBlueEmailConfigError, parse_recipient_list, send_html_digest

from .agents import LEADERS
from .briefing_store import save_briefing
from .models import LeaderBriefing
from . import services

logger = logging.getLogger(__name__)


def get_digest_recipients() -> list[str]:
    raw = getattr(settings, 'MDH_BRIEFINGS_DIGEST_RECIPIENTS', '') or ''
    return parse_recipient_list(raw)


def _digest_base_url() -> str:
    base = (
        (getattr(settings, 'MDH_BRIEFINGS_DIGEST_BASE_URL', '') or '').strip()
        or (getattr(settings, 'DREAM_BLUE_DIGEST_BASE_URL', '') or '').strip()
    )
    return base.rstrip('/')


def ensure_briefings_for_date(
    today: date,
    *,
    generate_missing: bool = True,
) -> tuple[list[LeaderBriefing], list[str]]:
    """
    Return today's LeaderBriefing rows for all roster leaders (in roster order).
    Generate missing rows when generate_missing is True.
    """
    briefings: list[LeaderBriefing] = []
    errors: list[str] = []

    for leader in LEADERS:
        existing = LeaderBriefing.objects.filter(leader_id=leader['id'], date=today).first()
        if existing:
            briefings.append(existing)
            continue
        if not generate_missing:
            errors.append(f"No briefing for {leader['name']} ({today.isoformat()})")
            continue
        try:
            data = services.generate_briefing(leader, today)
            briefings.append(save_briefing(leader, today, data))
        except Exception as exc:
            msg = f"{leader['name']}: {exc}"
            errors.append(msg)
            logger.warning('mdh_briefings digest: %s', msg)

    return briefings, errors


def build_digest_context(
    today: date,
    *,
    briefings: list[LeaderBriefing] | None = None,
    news_items: list[dict] | None = None,
    generation_errors: list[str] | None = None,
) -> dict:
    if briefings is None:
        briefings, generation_errors = ensure_briefings_for_date(today, generate_missing=True)

    leader_cards = []
    by_id = {b.leader_id: b for b in briefings}
    for leader in LEADERS:
        b = by_id.get(leader['id'])
        if not b:
            continue
        leader_cards.append(
            {
                'leader': leader,
                'briefing': b,
                'priorities': b.top_priorities or [],
                'relevant_news': b.relevant_news or [],
                'high_value_projects': b.high_value_projects or [],
            }
        )

    base = _digest_base_url()
    return {
        'today': today,
        'today_label': today.strftime('%A, %B %d, %Y'),
        'leader_cards': leader_cards,
        'news_items': news_items or [],
        'generation_errors': generation_errors or [],
        'dashboard_url': f'{base}/mdh/' if base else '',
    }


def render_digest_html(today: date, ctx: dict) -> tuple[str, str]:
    html = render_to_string('mdh_briefings/emails/daily_digest.html', ctx)
    subject = f'MDH Leadership Daily — priorities & news ({today.isoformat()})'
    return subject, html


def _plain_text_body(ctx: dict) -> str:
    lines = [
        f"MDH Leadership Daily — {ctx['today_label']}",
        '',
    ]
    if ctx.get('dashboard_url'):
        lines.extend([f"Dashboard: {ctx['dashboard_url']}", ''])

    for card in ctx.get('leader_cards') or []:
        b = card['briefing']
        lines.append(f"{b.name} — {b.title}")
        lines.append(f"  {b.bureau}")
        for i, p in enumerate(card.get('priorities') or [], 1):
            lines.append(f"  {i}. {p}")
        for item in card.get('relevant_news') or []:
            headline = item.get('headline') if isinstance(item, dict) else str(item)
            lines.append(f"  News: {headline}")
            if isinstance(item, dict) and item.get('summary'):
                lines.append(f"    {item['summary']}")
        for proj in card.get('high_value_projects') or []:
            if not isinstance(proj, dict):
                continue
            lines.append(f"  Project: {proj.get('title', '')}")
            if proj.get('impact'):
                lines.append(f"    Impact: {proj['impact']}")
            if proj.get('next_step'):
                lines.append(f"    Next: {proj['next_step']}")
        lines.append('')

    news = ctx.get('news_items') or []
    if news:
        lines.append('Relevant news')
        lines.append('—' * 40)
        for item in news:
            lines.append(item.get('headline') or 'News item')
            if item.get('summary'):
                lines.append(f"  {item['summary']}")
            if item.get('why_it_matters'):
                lines.append(f"  Why it matters: {item['why_it_matters']}")
            lines.append('')

    errs = ctx.get('generation_errors') or []
    if errs:
        lines.append('Notes')
        for e in errs:
            lines.append(f"  - {e}")

    return '\n'.join(lines).strip() + '\n'


def run_daily_digest_send(
    *,
    dry_run: bool = False,
    output_html_path: str | None = None,
    today: date | None = None,
    generate_missing: bool = True,
    include_news: bool = True,
) -> dict:
    """
    Generate briefings (if needed), fetch news, email digest.

    Returns dict with ok, message, subject, recipients, leader_count, news_count.
    """
    if today is None:
        today = timezone.localdate()

    recipients = get_digest_recipients()
    briefings, gen_errors = ensure_briefings_for_date(
        today,
        generate_missing=generate_missing,
    )

    news_items: list[dict] = []
    news_error = ''
    if include_news:
        try:
            news_items = services.fetch_daily_news_digest(today)
        except Exception as exc:
            news_error = str(exc)
            gen_errors = list(gen_errors) + [f'News digest: {news_error}']
            logger.warning('mdh_briefings news digest failed: %s', exc)

    ctx = build_digest_context(
        today,
        briefings=briefings,
        news_items=news_items,
        generation_errors=gen_errors,
    )
    subject, html = render_digest_html(today, ctx)
    text_body = _plain_text_body(ctx)

    result_base = {
        'subject': subject,
        'recipients': recipients,
        'leader_count': len(ctx['leader_cards']),
        'news_count': len(news_items),
    }

    if output_html_path:
        Path(output_html_path).write_text(html, encoding='utf-8')
        return {
            'ok': True,
            'message': f'Wrote HTML to {output_html_path}',
            **result_base,
        }

    if dry_run:
        rec_msg = ', '.join(recipients) if recipients else '(none configured)'
        return {
            'ok': True,
            'message': (
                f'Dry run: {subject!r} -> {rec_msg}; '
                f'{len(ctx["leader_cards"])} leader(s), {len(news_items)} news item(s).'
            ),
            **result_base,
        }

    if not recipients:
        return {
            'ok': False,
            'message': 'No recipients: set MDH_BRIEFINGS_DIGEST_RECIPIENTS.',
            **result_base,
        }

    if not ctx['leader_cards'] and not news_items:
        return {
            'ok': False,
            'message': 'Nothing to send: no briefings and no news.',
            **result_base,
        }

    try:
        delivery = send_html_digest(subject, html, recipients=recipients, text_body=text_body)
    except DreamBlueEmailConfigError as exc:
        return {
            'ok': False,
            'message': str(exc),
            **result_base,
        }

    mid = delivery.get('message_id') or ''
    logger.info(
        'mdh_briefings daily digest sent backend=%s id=%s recipients=%s leaders=%s news=%s',
        delivery.get('backend'),
        mid,
        recipients,
        len(ctx['leader_cards']),
        len(news_items),
    )
    extra = f' [{delivery.get("backend")} id={mid}]' if mid else f' [{delivery.get("backend")}]'
    return {
        'ok': True,
        'message': f'Sent "{subject}" to {", ".join(recipients)}.{extra}',
        'delivery': delivery,
        **result_base,
    }
