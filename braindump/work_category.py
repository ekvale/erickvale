"""
Map capture text to a work stream: MDH (default), Dream Blue, or Sioux Chef.

Rules are applied after AI parse so categorization stays consistent with these names/topics.
"""

from __future__ import annotations

import re

# Display labels stored in CaptureItem.category_label
CATEGORY_MDH = 'MDH'
CATEGORY_DREAM_BLUE = 'Dream Blue'
CATEGORY_SIOUX_CHEF = 'Sioux Chef'

# Higher number = wins when merging rule-based vs AI label for the same capture.
_STREAM_PRIORITY = {
    CATEGORY_MDH: 1,
    CATEGORY_DREAM_BLUE: 2,
    CATEGORY_SIOUX_CHEF: 3,
}

_MDH_TOKEN = re.compile(r'\bmdh\b', re.IGNORECASE)


def _canonical_from_ai_string(s: str) -> str | None:
    """Match full stream names; avoid substring false positives (e.g. \"not mdh\")."""
    if re.search(r'\bnomoar\b', s, re.IGNORECASE):
        return CATEGORY_SIOUX_CHEF
    if _MDH_TOKEN.search(s):
        return CATEGORY_MDH
    if re.search(r'\bdream\s*blue\b', s, re.IGNORECASE):
        return CATEGORY_DREAM_BLUE
    if re.search(r'\bsioux\s*chef\b', s, re.IGNORECASE):
        return CATEGORY_SIOUX_CHEF
    compact = re.sub(r'[\s_-]+', '', s)
    if compact == 'dreamblue':
        return CATEGORY_DREAM_BLUE
    if compact == 'siouxchef':
        return CATEGORY_SIOUX_CHEF
    if compact == 'mdh':
        return CATEGORY_MDH
    return None

_PROPERTY_TERMS = (
    'property',
    'properties',
    'lease',
    'leases',
    'leasing',
    'rental',
    'tenant',
    'tenants',
    'landlord',
    'vacancy',
    'vacancies',
    'apartment',
    'building',
    'portfolio',
    'real estate',
    'reit',
    'eviction',
    'hoa',
    'mortgage',
    'refinance',
)

_UNIT_WORD = re.compile(r'\bunits?\b', re.IGNORECASE)


def _word_pat(name: str) -> re.Pattern:
    return re.compile(rf'\b{re.escape(name)}\b', re.IGNORECASE)


_SIOUX_PATTERNS = (
    _word_pat('sean'),
    re.compile(r'sioux\s*chef', re.IGNORECASE),
    re.compile(r'\bnomoar\b', re.IGNORECASE),
)

_WENDY = _word_pat('wendy')

_MDH_NAMES = ('abby', 'hannah', 'analise', 'tim', 'angela', 'mike')
_MDH_PATTERNS = tuple(_word_pat(n) for n in _MDH_NAMES)


def canonical_work_stream_label(raw: str | None) -> str | None:
    """
    Map AI or free-text labels to MDH / Dream Blue / Sioux Chef.
    Returns None if not one of those streams (caller keeps rule-based default).
    """
    if raw is None:
        return None
    s = str(raw).strip()
    if not s:
        return None
    return _canonical_from_ai_string(s.lower())


def resolve_work_category(body: str, ai_category: str | None) -> str:
    """
    Combine keyword rules (Sioux Chef > Dream Blue > MDH names > default MDH) with an
    optional AI ``category`` field: the higher-priority stream wins; ties go to rules.
    """
    rule = work_category_from_body(body)
    ai_norm = canonical_work_stream_label(ai_category)
    if ai_norm is None:
        return rule
    pr = _STREAM_PRIORITY.get(rule, 1)
    pa = _STREAM_PRIORITY.get(ai_norm, 1)
    if pa > pr:
        return ai_norm
    return rule


def work_category_from_body(body: str) -> str:
    """
    Sioux Chef > Dream Blue > MDH (named colleagues) > default MDH.
    """
    text = (body or '').strip()
    if not text:
        return CATEGORY_MDH

    for pat in _SIOUX_PATTERNS:
        if pat.search(text):
            return CATEGORY_SIOUX_CHEF

    if _WENDY.search(text):
        return CATEGORY_DREAM_BLUE

    lower = text.lower()
    if any(term in lower for term in _PROPERTY_TERMS) or _UNIT_WORD.search(text):
        return CATEGORY_DREAM_BLUE

    for pat in _MDH_PATTERNS:
        if pat.search(text):
            return CATEGORY_MDH

    return CATEGORY_MDH
