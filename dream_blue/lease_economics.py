"""
Portfolio lease economics for digest: expense roll-up, vacancy-adjusted breakeven, $/sf vs benchmark.

Uses active BusinessCalendarEvent rows (amounts). Benchmark $/sf/year is optional via settings.
"""

from __future__ import annotations

from decimal import Decimal

from django.conf import settings
from django.db.models import Q, Sum
from django.utils import timezone

from .models import BusinessCalendarEvent, BusinessCalendarEventType

_EXPENSE_TYPES = (
    BusinessCalendarEventType.UTILITY,
    BusinessCalendarEventType.INSURANCE,
    BusinessCalendarEventType.PROPERTY_TAX,
    BusinessCalendarEventType.BILL,
    BusinessCalendarEventType.MAINTENANCE,
    BusinessCalendarEventType.LICENSE,
    BusinessCalendarEventType.OTHER,
)


def _sum_amount(qs) -> Decimal:
    t = qs.aggregate(s=Sum('amount'))['s']
    return t if t is not None else Decimal('0')


def _vacancy_pct() -> Decimal:
    raw = getattr(settings, 'DREAM_BLUE_LEASE_ECONOMICS_VACANCY_PCT', '8')
    try:
        v = Decimal(str(raw).strip())
    except Exception:
        v = Decimal('8')
    if v < Decimal('0'):
        v = Decimal('0')
    if v > Decimal('40'):
        v = Decimal('40')
    return v


def _benchmark_psf_year() -> tuple[Decimal | None, str]:
    raw = (getattr(settings, 'DREAM_BLUE_RENT_BENCHMARK_PSF_YEAR', '') or '').strip()
    note = (getattr(settings, 'DREAM_BLUE_RENT_BENCHMARK_NOTE', '') or '').strip()
    if not raw:
        return None, note
    try:
        return Decimal(raw), note
    except Exception:
        return None, note


def build_lease_economics_snapshot() -> dict:
    """
    Returns template-friendly dict. All money values are Decimal (Django templates format them).
    """
    today = timezone.localdate()
    base = BusinessCalendarEvent.objects.filter(is_active=True)

    monthly_operating = _sum_amount(base.filter(event_type__in=_EXPENSE_TYPES))
    monthly_loans = _sum_amount(base.filter(event_type=BusinessCalendarEventType.LOAN))
    monthly_out = monthly_operating + monthly_loans

    leases = list(
        base.filter(event_type=BusinessCalendarEventType.LEASE)
        .filter(Q(end_date__isnull=True) | Q(end_date__gte=today))
        .order_by('sort_order', 'due_date', 'id')
    )
    monthly_rent = sum(
        (e.amount for e in leases if e.amount is not None),
        start=Decimal('0'),
    )
    occupied = [e for e in leases if e.amount is not None]
    vacant = [e for e in leases if e.amount is None]

    occupied_sqft = sum(
        (e.square_footage for e in occupied if e.square_footage),
        start=0,
    )
    vacant_sqft = sum(
        (e.square_footage for e in vacant if e.square_footage),
        start=0,
    )
    total_leasable_sqft = sum(
        (e.square_footage for e in leases if e.square_footage),
        start=0,
    )

    vac_pct = _vacancy_pct()
    vac_factor = (Decimal('100') - vac_pct) / Decimal('100')
    if vac_factor <= 0:
        vac_factor = Decimal('1')
    required_gross_monthly = (monthly_out / vac_factor).quantize(Decimal('0.01'))
    shortfall_monthly = (required_gross_monthly - monthly_rent).quantize(Decimal('0.01'))

    n_units = len(leases)
    required_avg_rent_per_unit = None
    if n_units > 0:
        required_avg_rent_per_unit = (required_gross_monthly / Decimal(n_units)).quantize(
            Decimal('0.01')
        )

    required_psf_year_portfolio = None
    if total_leasable_sqft > 0:
        required_psf_year_portfolio = (
            (required_gross_monthly * Decimal('12')) / Decimal(total_leasable_sqft)
        ).quantize(Decimal('0.01'))

    portfolio_occupied_psf_year = None
    if occupied_sqft > 0 and monthly_rent > 0:
        portfolio_occupied_psf_year = (
            (monthly_rent * Decimal('12')) / Decimal(occupied_sqft)
        ).quantize(Decimal('0.01'))

    bench_psf, bench_note = _benchmark_psf_year()
    vs_benchmark = None
    if bench_psf is not None and required_psf_year_portfolio is not None:
        vs_benchmark = (required_psf_year_portfolio - bench_psf).quantize(Decimal('0.01'))

    physical_occupancy_pct = None
    if n_units > 0:
        physical_occupancy_pct = (
            Decimal(len(occupied)) / Decimal(n_units) * Decimal('100')
        ).quantize(Decimal('0.1'))

    return {
        'show_section': bool(leases),
        'monthly_operating': monthly_operating,
        'monthly_loans': monthly_loans,
        'monthly_out': monthly_out,
        'monthly_rent_collected': monthly_rent,
        'vacancy_assumption_pct': vac_pct,
        'required_gross_monthly': required_gross_monthly,
        'shortfall_monthly': shortfall_monthly,
        'required_avg_rent_per_unit': required_avg_rent_per_unit,
        'required_psf_year_portfolio': required_psf_year_portfolio,
        'portfolio_occupied_psf_year': portfolio_occupied_psf_year,
        'benchmark_psf_year': bench_psf,
        'benchmark_configured': bench_psf is not None,
        'benchmark_note': bench_note,
        'vs_benchmark_psf_year': vs_benchmark,
        'lease_unit_count': n_units,
        'occupied_unit_count': len(occupied),
        'vacant_unit_count': len(vacant),
        'occupied_sqft': occupied_sqft,
        'vacant_sqft': vacant_sqft,
        'total_leasable_sqft': total_leasable_sqft,
        'physical_occupancy_pct': physical_occupancy_pct,
        'sqft_complete': total_leasable_sqft > 0
        and sum(1 for e in leases if e.square_footage) == n_units,
    }
