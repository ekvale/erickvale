"""Perplexity API — daily leadership briefing generation."""

from __future__ import annotations

import json
import logging
import re
from datetime import date

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a government leadership simulation assistant.
Generate realistic, specific daily briefings for Minnesota Department of Health leaders.
Always respond with valid JSON only — no markdown, no preamble, no backticks.
Ground every briefing in real MDH context: the $38M PHIG grant termination (Feb 2026),
the $226M COVID-era grant cuts (2025), rural health access gaps, ongoing federal litigation,
and the 2025-2029 Healthy Minnesota Partnership priorities."""


def _perplexity_model() -> str:
    model = (getattr(settings, 'MDH_BRIEFINGS_PERPLEXITY_MODEL', '') or '').strip()
    if model:
        return model
    return getattr(settings, 'GRANTSCOUT_PERPLEXITY_MODEL', 'sonar')


def build_user_prompt(leader: dict, today: date) -> str:
    if leader.get('extended_briefing'):
        return _build_extended_user_prompt(leader, today)
    return _build_standard_user_prompt(leader, today)


def _build_standard_user_prompt(leader: dict, today: date) -> str:
    return f"""
You are {leader['name']}, {leader['title']} at the Minnesota Department of Health.

Background: {leader['context']}

Generate a realistic daily leadership briefing for {today.strftime('%A, %B %d, %Y')}.

Respond ONLY with this JSON structure:
{{
  "schedule": ["9:00am: ...", "10:30am: ...", "1:00pm: ...", "3:30pm: ..."],
  "core_beliefs": "2-3 sentences on your driving philosophy and values.",
  "vision": "1-2 sentences on what success looks like for MDH in 3 years.",
  "top_priorities": [
    "Specific priority #1 for today",
    "Specific priority #2 for today",
    "Specific priority #3 for today"
  ]
}}
"""


def _build_extended_user_prompt(leader: dict, today: date) -> str:
    return f"""
You are {leader['name']}, {leader['title']} at the Minnesota Department of Health.

Background: {leader['context']}

Generate a realistic daily leadership briefing for {today.strftime('%A, %B %d, %Y')}.
Use current, plausible public health informatics and Minnesota policy context where helpful.

Respond ONLY with this JSON structure:
{{
  "schedule": ["9:00am: ...", "10:30am: ...", "1:00pm: ...", "3:30pm: ..."],
  "core_beliefs": "2-3 sentences on your driving philosophy and values.",
  "vision": "1-2 sentences on what success looks like for MDH data strategy in 3 years.",
  "top_priorities": [
    "Specific priority #1 for today",
    "Specific priority #2 for today",
    "Specific priority #3 for today"
  ],
  "relevant_news": [
    {{
      "headline": "Short headline on data/interop/funding/policy",
      "summary": "1-2 sentences and why it matters to this role."
    }}
  ],
  "high_value_projects": [
    {{
      "title": "Concrete project name",
      "impact": "Why this is among the highest-value deliverables for MDH (outcomes, risk reduction, equity).",
      "next_step": "Specific next action this week."
    }}
  ]
}}

Include 4-6 relevant_news items (FHIR/interoperability, federal data policy, MN public health IT,
funding cuts, outbreak data, AI governance) and 4-6 high_value_projects ranked by strategic value.
"""


def _extract_json_object(text: str) -> dict:
    text = text.strip()
    if text.startswith('```'):
        parts = text.split('```')
        if len(parts) >= 2:
            inner = parts[1]
            if inner.lstrip().startswith('json'):
                inner = inner.lstrip()[4:].lstrip()
            text = inner.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r'\{[\s\S]*\}', text)
        if match:
            return json.loads(match.group(0))
        raise


def generate_briefing(leader: dict, today: date) -> dict:
    """Call Perplexity chat completions and return parsed briefing dict."""
    max_tokens = 2200 if leader.get('extended_briefing') else 1200
    raw = _perplexity_chat(
        SYSTEM_PROMPT,
        build_user_prompt(leader, today),
        max_tokens=max_tokens,
    )
    return _extract_json_object(raw)


NEWS_SYSTEM_PROMPT = """You are a public health news analyst focused on Minnesota and MDH.
Use current web information when available. Respond with valid JSON only — no markdown fences."""


def build_news_prompt(today: date) -> str:
    return f"""
Today is {today.strftime('%A, %B %d, %Y')}.

List the 5–8 most relevant news items from roughly the last 48 hours for Minnesota Department
of Health leadership. Prioritize: federal funding and PHIG/CDC grant changes, Minnesota legislative
or policy actions affecting public health, infectious disease and outbreak news in MN or the
region, health equity and rural access, litigation or federal actions affecting state health
authority, and major MDH program announcements.

Respond ONLY with this JSON:
{{
  "items": [
    {{
      "headline": "Short headline",
      "summary": "1–2 sentences on what happened.",
      "why_it_matters": "One sentence on relevance to MDH leaders."
    }}
  ]
}}
"""


def _perplexity_chat(system: str, user: str, *, max_tokens: int = 2000) -> str:
    key = (getattr(settings, 'PERPLEXITY_API_KEY', '') or '').strip()
    if not key:
        raise RuntimeError('PERPLEXITY_API_KEY is not set')

    url = getattr(
        settings,
        'PERPLEXITY_API_URL',
        'https://api.perplexity.ai/chat/completions',
    )
    model = _perplexity_model()
    resp = requests.post(
        url,
        headers={
            'Authorization': f'Bearer {key}',
            'Content-Type': 'application/json',
        },
        json={
            'model': model,
            'temperature': 0.3,
            'max_tokens': max_tokens,
            'messages': [
                {'role': 'system', 'content': system},
                {'role': 'user', 'content': user},
            ],
        },
        timeout=180,
    )
    if resp.status_code >= 400:
        logger.warning(
            'mdh_briefings Perplexity HTTP %s: %s',
            resp.status_code,
            resp.text[:500],
        )
        resp.raise_for_status()

    body = resp.json()
    choices = body.get('choices') or []
    if not choices:
        raise RuntimeError('Perplexity response missing choices')
    content = (choices[0].get('message') or {}).get('content')
    if not content:
        raise RuntimeError('Perplexity response missing content')
    return str(content)


def fetch_daily_news_digest(today: date) -> list[dict]:
    """Perplexity (sonar) web-grounded MDH news headlines for the digest email."""
    raw = _perplexity_chat(
        NEWS_SYSTEM_PROMPT,
        build_news_prompt(today),
        max_tokens=2500,
    )
    data = _extract_json_object(raw)
    items = data.get('items') if isinstance(data, dict) else None
    if not isinstance(items, list):
        raise RuntimeError('News digest JSON missing "items" list')
    out: list[dict] = []
    for row in items[:10]:
        if not isinstance(row, dict):
            continue
        headline = (row.get('headline') or '').strip()
        if not headline:
            continue
        out.append(
            {
                'headline': headline,
                'summary': (row.get('summary') or '').strip(),
                'why_it_matters': (row.get('why_it_matters') or '').strip(),
            }
        )
    return out
