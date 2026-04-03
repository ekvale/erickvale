"""
GrantScout LLM agent: calls OpenAI or Perplexity (web-capable) and returns structured JSON.

Secrets: OPENAI_API_KEY and/or PERPLEXITY_API_KEY via Django settings / env only.
"""

from __future__ import annotations

import hashlib
import json
import logging
import re
from typing import Any
from urllib.parse import urlparse

import requests
from django.conf import settings
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError

from .models import GrantScoutCategory

logger = logging.getLogger(__name__)


class GrantScoutAgentError(RuntimeError):
    """LLM missing config, HTTP failure, or unparseable response."""


SYSTEM_PROMPT = """You are GrantScout, an internal research assistant for Dream Blue.
Focus: grants, tax credits, rebates, energy/weatherization incentives, small-business and
community development funding, and regulatory or compliance items relevant to Minnesota,
especially Beltrami County, Bemidji, and nearby tribal nations when applicable.

Rules:
- Prefer official sources: .gov, state agencies (e.g. MN DEED, Commerce, MPCA), federal (grants.gov, DOE, USDA), utilities, and established nonprofits.
- Each opportunity MUST include a real https source_url you are confident exists. If you cannot cite a stable URL, omit that item.
- Do not invent program names or deadlines; use null for unknown deadline.
- Return ONLY valid JSON matching the user schema. No markdown fences."""

USER_PROMPT = """Produce a monthly scan suitable for an internal dashboard.

Return a JSON object with exactly these keys:
- "coverage_summary": string (2-4 sentences on what you covered and limitations)
- "search_queries": array of strings (the logical queries or topics you used)
- "opportunities": array of 5-15 objects, each with:
  - "category": one of grant, tax_credit, rebate, regulatory, other
  - "opportunity_type": short label (e.g. "DEED program", "IRA rebate")
  - "eligibility": string (who qualifies, briefly)
  - "deadline": string "YYYY-MM-DD" or null
  - "summary": string (1-3 sentences)
  - "action_recommended": string (concrete next step)
  - "source_url": string (https URL to official page)
  - "priority_score": integer 0-100 (higher = more important for this org)

Prioritize items actionable for a Minnesota property / small-business operator in the Bemidji / north-central MN region."""


def _extract_json_object(text: str) -> dict[str, Any]:
    text = text.strip()
    if text.startswith('```'):
        parts = text.split('```')
        if len(parts) >= 2:
            inner = parts[1]
            if inner.lstrip().startswith('json'):
                inner = inner.lstrip()[4:].lstrip()
            text = inner.strip()
    return json.loads(text)


def _valid_https_url(url: str) -> bool:
    if not url or not isinstance(url, str):
        return False
    url = url.strip()
    try:
        parsed = urlparse(url)
        if parsed.scheme != 'https':
            return False
        URLValidator()(url)
        return bool(parsed.netloc)
    except ValidationError:
        return False


def _normalize_category(raw: str) -> str:
    if not raw:
        return GrantScoutCategory.OTHER
    key = str(raw).strip().lower().replace(' ', '_').replace('-', '_')
    mapping = {
        'grant': GrantScoutCategory.GRANT,
        'tax_credit': GrantScoutCategory.TAX_CREDIT,
        'taxcredit': GrantScoutCategory.TAX_CREDIT,
        'rebate': GrantScoutCategory.REBATE,
        'regulatory': GrantScoutCategory.REGULATORY,
        'other': GrantScoutCategory.OTHER,
    }
    return mapping.get(key, GrantScoutCategory.OTHER)


def _normalize_opportunity(raw: dict[str, Any]) -> dict[str, Any] | None:
    url = raw.get('source_url') or ''
    if not _valid_https_url(url):
        logger.warning('Skipping opportunity (invalid or non-https URL): %s', raw.get('summary', '')[:80])
        return None
    dedupe = hashlib.sha256(url.encode('utf-8')).hexdigest()[:64]
    deadline = raw.get('deadline')
    if deadline is not None and deadline != '':
        ds = str(deadline).strip()[:10]
        if not re.match(r'^\d{4}-\d{2}-\d{2}$', ds):
            deadline = None
        else:
            deadline = ds
    else:
        deadline = None
    try:
        score = int(raw.get('priority_score', 0))
    except (TypeError, ValueError):
        score = 0
    score = max(0, min(100, score))
    return {
        'category': _normalize_category(raw.get('category', '')),
        'opportunity_type': str(raw.get('opportunity_type', ''))[:128],
        'eligibility': str(raw.get('eligibility', ''))[:4000],
        'deadline': deadline,
        'summary': str(raw.get('summary', ''))[:8000] or '(no summary)',
        'action_recommended': str(raw.get('action_recommended', ''))[:4000],
        'source_url': url[:500],
        'priority_score': score,
        'dedupe_key': dedupe,
    }


