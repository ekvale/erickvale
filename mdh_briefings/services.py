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
            'temperature': 0.4,
            'max_tokens': 1200,
            'messages': [
                {'role': 'system', 'content': SYSTEM_PROMPT},
                {'role': 'user', 'content': build_user_prompt(leader, today)},
            ],
        },
        timeout=120,
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
    return _extract_json_object(str(content))
