"""Persist API briefing payloads to LeaderBriefing."""

from __future__ import annotations

from datetime import date

from .models import LeaderBriefing


def _normalize_news(raw) -> list[dict]:
    if not isinstance(raw, list):
        return []
    out: list[dict] = []
    for row in raw[:8]:
        if isinstance(row, str) and row.strip():
            out.append({'headline': row.strip(), 'summary': ''})
            continue
        if not isinstance(row, dict):
            continue
        headline = (row.get('headline') or row.get('title') or '').strip()
        if not headline:
            continue
        out.append(
            {
                'headline': headline,
                'summary': (row.get('summary') or '').strip(),
            }
        )
    return out


def _normalize_projects(raw) -> list[dict]:
    if not isinstance(raw, list):
        return []
    out: list[dict] = []
    for row in raw[:8]:
        if isinstance(row, str) and row.strip():
            out.append({'title': row.strip(), 'impact': '', 'next_step': ''})
            continue
        if not isinstance(row, dict):
            continue
        title = (row.get('title') or row.get('name') or '').strip()
        if not title:
            continue
        out.append(
            {
                'title': title,
                'impact': (row.get('impact') or row.get('value') or '').strip(),
                'next_step': (row.get('next_step') or row.get('status_or_next_step') or '').strip(),
            }
        )
    return out


def save_briefing(leader: dict, today: date, data: dict) -> LeaderBriefing:
    return LeaderBriefing.objects.update_or_create(
        leader_id=leader['id'],
        date=today,
        defaults={
            'name': leader['name'],
            'title': leader['title'],
            'bureau': leader['bureau'],
            'schedule': data.get('schedule') or [],
            'core_beliefs': data.get('core_beliefs') or '',
            'vision': data.get('vision') or '',
            'top_priorities': data.get('top_priorities') or [],
            'relevant_news': _normalize_news(data.get('relevant_news')),
            'high_value_projects': _normalize_projects(data.get('high_value_projects')),
        },
    )[0]


def briefing_to_card_context(briefing: LeaderBriefing) -> dict:
    return {
        'leader_id': briefing.leader_id,
        'error': None,
        'schedule': briefing.schedule,
        'core_beliefs': briefing.core_beliefs,
        'vision': briefing.vision,
        'top_priorities': briefing.top_priorities,
        'relevant_news': briefing.relevant_news or [],
        'high_value_projects': briefing.high_value_projects or [],
        'cached': True,
    }