def normalize_agent_payload(data: dict[str, Any]) -> dict[str, Any]:
    """Validate top-level keys and opportunity list."""
    if not isinstance(data, dict):
        raise GrantScoutAgentError('Agent returned non-object JSON')
    summary = str(data.get('coverage_summary', '')).strip()
    queries = data.get('search_queries')
    if not isinstance(queries, list):
        queries = []
    queries = [str(q) for q in queries if str(q).strip()][:50]
    raw_opps = data.get('opportunities')
    if not isinstance(raw_opps, list):
        raw_opps = []
    opportunities = []
    for item in raw_opps:
        if not isinstance(item, dict):
            continue
        norm = _normalize_opportunity(item)
        if norm:
            opportunities.append(norm)
    if not opportunities:
        raise GrantScoutAgentError('Agent returned no opportunities with valid https source_url')
    return {
        'coverage_summary': summary[:8000],
        'search_queries': queries,
        'opportunities': opportunities,
    }


def _chat_completions(url: str, api_key: str, model: str, timeout: int = 120) -> str:
    payload = {
        'model': model,
        'temperature': 0.25,
        'messages': [
            {'role': 'system', 'content': SYSTEM_PROMPT},
            {'role': 'user', 'content': USER_PROMPT},
        ],
    }
    # OpenAI JSON mode; Perplexity ignores unknown fields in some versions — include only if openai
    if 'openai.com' in url:
        payload['response_format'] = {'type': 'json_object'}
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
        logger.error('LLM HTTP %s: %s', resp.status_code, resp.text[:500])
        resp.raise_for_status()
    body = resp.json()
    choices = body.get('choices') or []
    if not choices:
        raise GrantScoutAgentError('LLM response missing choices')
    message = choices[0].get('message') or {}
    content = message.get('content')
    if not content:
        raise GrantScoutAgentError('LLM response missing content')
    if isinstance(content, list):
        # Some APIs return content parts
        parts = [p.get('text', '') for p in content if isinstance(p, dict)]
        content = ''.join(parts)
    return str(content)


def run_grantscout_agent() -> dict[str, Any]:
    """
    Call configured LLM provider and return normalized payload:
    coverage_summary, search_queries, opportunities (list of dicts).
    """
    provider = (getattr(settings, 'GRANTSCOUT_LLM_PROVIDER', 'openai') or 'openai').strip().lower()
    if provider == 'perplexity':
        key = (getattr(settings, 'PERPLEXITY_API_KEY', '') or '').strip()
        if not key:
            raise GrantScoutAgentError('Set PERPLEXITY_API_KEY for provider=perplexity')
        model = getattr(settings, 'GRANTSCOUT_PERPLEXITY_MODEL', 'sonar')
        url = getattr(settings, 'PERPLEXITY_API_URL', 'https://api.perplexity.ai/chat/completions')
        content = _chat_completions(url, key, model)
    else:
        key = (getattr(settings, 'OPENAI_API_KEY', '') or '').strip()
        if not key:
            raise GrantScoutAgentError('Set OPENAI_API_KEY or use GRANTSCOUT_LLM_PROVIDER=perplexity')
        model = getattr(settings, 'GRANTSCOUT_OPENAI_MODEL', 'gpt-4o-mini')
        url = getattr(settings, 'OPENAI_CHAT_COMPLETIONS_URL', 'https://api.openai.com/v1/chat/completions')
        content = _chat_completions(url, key, model)
    try:
        data = _extract_json_object(content)
    except (json.JSONDecodeError, ValueError) as e:
        raise GrantScoutAgentError(f'Invalid JSON from LLM: {e}') from e
    return normalize_agent_payload(data)
