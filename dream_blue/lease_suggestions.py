"""
Suggested asking rents per lease row: above-grade $/sf × location factor + storage $/sf.

Rates default from settings; location multipliers reflect downtown Bemidji context
(corner + kitchen vs inline retail vs service use). Tune env vars or admin SF.
"""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal

from django.conf import settings

# property_label → multiplier on above-grade rent only (storage uses flat $/sf).
_LOCATION = {
    '401 A Beltrami Ave.': (
        Decimal('1.52'),
        'Prime corner; commercial kitchen; owner-funded buildout for tenant — highest suggested rate.',
    ),
    '401 B Beltrami Ave.': (
        Decimal('1.18'),
        'Street-facing retail; not on corner; downtown near the lake.',
    ),
    '211 4th St.': (
        Decimal('0.77'),
        'Tattoo / service retail; above-grade + below-grade storage (modest storage rate).',
    ),
    '207 4th St.': (
        Decimal('1.05'),
        'Available; downtown Bemidji near the lake; above-grade + below-grade storage '
        '(below grade fire-zoned for storage only).',
    ),
}


def _money_psf_year(key: str, default: str) -> Decimal:
    raw = getattr(settings, key, default)
    try:
        return Decimal(str(raw).strip())
    except Exception:
        return Decimal(default)


def _round_monthly_rent(monthly: Decimal) -> Decimal:
    step = Decimal('25')
    return (monthly / step).to_integral_value(rounding=ROUND_HALF_UP) * step


def build_lease_suggestion_rows(leases: list) -> dict:
    """
    Returns dict with 'rows' (list of display dicts) and 'footnote' (methodology str).
    """
    base_above = _money_psf_year('DREAM_BLUE_SUGGEST_RENT_PSF_YEAR_ABOVE', '9.5')
    base_stor = _money_psf_year('DREAM_BLUE_SUGGEST_RENT_PSF_YEAR_STORAGE', '2')
    if base_above < Decimal('0'):
        base_above = Decimal('0')
    if base_stor < Decimal('0'):
        base_stor = Decimal('0')

    rows: list[dict] = []
    total_suggested = Decimal('0')

    for ev in leases:
        prop = (ev.property_label or '').strip()
        above = int(ev.square_footage or 0)
        storage = int(ev.square_footage_storage or 0)
        mult, tag = _LOCATION.get(prop, (Decimal('1'), ''))

        annual = (
            Decimal(above) * base_above * mult + Decimal(storage) * base_stor
        ).quantize(Decimal('0.01'))
        monthly = (annual / Decimal('12')).quantize(Decimal('0.01'))
        suggested = _round_monthly_rent(monthly)

        contract = ev.amount
        delta = None
        if contract is not None:
            delta = (suggested - contract).quantize(Decimal('0.01'))

        total_suggested += suggested

        rows.append(
            {
                'property_label': prop or '—',
                'title': ev.title,
                'above_sf': above if above else None,
                'storage_sf': storage if storage else None,
                'suggested_monthly': suggested,
                'contract_monthly': contract,
                'has_contract': contract is not None,
                'delta_vs_contract': delta,
                'location_note': tag,
            }
        )

    footnote = (
        f'Suggested rent = above-grade sf × ${base_above}/sf/yr × location factor + '
        f'storage sf × ${base_stor}/sf/yr, rounded to nearest $25. '
        'Adjust DREAM_BLUE_SUGGEST_RENT_PSF_YEAR_ABOVE and '
        'DREAM_BLUE_SUGGEST_RENT_PSF_YEAR_STORAGE; not a lease quote.'
    )

    return {
        'rows': rows,
        'total_suggested_monthly': total_suggested,
        'footnote': footnote,
        'show_section': bool(rows),
    }
