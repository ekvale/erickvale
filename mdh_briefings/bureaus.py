"""
MDH bureau structure from org chart (May 6, 2026).

Email digest spotlights one bureau per weekday (Mon–Fri); full roster stays on /mdh/.
"""

from __future__ import annotations

from datetime import date

# Monday=0 … Friday=4 → bureau slug
WEEKDAY_SPOTLIGHT_SLUGS = (
    'health_operations',
    'health_equity',
    'health_improvement',
    'health_protection',
    'health_systems',
)

# Always included in email (priorities only, short section)
CORE_DIGEST_LEADER_IDS = (
    'commissioner',
    'deputy_commissioner',
)

BUREAUS = [
    {
        'slug': 'health_operations',
        'name': 'Health Operations Bureau',
        'color': 'gray',
        'ac_leader_id': 'ac_health_operations',
        'assistant_commissioner': 'Mel Gresczyk',
        'ac_title': 'Assistant Commissioner, Chief Operating Officer',
        'divisions': [
            {
                'name': 'Health Regulation Division',
                'director': 'Maria King',
                'assistant_directors': ['Susan Winkelmann', 'Matt Heffron', 'Lindsey Krueger'],
            },
            {
                'name': 'Emergency Preparedness and Response Division',
                'director': 'Cheryl Petersen-Kroeber',
                'assistant_directors': ['Michelle Larson'],
            },
            {
                'name': 'Human Resources Management Division',
                'director': 'Taylor Stiff',
                'assistant_directors': [],
            },
            {
                'name': 'Financial Management Division',
                'director': 'Joshua Bunker (CFO)',
                'assistant_directors': ['Tara Barenok'],
            },
            {
                'name': 'Facilities Management Division',
                'director': 'Kevin Umidon (Facilities Manager)',
                'assistant_directors': [],
            },
            {
                'name': 'Office of Organizational Wellbeing and Employee Experience',
                'director': 'Annie Kiel',
                'assistant_directors': [],
            },
            {
                'name': 'Public Health Strategy and Partnership Division',
                'director': 'Chelsie Huntley',
                'assistant_directors': ['Becky Sechrist'],
            },
        ],
    },
    {
        'slug': 'health_equity',
        'name': 'Health Equity Bureau',
        'color': 'teal',
        'ac_leader_id': 'ac_health_equity_acting',
        'assistant_commissioner': 'Wendy Underwood (Acting)',
        'ac_title': 'Assistant Commissioner (Acting)',
        'divisions': [
            {
                'name': 'Health Equity Strategy and Innovation Division',
                'director': 'Odi Akosionu-DeSouza',
                'assistant_directors': ['Sara Chute'],
            },
            {
                'name': 'Office of American Indian Health and Tribal Relations',
                'director': 'Kris Rhodes',
                'assistant_directors': [],
            },
            {
                'name': 'Office of African American Health',
                'director': 'Aisha Ellis',
                'assistant_directors': [],
            },
            {
                'name': 'Office of Diversity, Inclusion, Belonging, and Equity Strategy',
                'director': 'Shalome Musigñac Jordán',
                'assistant_directors': [],
            },
        ],
    },
    {
        'slug': 'health_improvement',
        'name': 'Health Improvement Bureau',
        'color': 'green',
        'ac_leader_id': 'ac_health_improvement',
        'assistant_commissioner': 'Robsan (Halkeno) Tura',
        'ac_title': 'Assistant Commissioner',
        'divisions': [
            {
                'name': 'Child and Family Health Division',
                'director': 'Noya Woodrich',
                'assistant_directors': ['Meredith O’Brien'],
            },
            {
                'name': 'Health Promotion and Chronic Disease Division',
                'director': 'Khatidja Dawood',
                'assistant_directors': ['Chuck Stroebel'],
            },
            {
                'name': 'Injury Prevention and Mental Health Division',
                'director': 'Catherine Diamond',
                'assistant_directors': ['Autumn Baum'],
            },
            {
                'name': 'Public Health Laboratory',
                'director': 'Sara Vetter',
                'assistant_directors': ['Jill Simonetti'],
            },
        ],
    },
    {
        'slug': 'health_protection',
        'name': 'Health Protection Bureau',
        'color': 'orange',
        'ac_leader_id': 'ac_health_protection',
        'assistant_commissioner': 'Myra Kunas',
        'ac_title': 'Assistant Commissioner',
        'divisions': [
            {
                'name': 'Environmental Health Division',
                'director': 'Tom Hogan',
                'assistant_directors': ['Tom Higgins'],
            },
            {
                'name': 'Infectious Disease Epidemiology, Prevention and Control Division',
                'director': 'Jessica Hancock-Allen',
                'assistant_directors': ['Emily Emerson'],
            },
            {
                'name': 'State Epidemiologist (cross-bureau)',
                'director': 'Dr. Ruth Lynfield',
                'assistant_directors': [],
            },
        ],
    },
    {
        'slug': 'health_systems',
        'name': 'Health Systems Bureau',
        'color': 'purple',
        'ac_leader_id': 'ac_health_systems',
        'assistant_commissioner': 'Carol Backstrom',
        'ac_title': 'Assistant Commissioner',
        'divisions': [
            {
                'name': 'Health Policy Division',
                'director': 'Diane Rydrych',
                'assistant_directors': ['Susan Castellano', 'Karen Soderberg'],
            },
        ],
    },
]


def bureau_by_slug(slug: str) -> dict | None:
    for b in BUREAUS:
        if b['slug'] == slug:
            return b
    return None


def spotlight_bureau_for_date(d: date) -> dict | None:
    """Return bureau dict for weekday Mon–Fri; None on weekends."""
    wd = d.weekday()
    if wd > 4:
        return None
    return bureau_by_slug(WEEKDAY_SPOTLIGHT_SLUGS[wd])


def is_digest_weekday(d: date) -> bool:
    return d.weekday() < 5


def digest_leader_ids_for_date(d: date) -> tuple[list[str], dict | None]:
    """
    Leader IDs to generate for email: core executives + spotlight bureau AC.
    Returns (ids, spotlight_bureau dict or None).
    """
    bureau = spotlight_bureau_for_date(d)
    ids = list(CORE_DIGEST_LEADER_IDS)
    if bureau:
        ac_id = bureau['ac_leader_id']
        if ac_id not in ids:
            ids.append(ac_id)
    return ids, bureau


def format_bureau_org_chart(bureau: dict) -> str:
    """Plain-text division roster for LLM context."""
    lines = [
        f"Bureau: {bureau['name']}",
        f"Assistant Commissioner: {bureau['assistant_commissioner']} ({bureau['ac_title']})",
        'Divisions and directors (org chart May 2026):',
    ]
    for div in bureau['divisions']:
        ads = div.get('assistant_directors') or []
        ad_note = f"; Asst. Directors: {', '.join(ads)}" if ads else ''
        lines.append(f"  - {div['name']}: {div['director']}{ad_note}")
    return '\n'.join(lines)


def all_bureau_ac_leader_ids() -> list[str]:
    return [b['ac_leader_id'] for b in BUREAUS]
