"""
Lease / flex space comparables agent — same LLM providers as GrantScout (OpenAI, Anthropic, Perplexity).

Returns JSON with a plain-text report suitable for the Dream Blue digest email.
"""

from __future__ import annotations

import json
import logging
from typing import Any

import requests
from django.conf import settings

from .grantscout_agent import GrantScoutAgentError, _extract_json_object

logger = logging.getLogger(__name__)


LEASE_COMP_SYSTEM = """You are a commercial real estate research assistant for Dream Blue (Minnesota / Bemidji area).

Geography (strict):
- Only cite comps and listings that are clearly in **Minnesota**, preferably **Beltrami County / Bemidji**, then **north-central MN** (e.g. Grand Rapids, Park Rapids, Detroit Lakes, Thief River Falls, International Falls corridor) when Bemidji is thin.
- **Reject irrelevant geographies:** if search tools return results in other states (e.g. Connecticut, Texas) or clearly residential-only apartment complexes far from MN, **do not** use them in the memo. Say "off-target results discarded" in coverage_summary if that happened — never treat out-of-market junk as comps.

Search strategy (wide net):
- The owner’s building is **retail- and service-heavy** (salons, tattoo, restaurants, small retail). Prioritize **close matches** first (street retail, restaurant, service bays, small storefronts).
- **Also run a broad commercial scan:** any **commercial** property **newly listed, recently updated, or newly marketed** in the region — **retail, office, medical, flex, light industrial, mixed-use, vacant commercial** — even if size or use does not match 2,000 sf units. These are **market supply and pricing signals**, not perfect analogs. Label them as "broad market listing" when use-type differs.

Rent discipline:
- For **every** rent or occupancy-cost figure, state **NNN**, **gross**, **modified gross**, or **unknown**, and **asking / listing / broker quote / reported deal**.
- **Do not fabricate** dollars; if unpublished, say so.

Output:
- Include **CLOSE COMPS** (best matches) and **BROAD REGIONAL COMMERCIAL LISTINGS** (new/recent, any commercial type in geography) as separate sections in report_markdown.
- **MARKET TREND / PRICING TAKEAWAY** when evidence supports it; if only broad listings exist, infer **supply / asking-level hints** with caveats.
- **Plain text only** in report_markdown: ALL CAPS section titles, blank lines, hyphen bullets. No Markdown `#`. No markdown fences in JSON.
- Return **only** valid JSON matching the user schema."""


def _lease_comp_user_prompt(reference: str, subject: str) -> str:
    ref = (reference or '').strip() or '(not configured — ask user for reference property details)'
    subj = (subject or '').strip() or '(not configured — ask user for their unit mix)'
    return f"""Produce an internal **lease comparable / commercial market** memo: **trends and pricing** for the owner’s asset vs the **actual local market** (not an appraisal).

REFERENCE PROPERTY (owner benchmark):
{ref}

SUBJECT PORTFOLIO + research intent:
{subj}

Tasks:
1. **REFERENCE CONTEXT:** How this building fits Bemidji/Beltrami (retail & service tenants, quality tier) and what the owner is tracking.

2. **CLOSE COMPS:** Specific listings or deals that resemble **retail, restaurant, salon/service, or small storefront** space in **MN / Bemidji area first**. For each: address or listing ID, size if known, rent **NNN vs gross vs unknown**, **asking vs deal**, date seen if known, URL.

3. **BROAD REGIONAL COMMERCIAL SCAN (required):** Independently search for **any commercial** properties **newly listed or recently marketed** in **Bemidji, Beltrami County, and north-central MN** — include retail, office, flex, warehouse, medical, mixed-use, etc. **Do not require** a match to 2,000 sf or kitchen. Purpose: **new supply and asking levels** in the region. If a hit is a sale listing, note whether lease rate or investment context is mentioned. If **zero** credible local hits after a deliberate search, say so clearly (do not pad with out-of-state residential).

4. **GEOGRAPHY QC:** If your tools returned off-market results (wrong state, residential apartments unrelated to MN CRE), **discard** them; mention briefly in coverage_summary that they were excluded.

5. **IMPLICATIONS FOR SUBJECT UNITS:** Tie findings to the four units (kitchen unit vs others) only where logical; otherwise use broad scan for **overall market temperature**.

6. **MARKET TREND / PRICING TAKEAWAY:** Directional read from **local** evidence; if only broad listings, comment on **volume of new listings / asking posture** with caveats.

7. **DATA GAPS / NEXT STEPS**

Return a JSON object with exactly these keys:
- "coverage_summary": string (2-4 sentences: what you searched and limits)
- "search_queries": array of strings (topics or queries you used)
- "report_markdown": string (plain text body per system rules; aim for 400-1200 words, concise)"""


def _anthropic_lease_comp(api_key: str, model: str, user_block: str, timeout: int = 180) -> str:
    url = getattr(settings, 'ANTHROPIC_API_URL', 'https://api.anthropic.com/v1/messages')
    version = getattr(settings, 'ANTHROPIC_VERSION', '2023-06-01')
    try:
        max_tokens = int(getattr(settings, 'GRANTSCOUT_ANTHROPIC_MAX_TOKENS', 8192))
    except (TypeError, ValueError):
        max_tokens = 8192
    max_tokens = max(2048, min(max_tokens, 8192))

    resp = requests.post(
        url,
        headers={
            'x-api-key': api_key,
            'anthropic-version': str(version),
            'Content-Type': 'application/json',
        },
        json={
            'model': model,
            'max_tokens': max_tokens,
            'system': LEASE_COMP_SYSTEM,
            'messages': [{'role': 'user', 'content': user_block}],
        },
        timeout=timeout,
    )
    if resp.status_code >= 400:
        logger.error('Lease comp Anthropic HTTP %s: %s', resp.status_code, resp.text[:800])
        resp.raise_for_status()
    body = resp.json()
    parts = body.get('content') or []
    texts: list[str] = []
    for block in parts:
        if isinstance(block, dict) and block.get('type') == 'text':
            texts.append(block.get('text') or '')
    if not texts:
        raise GrantScoutAgentError('Anthropic lease comp response missing text')
    return ''.join(texts)


