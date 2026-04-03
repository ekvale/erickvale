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

Ground rules:
- Focus on **Bemidji, Beltrami County**, and reasonable comparables in **north-central Minnesota** (e.g. Grand Forks ND–adjacent markets only when Bemidji data is thin).
- The user named a **reference property** and a **subject portfolio** (their units). Benchmark **similar size, use type, build-out, sprinkler, kitchen**, and lease structure where possible.
- Use the **best current evidence you can** (listings, broker blurbs, news, assessor or economic development pages). **Perplexity / web-aware tools:** prefer fresh sources.
- **Do not fabricate** exact asking rents, dollar amounts, or lease comps. If you only have ranges or older data, say so explicitly (e.g. "reported in 2023", "asking rent not published").
- When you cite a number or comp, **name the source** in the same line or the next (URL if available).
- **Plain text only** in report_markdown: no Markdown `#` headers. Use ALL CAPS one-line section titles, blank lines between sections, and simple hyphen bullets.
- Return **only** valid JSON matching the user schema. No markdown fences."""


def _lease_comp_user_prompt(reference: str, subject: str) -> str:
    ref = (reference or '').strip() or '(not configured — ask user for reference property details)'
    subj = (subject or '').strip() or '(not configured — ask user for their unit mix)'
    return f"""Produce an internal **lease comparable / market rent** memo for underwriting and storytelling.

REFERENCE PROPERTY (benchmark / comp anchor):
{ref}

SUBJECT PORTFOLIO (what we need to price / defend):
{subj}

Tasks:
1. Summarize how the reference property would likely be marketed (use type, typical tenant, quality tier).
2. List **specific** comparable properties or spaces if you find them (address or listing name, approximate size, asking rent or terms if stated, source URL). If nothing close exists online, say so and broaden to "typical flex / light industrial / small-bay" ranges **with caveats**.
3. Discuss implications for the subject portfolio (four ~2,000 sq ft units with one kitchen unit vs non-kitchen units).
4. Note data gaps and what a broker or appraiser would need next.

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
