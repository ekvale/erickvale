"""
Rollover & vacancy command center: sort by NOI urgency, pipeline status, digest top-N money moves.
"""

from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

from django.conf import settings
from django.utils import timezone

from .lease_digest_bundle import build_lease_rates_digest_section
from .models import BusinessCalendarEvent, LeaseRentRollChange


def _money_moves_limit() -> int:
    try:
        n = int(getattr(settings, 'DREAM_BLUE_MONEY_MOVES_LIMIT', 5))
    except (TypeError, ValueError):
        n = 5
    return max(1, min(n, 12))


def _rollover_dashboard_url() -> str:
    base = (getattr(settings, 'DREAM_BLUE_DIGEST_BASE_URL', '') or '').strip().rstrip('/')
    if not base:
        return ''
    return f'{base}/apps/dream-blue/operations/rollover/'


def _latest_rent_roll_by_event(event_ids: list[int]) -> dict[int, LeaseRentRollChange]:
    if not event_ids:
        return {}
    out: dict[int, LeaseRentRollChange] = {}
    for ch in LeaseRentRollChange.objects.filter(event_id__in=event_ids).order_by(
        '-recorded_at', '-id'
    ):
        eid = ch.event_id
        if eid not in out:
            out[eid] = ch
    return out


def _format_last_change(ch: LeaseRentRollChange | None) -> str:
    if ch is None:
        return ''
    bits = []
    if ch.amount_before != ch.amount_after:
        b = ch.amount_before
        a = ch.amount_after
        bits.append(f'Rent {b}→{a}')
    if ch.square_footage_before != ch.square_footage_after:
        bits.append(f'Sf {ch.square_footage_before}→{ch.square_footage_after}')
    if ch.square_footage_storage_before != ch.square_footage_storage_after:
        bits.append(
            f'Storage sf {ch.square_footage_storage_before}→{ch.square_footage_storage_after}'
        )
    body = '; '.join(bits) if bits else 'Updated'
    return f'{body} · {ch.recorded_at.date().isoformat()}'


def build_rollover_vacancy_rows(
    lease_rows: list[BusinessCalendarEvent],
    *,
    today=None,
) -> list[dict]:
    """
    Full sorted list: vacant units by (suggested $/mo × days vacant), then rollovers with
    lease end in the next 12 months (soonest end first).
    """
    if today is None:
        today = timezone.localdate()
    bundle = build_lease_rates_digest_section(lease_rows)
    if not bundle.get('show_section'):
        return []

    unit_rows = bundle['unit_rows']
    if len(unit_rows) != len(lease_rows):
        return []

    event_ids = [ev.id for ev in lease_rows]
    last_by_ev = _latest_rent_roll_by_event(event_ids)

    vacant_rows: list[dict] = []
    rollover_rows: list[dict] = []

    horizon_end = today + timedelta(days=365)

    for ev, u in zip(lease_rows, unit_rows):
        suggested: Decimal = u['suggested_monthly']
        breakeven: Decimal = u['breakeven_allocated_monthly']
        gap_sb = (suggested - breakeven).quantize(Decimal('0.01'))
        doc = (u.get('document_url') or '').strip()
        last_ch = last_by_ev.get(ev.id)

        if not u['has_contract']:
            vs = getattr(ev, 'vacancy_started', None)
            if vs:
                days_vacant = max(0, (today - vs).days)
            else:
                days_vacant = 0
            score = float(suggested) * float(max(days_vacant, 1))
            vacant_rows.append(
                {
                    'sort_key': (-score, ev.id),
                    'event_id': ev.id,
                    'property_label': u['property_label'],
                    'title': u['title'],
                    'kind': 'vacant',
                    'renewal_band': 'vacant',
                    'renewal_band_label': 'Vacant',
                    'current_monthly': None,
                    'suggested_monthly': suggested,
                    'breakeven_allocated_monthly': breakeven,
                    'gap_suggested_minus_breakeven': gap_sb,
                    'days_vacant': days_vacant,
                    'vacancy_started': vs,
                    'days_to_end': None,
                    'lease_end': ev.end_date,
                    'doc_url': doc,
                    'pipeline_status': ev.lease_pipeline_status,
                    'pipeline_label': ev.get_lease_pipeline_status_display(),
                    'last_change_summary': _format_last_change(last_ch),
                }
            )
            continue

        end = ev.end_date
        if end is not None and today < end <= horizon_end:
            days_to_end = (end - today).days
            if days_to_end <= 180:
                band = 'lt_6mo'
                band_label = f'≤6 mo ({days_to_end}d)'
            else:
                band = '6_12mo'
                band_label = f'6–12 mo ({days_to_end}d)'
            cur = u['current_monthly']
            rollover_rows.append(
                {
                    'sort_key': (days_to_end, -abs(float(gap_sb)), ev.id),
                    'event_id': ev.id,
                    'property_label': u['property_label'],
                    'title': u['title'],
                    'kind': 'rollover',
                    'renewal_band': band,
                    'renewal_band_label': band_label,
                    'current_monthly': cur,
                    'suggested_monthly': suggested,
                    'breakeven_allocated_monthly': breakeven,
                    'gap_suggested_minus_breakeven': gap_sb,
                    'days_vacant': None,
                    'vacancy_started': None,
                    'days_to_end': days_to_end,
                    'lease_end': end,
                    'doc_url': doc,
                    'pipeline_status': ev.lease_pipeline_status,
                    'pipeline_label': ev.get_lease_pipeline_status_display(),
                    'last_change_summary': _format_last_change(last_ch),
                }
            )

    vacant_rows.sort(key=lambda r: r['sort_key'])
    rollover_rows.sort(key=lambda r: r['sort_key'])
    merged = vacant_rows + rollover_rows
    for r in merged:
        r.pop('sort_key', None)
    return merged


def build_money_moves_bundle(
    lease_rows: list[BusinessCalendarEvent],
    *,
    today=None,
) -> dict:
    rows = build_rollover_vacancy_rows(lease_rows, today=today)
    lim = _money_moves_limit()
    digest_slice = rows[:lim]
    return {
        'show_section': bool(digest_slice),
        'money_moves_digest': digest_slice,
        'rollover_vacancy_rows': rows,
        'digest_limit': lim,
        'rollover_dashboard_url': _rollover_dashboard_url(),
    }
