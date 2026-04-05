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
