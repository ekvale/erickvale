"""
Single digest section: per-unit current vs suggested vs breakeven allocation + portfolio cap/cash rows.
"""

from __future__ import annotations

from decimal import Decimal

from django.conf import settings

from .lease_economics import build_lease_economics_snapshot, lease_row_total_sqft
from .lease_suggestions import build_lease_suggestion_rows
from .models import LeaseRentBasis


def _fmt_dollars(d: Decimal | None) -> str:
    if d is None:
        return ''
    x = Decimal(str(d))
    if x == x.to_integral_value():
        return f'${int(x):,}'
    return f'${x:,.2f}'


def build_lease_rates_digest_section(lease_rows: list) -> dict:
    """
    Merges lease schedule, suggested asks, and lease_economics into one template-ready bundle.
    """
    eco = build_lease_economics_snapshot()
    if not lease_rows or not eco.get('show_section'):
        return {'show_section': False}

    sug = build_lease_suggestion_rows(lease_rows)
    req = eco['required_gross_monthly']
    total_sf = int(eco['total_leasable_sqft'] or 0)
    n = len(lease_rows)

    unit_rows: list[dict] = []
    for ev, srow in zip(lease_rows, sug['rows']):
        tsf = lease_row_total_sqft(ev)
        if total_sf > 0:
            breakeven_share = (
                req * Decimal(tsf) / Decimal(str(total_sf))
            ).quantize(Decimal('0.01'))
        else:
            breakeven_share = (req / Decimal(n)).quantize(Decimal('0.01')) if n else Decimal('0')

        doc_url = (getattr(ev, 'lease_document_url', None) or '').strip() or (
            (ev.reference_url or '').strip()
        )
        basis = getattr(ev, 'rent_basis', None) or LeaseRentBasis.UNKNOWN
        try:
            basis_label = dict(LeaseRentBasis.choices).get(basis, basis)
        except Exception:
            basis_label = str(basis)

        tsf = int(srow['above_sf'] or 0) + int(srow['storage_sf'] or 0)
        cur_m = srow['contract_monthly']
        sug_m = srow['suggested_monthly']
        actual_psf_year = None
        suggested_psf_year = None
        if tsf > 0:
            if srow['has_contract'] and cur_m is not None:
                actual_psf_year = (cur_m * Decimal('12') / Decimal(tsf)).quantize(
                    Decimal('0.01')
                )
            if sug_m is not None:
                suggested_psf_year = (sug_m * Decimal('12') / Decimal(tsf)).quantize(
                    Decimal('0.01')
                )
        breakeven_psf_year = None
        if tsf > 0 and breakeven_share is not None:
            breakeven_psf_year = (breakeven_share * Decimal('12') / Decimal(tsf)).quantize(
                Decimal('0.01')
            )

        unit_rows.append(
            {
                'property_label': srow['property_label'],
                'title': srow['title'],
                'due_date': ev.due_date,
                'end_date': ev.end_date,
                'above_sf': srow['above_sf'],
                'storage_sf': srow['storage_sf'],
                'total_sf': tsf,
                'has_contract': srow['has_contract'],
                'current_monthly': srow['contract_monthly'],
                'suggested_monthly': srow['suggested_monthly'],
                'delta_vs_contract': srow['delta_vs_contract'],
                'breakeven_allocated_monthly': breakeven_share,
                'breakeven_psf_year': breakeven_psf_year,
                'location_note': srow['location_note'],
                'rent_basis': basis,
                'rent_basis_label': basis_label,
                'rent_basis_note': (getattr(ev, 'rent_basis_note', None) or '').strip(),
                'document_url': doc_url,
                'actual_psf_year': actual_psf_year,
                'suggested_psf_year': suggested_psf_year,
            }
        )

    try:
        base_above = Decimal(
            str(getattr(settings, 'DREAM_BLUE_SUGGEST_RENT_PSF_YEAR_ABOVE', '9.5')).strip()
        )
        base_stor = Decimal(
            str(getattr(settings, 'DREAM_BLUE_SUGGEST_RENT_PSF_YEAR_STORAGE', '2')).strip()
        )
    except Exception:
        base_above = Decimal('9.5')
        base_stor = Decimal('2')

    logic_bullets = [
        (
            '<strong>Current rent</strong> is the in-place monthly amount from each lease row. Use the '
            '<strong>Rent basis</strong> column (Gross vs NNN / unknown) and notes so comparisons to '
            '<strong>suggested</strong> (a gross-oriented ask model) are interpreted honestly. Suggested '
            'rent is not a CAM or NNN pass-through estimate.'
        ),
        (
            '<strong>Suggested rent</strong> is an illustrative asking rate: above-grade sf × '
            f'${base_above}/sf/yr × a <em>location / use</em> factor, plus below-grade storage sf × '
            f'${base_stor}/sf/yr (storage only; no factor), rounded to the nearest $25. '
            '<strong>Tara Thai (401 A)</strong> uses the highest factor: prime corner, commercial kitchen, '
            'and owner-funded buildout to support the restaurant — so its suggested rate should read '
            'above the other units. Tune rates via <code>DREAM_BLUE_SUGGEST_RENT_PSF_YEAR_ABOVE</code> '
            'and <code>DREAM_BLUE_SUGGEST_RENT_PSF_YEAR_STORAGE</code>.'
        ),
        (
            '<strong>Breakeven share</strong> splits the portfolio <strong>required gross potential rent</strong> '
            f'(monthly cash out ÷ (1 − {eco["vacancy_assumption_pct"]}% economic vacancy)) across units by '
            'each unit’s fraction of total building sf (above + storage). The column sums to that required '
            'GPR; it is not a lease quote for any single suite.'
        ),
        (
            '<strong>Portfolio rows</strong> below the units sum operating and loan cash out, rent collected, '
            'and required GPR. <strong>Trailing NOI</strong> for the cap band is rent collected minus '
            '<em>operating</em> expenses only (debt service excluded). '
            '<strong>Implied value</strong> = trailing annual NOI ÷ cap rate at the low and high ends of '
            f'{eco["cap_rate_benchmark_low_pct"]}%–{eco["cap_rate_benchmark_high_pct"]}% — illustrative, '
            'not an appraisal.'
        ),
    ]

    if eco.get('benchmark_configured'):
        logic_bullets.append(
            '<strong>Optional $/sf benchmark</strong> (if configured) compares breakeven portfolio $/sf/yr '
            'to a market reference you supply — see the row in the table.'
        )

    return {
        'show_section': True,
        'unit_rows': unit_rows,
        'portfolio': eco,
        'total_suggested_monthly': sug['total_suggested_monthly'],
        'suggest_footnote': sug['footnote'],
        'logic_bullets': logic_bullets,
    }


