"""Build stored report text and snapshot dict from normalized GrantScout agent payload."""

from __future__ import annotations

from typing import Any


def build_agent_snapshot(payload: dict[str, Any]) -> dict[str, Any]:
    """JSON-serializable copy of the normalized payload for DB storage."""
    return {
        'coverage_summary': payload.get('coverage_summary', ''),
        'search_queries': list(payload.get('search_queries') or []),
        'opportunities': [dict(o) for o in payload.get('opportunities') or []],
    }


def build_compiled_report(payload: dict[str, Any]) -> str:
    """Markdown-style report for admin and archival."""
    lines: list[str] = [
        '# GrantScout run report',
        '',
        '## Coverage summary',
        '',
        (payload.get('coverage_summary') or '').strip() or '_None_',
        '',
        '## Research topics / queries',
        '',
    ]
    for q in payload.get('search_queries') or []:
        lines.append(f'- {q}')
    if len(lines) == 6:
        lines.append('_None listed_')
    lines.extend(['', '## Opportunities', ''])

    for i, o in enumerate(payload.get('opportunities') or [], start=1):
        cat = o.get('category', '')
        typ = o.get('opportunity_type', '')
        head = f'### {i}. {typ or cat or "Opportunity"}'
        lines.append(head)
        lines.append('')
        lines.append(f'- **Category:** {cat}')
        if o.get('deadline'):
            lines.append(f'- **Deadline:** {o["deadline"]}')
        lines.append(f'- **Priority score:** {o.get("priority_score", 0)}')
        if o.get('source_url_check_passed') is False:
            lines.append('- **Link check:** automated HTTP check failed — verify this URL manually.')
        lines.append(f'- **Source:** {o.get("source_url", "")}')
        lines.append('')
        lines.append(str(o.get('summary', '')).strip())
        lines.append('')
        if o.get('eligibility'):
            lines.append(f'**Eligibility:** {o["eligibility"]}')
            lines.append('')
        if o.get('action_recommended'):
            lines.append(f'**Recommended action:** {o["action_recommended"]}')
            lines.append('')
        lines.append('---')
        lines.append('')

    bad = [
        o
        for o in (payload.get('opportunities') or [])
        if o.get('source_url_check_passed') is False
    ]
    if bad:
        lines.extend(
            [
                '',
                '## Links that failed automated verification',
                '',
                'These opportunities remain in the list above. URLs may be incorrect, moved, or blocked to automated requests—open from a browser and search the program name if needed.',
                '',
            ]
        )
        for o in bad:
            url = o.get('source_url', '')
            summ = str(o.get('summary', '')).strip().replace('\n', ' ')[:200]
            lines.append(f'- {url} — _{summ}_')

    return '\n'.join(lines).strip()
