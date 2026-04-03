"""Short text diff between successive lease-comp agent reports for digest."""

from __future__ import annotations


def build_lease_comp_diff_summary(previous_report: str, new_report: str, max_lines: int = 48) -> str:
    """Returns a compact unified-diff excerpt; empty if nothing to compare."""
    a = (previous_report or '').splitlines()
    b = (new_report or '').splitlines()
    if not a and not b:
        return ''
    import difflib

    diff = list(
        difflib.unified_diff(
            a,
            b,
            fromfile='prior_run',
            tofile='latest_run',
            lineterm='',
            n=2,
        )
    )
    if not diff:
        return 'No line-level changes detected vs prior run (reports may match).'
    tail = diff[: max_lines + 10]
    body = '\n'.join(tail[:max_lines])
    if len(tail) > max_lines:
        body += '\n… (truncated)'
    return body