def lease_rates_markdown_lines(lease_rows: list) -> list[str]:
    """Markdown lines for GrantScout / operations appendix."""
    bundle = build_lease_rates_digest_section(lease_rows)
    if not bundle.get('show_section'):
        return ['_No active leases in schedule._']

    lines = [
        '| Property | Tenant | Start | End | Basis | Above sf | Storage | Current/mo | Suggested/mo | Breakeven share/mo |',
        '| --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: |',
    ]
    p = bundle['portfolio']
    for r in bundle['unit_rows']:
        st = r['due_date'].isoformat() if r['due_date'] else ''
        en = r['end_date'].isoformat() if r['end_date'] else ''
        cur = _fmt_dollars(r['current_monthly']) if r['has_contract'] else '—'
        basis = _md_esc(str(r.get('rent_basis_label') or ''))
        lines.append(
            f"| {_md_esc(r['property_label'])} | {_md_esc(r['title'])} | {st} | {en} | {basis} | "
            f"{r['above_sf'] or '—'} | {r['storage_sf'] or '—'} | {cur} | "
            f"${int(r['suggested_monthly']):,} | {_fmt_dollars(r['breakeven_allocated_monthly'])} |"
        )

    lines.extend(
        [
            '',
            '| Portfolio line | Amount |',
            '| --- | ---: |',
            f"| Operating expenses (mo) | {_fmt_dollars(p['monthly_operating'])} |",
            f"| Loan payments (mo) | {_fmt_dollars(p['monthly_loans'])} |",
            f"| **Total cash out (mo)** | **{_fmt_dollars(p['monthly_out'])}** |",
            f"| Rent collected (mo) | {_fmt_dollars(p['monthly_rent_collected'])} |",
            f"| **Required GPR (mo) @ {p['vacancy_assumption_pct']}% vacancy** | **{_fmt_dollars(p['required_gross_monthly'])}** |",
            f"| Gap vs required (mo) | {_fmt_dollars(p['shortfall_monthly'])} |",
            f"| NOI monthly (rent − operating, excl. loans) | {_fmt_dollars(p['noi_monthly'])} |",
            f"| NOI annual (approx.) | {_fmt_dollars(p['noi_annual'])} |",
        ]
    )
    if p.get('show_cap_implied_value') and p.get('implied_value_range_min') is not None:
        lines.append(
            f"| Implied value @ {p['cap_rate_benchmark_low_pct']}%–{p['cap_rate_benchmark_high_pct']}% cap | "
            f"~{_fmt_dollars(p['implied_value_range_min'])} – {_fmt_dollars(p['implied_value_range_max'])} |"
        )
    if p.get('benchmark_configured'):
        bnote = _md_esc((p.get('benchmark_note') or '')[:160])
        lines.append(
            f"| Optional benchmark $/sf/yr | {p['benchmark_psf_year']}; {bnote} |"
        )
    lines.extend(
        [
            '',
            f"_Suggested formula: {bundle['suggest_footnote']}_",
            '',
            '_Breakeven share allocates required GPR by each unit’s fraction of total building sf._',
        ]
    )
    return lines


def _md_esc(s: str) -> str:
    return (s or '').replace('|', '\\|').replace('\n', ' ')
