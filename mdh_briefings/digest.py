"""Build and send the daily MDH leadership priorities + news email."""

from __future__ import annotations

import logging
from datetime import date, timedelta
from pathlib import Path

from django.conf import settings
from django.template.loader import render_to_string
from django.utils import timezone

from dream_blue.emailing import DreamBlueEmailConfigError, parse_recipient_list, send_html_digest

from .agents import LEADERS, leader_by_id
from .briefing_store import save_briefing
from .bureaus import (
    CORE_DIGEST_LEADER_IDS,
    WEEKDAY_SPOTLIGHT_SLUGS,
    digest_leader_ids_for_date,
    format_bureau_org_chart,
    is_digest_weekday,
    spotlight_bureau_for_date,
)
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
    leader_ids: list[str] | None = None,
) -> tuple[list[LeaderBriefing], list[str]]:
    """
    Generate/cache briefings for the given leader ids (default: all LEADERS).
    """
    if leader_ids is None:
        targets = LEADERS
    else:
        id_set = set(leader_ids)
        targets = [L for L in LEADERS if L['id'] in id_set]

    briefings: list[LeaderBriefing] = []
    errors: list[str] = []

    for leader in targets:
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


def _card_from_briefing(leader: dict, briefing: LeaderBriefing) -> dict:
    return {
        'leader': leader,
        'briefing': briefing,
        'priorities': briefing.top_priorities or [],
        'relevant_news': briefing.relevant_news or [],
        'high_value_projects': briefing.high_value_projects or [],
    }


def build_digest_context(
    today: date,
    *,
    briefings: list[LeaderBriefing] | None = None,
    news_items: list[dict] | None = None,
    generation_errors: list[str] | None = None,
    digest_leader_ids: list[str] | None = None,
    spotlight_bureau: dict | None = None,
) -> dict:
    if digest_leader_ids is None:
        digest_leader_ids, spotlight_bureau = digest_leader_ids_for_date(today)

    if briefings is None:
        briefings, generation_errors = ensure_briefings_for_date(
            today,
            generate_missing=True,
            leader_ids=digest_leader_ids,
        )

    by_id = {b.leader_id: b for b in briefings}
    executive_cards = []
    spotlight_card = None

    for lid in CORE_DIGEST_LEADER_IDS:
        leader = leader_by_id(lid)
        b = by_id.get(lid) if leader else None
        if leader and b:
            executive_cards.append(_card_from_briefing(leader, b))

    if spotlight_bureau:
        ac_id = spotlight_bureau['ac_leader_id']
        leader = leader_by_id(ac_id)
        b = by_id.get(ac_id) if leader else None
        if leader and b:
            spotlight_card = _card_from_briefing(leader, b)

    next_bureau = None
    if is_digest_weekday(today):
        nxt = today + timedelta(days=1)
        while nxt.weekday() > 4:
            nxt += timedelta(days=1)
        nb = spotlight_bureau_for_date(nxt)
        if nb:
            next_bureau = nb['name']

    base = _digest_base_url()
    return {
        'today': today,
        'today_label': today.strftime('%A, %B %d, %Y'),
        'executive_cards': executive_cards,
        'spotlight_card': spotlight_card,
        'spotlight_bureau': spotlight_bureau,
        'spotlight_org_chart': (
            format_bureau_org_chart(spotlight_bureau) if spotlight_bureau else ''
        ),
        'next_spotlight_bureau': next_bureau,
        'news_items': news_items or [],
        'generation_errors': generation_errors or [],
        'dashboard_url': f'{base}/mdh/' if base else '',
    }


def render_digest_html(today: date, ctx: dict) -> tuple[str, str]:
    html = render_to_string('mdh_briefings/emails/daily_digest.html', ctx)
    bureau_name = (ctx.get('spotlight_bureau') or {}).get('name', 'MDH')
    subject = f'MDH Daily — {bureau_name} spotlight ({today.strftime("%a %b %d")})'
    return subject, html


def _plain_text_body(ctx: dict) -> str:
    lines = [
        f"MDH Leadership Daily — {ctx['today_label']}",
        '',
    ]
    if ctx.get('dashboard_url'):
        lines.extend([f"Dashboard: {ctx['dashboard_url']}", ''])

    if ctx.get('spotlight_bureau'):
        lines.append(f"Bureau spotlight: {ctx['spotlight_bureau']['name']}")
        lines.append('')

    for card in ctx.get('executive_cards') or []:
        b = card['briefing']
        lines.append(f"{b.name} — {b.title}")
        for i, p in enumerate(card.get('priorities') or [], 1):
            lines.append(f"  {i}. {p}")
        lines.append('')

    sc = ctx.get('spotlight_card')
    if sc:
        b = sc['briefing']
        lines.append(f"SPOTLIGHT: {b.name} — {b.title}")
        for i, p in enumerate(sc.get('priorities') or [], 1):
            lines.append(f"  {i}. {p}")
        lines.append('')

    news = ctx.get('news_items') or []
    if news:
        lines.append('Relevant news')
        for item in news:
            lines.append(item.get('headline') or 'News item')
            if item.get('summary'):
                lines.append(f"  {item['summary']}")
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
    force_weekend: bool = False,
) -> dict:
    if today is None:
        today = timezone.localdate()

    if not force_weekend and not is_digest_weekday(today):
        return {
            'ok': True,
            'skipped': True,
            'message': f'Skipped weekend ({today.strftime("%A")}); digest sends Monday–Friday only.',
            'subject': '',
            'recipients': get_digest_recipients(),
            'leader_count': 0,
            'news_count': 0,
        }

    digest_ids, spotlight_bureau = digest_leader_ids_for_date(today)
    recipients = get_digest_recipients()

    briefings, gen_errors = ensure_briefings_for_date(
        today,
        generate_missing=generate_missing,
        leader_ids=digest_ids,
    )

    news_items: list[dict] = []
    if include_news:
        try:
            news_items = services.fetch_daily_news_digest(today)
        except Exception as exc:
            gen_errors = list(gen_errors) + [f'News digest: {exc}']
            logger.warning('mdh_briefings news digest failed: %s', exc)

    ctx = build_digest_context(
        today,
        briefings=briefings,
        news_items=news_items,
        generation_errors=gen_errors,
        digest_leader_ids=digest_ids,
        spotlight_bureau=spotlight_bureau,
    )
    subject, html = render_digest_html(today, ctx)
    text_body = _plain_text_body(ctx)

    leader_count = len(ctx['executive_cards']) + (1 if ctx.get('spotlight_card') else 0)
    result_base = {
        'subject': subject,
        'recipients': recipients,
        'leader_count': leader_count,
        'news_count': len(news_items),
        'spotlight_bureau': (spotlight_bureau or {}).get('name', ''),
        'skipped': False,
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
                f'{leader_count} leader(s) in email, {len(news_items)} news item(s).'
            ),
            **result_base,
        }

    if not recipients:
        return {
            'ok': False,
            'message': 'No recipients: set MDH_BRIEFINGS_DIGEST_RECIPIENTS.',
            **result_base,
        }

    if leader_count == 0 and not news_items:
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
        'mdh_briefings daily digest sent backend=%s id=%s spotlight=%s',
        delivery.get('backend'),
        mid,
        result_base.get('spotlight_bureau'),
    )
    extra = f' [{delivery.get("backend")} id={mid}]' if mid else f' [{delivery.get("backend")}]'
    return {
        'ok': True,
        'message': f'Sent "{subject}" to {", ".join(recipients)}.{extra}',
        'delivery': delivery,
        **result_base,
    }