def _openai_lease_comp_json(api_key: str, model: str, user_block: str, url: str, timeout: int = 120) -> str:
    payload = {
        'model': model,
        'temperature': 0.25,
        'response_format': {'type': 'json_object'},
        'messages': [
            {'role': 'system', 'content': LEASE_COMP_SYSTEM},
            {'role': 'user', 'content': user_block},
        ],
    }
    resp = requests.post(
        url,
        headers={
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
        },
        json=payload,
        timeout=timeout,
    )
    if resp.status_code >= 400:
        logger.error('Lease comp OpenAI HTTP %s: %s', resp.status_code, resp.text[:500])
        resp.raise_for_status()
    body = resp.json()
    choices = body.get('choices') or []
    if not choices:
        raise GrantScoutAgentError('OpenAI lease comp missing choices')
    message = choices[0].get('message') or {}
    content = message.get('content')
    if not content:
        raise GrantScoutAgentError('OpenAI lease comp missing content')
    return str(content)


def _perplexity_lease_comp(api_key: str, model: str, user_block: str, url: str, timeout: int = 120) -> str:
    # Reuse OpenAI-shaped API; no json_object guarantee — still request JSON in system prompt.
    payload = {
        'model': model,
        'temperature': 0.25,
        'messages': [
            {'role': 'system', 'content': LEASE_COMP_SYSTEM},
            {'role': 'user', 'content': user_block},
        ],
    }
    resp = requests.post(
        url,
        headers={
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
        },
        json=payload,
        timeout=timeout,
    )
    if resp.status_code >= 400:
        logger.error('Lease comp Perplexity HTTP %s: %s', resp.status_code, resp.text[:500])
        resp.raise_for_status()
    body = resp.json()
    choices = body.get('choices') or []
    if not choices:
        raise GrantScoutAgentError('Perplexity lease comp missing choices')
    message = choices[0].get('message') or {}
    content = message.get('content')
    if not content:
        raise GrantScoutAgentError('Perplexity lease comp missing content')
    return str(content)


def normalize_lease_comp_payload(data: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise GrantScoutAgentError('Lease comp agent returned non-object JSON')
    summary = str(data.get('coverage_summary', '')).strip()
    report = str(data.get('report_markdown', '')).strip()
    queries = data.get('search_queries')
    if not isinstance(queries, list):
        queries = []
    queries = [str(q) for q in queries if str(q).strip()][:40]
    if len(report) < 100:
        raise GrantScoutAgentError(
            'Lease comp report_markdown too short or empty — refine prompts or retry',
        )
    return {
        'coverage_summary': summary[:4000],
        'search_queries': queries,
        'report_markdown': report[:24000],
    }


def run_lease_comp_agent(
    *,
    reference: str | None = None,
    subject: str | None = None,
) -> dict[str, Any]:
    """
    Call configured provider; return normalized dict with coverage_summary, search_queries, report_markdown.
    """
    ref = reference if reference is not None else getattr(
        settings, 'DREAM_BLUE_LEASE_COMP_REFERENCE', ''
    )
    subj = subject if subject is not None else getattr(
        settings, 'DREAM_BLUE_LEASE_COMP_SUBJECT', ''
    )
    user_block = _lease_comp_user_prompt(str(ref), str(subj))
    provider = (getattr(settings, 'GRANTSCOUT_LLM_PROVIDER', 'openai') or 'openai').strip().lower()

    if provider == 'anthropic':
        key = (getattr(settings, 'ANTHROPIC_API_KEY', '') or '').strip()
        if not key:
            raise GrantScoutAgentError('Set ANTHROPIC_API_KEY for provider=anthropic')
        model = getattr(settings, 'GRANTSCOUT_ANTHROPIC_MODEL', 'claude-sonnet-4-6')
        raw = _anthropic_lease_comp(key, model, user_block)
    elif provider == 'perplexity':
        key = (getattr(settings, 'PERPLEXITY_API_KEY', '') or '').strip()
        if not key:
            raise GrantScoutAgentError('Set PERPLEXITY_API_KEY for provider=perplexity')
        model = getattr(settings, 'GRANTSCOUT_PERPLEXITY_MODEL', 'sonar')
        url = getattr(settings, 'PERPLEXITY_API_URL', 'https://api.perplexity.ai/chat/completions')
        raw = _perplexity_lease_comp(key, model, user_block, url)
    elif provider == 'openai':
        key = (getattr(settings, 'OPENAI_API_KEY', '') or '').strip()
        if not key:
            raise GrantScoutAgentError('Set OPENAI_API_KEY for provider=openai')
        model = getattr(settings, 'GRANTSCOUT_OPENAI_MODEL', 'gpt-4o-mini')
        url = getattr(
            settings,
            'OPENAI_CHAT_COMPLETIONS_URL',
            'https://api.openai.com/v1/chat/completions',
        )
        raw = _openai_lease_comp_json(key, model, user_block, url)
    else:
        raise GrantScoutAgentError(
            f'Unknown GRANTSCOUT_LLM_PROVIDER={provider!r} for lease comp.',
        )

    try:
        data = _extract_json_object(raw)
    except (json.JSONDecodeError, ValueError) as e:
        raise GrantScoutAgentError(f'Lease comp invalid JSON from LLM: {e}') from e
    return normalize_lease_comp_payload(data)
