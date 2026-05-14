"""
Seed contacts, conference-style events, and funding-pipeline tasks for the practice.

Idempotent: skips contacts matching (first_name, last_name, organization);
           skips events matching (title, start_datetime);
           reuses project "Funding Pipeline" if present; skips existing tasks by title.

Run:
  python manage.py seed_network_data --user <cto_username_or_email> [--cspo <cspo_username_or_email>]

--user resolves the CTO (same as seed_initial_tasks) and is used for added_by (contacts),
created_by (events), and ownership of the Funding Pipeline project. --cspo assigns funding
tasks when provided; otherwise assignees default to the CTO user.
"""

from __future__ import annotations

import logging
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q
from django.utils import timezone

from projects.models import (
    Contact,
    ContactType,
    Event,
    EventType,
    MembershipRole,
    Priority,
    Project,
    ProjectMembership,
    ProjectStatus,
    Task,
    TaskStatus,
)

logger = logging.getLogger(__name__)

User = get_user_model()

# --- Exact project titles (must match seed_initial_tasks.py) ---
P4 = "Business Development and Market Entry"
P5 = "Grant Applications"
P6 = "Nonprofit Transition Planning"
P7 = "OMOP and Technical Skill Development"
FUNDING_PROJECT_NAME = "Funding Pipeline"


def _resolve_user(identifier: str, *, label: str) -> User:
    identifier = (identifier or "").strip()
    if not identifier:
        raise CommandError(f"{label}: empty username or email.")
    user = User.objects.filter(
        Q(username__iexact=identifier) | Q(email__iexact=identifier)
    ).first()
    if user is None:
        raise CommandError(
            f'{label}: no user found matching username or email "{identifier}". '
            "Nothing was created."
        )
    return user


def _require_project(name: str) -> Project:
    project = Project.objects.filter(name=name).first()
    if project is None:
        raise CommandError(
            f'Required project "{name}" not found. Run seed_initial_tasks first '
            "so practice projects exist."
        )
    return project


def _event_start_all_day(d: date) -> datetime:
    return timezone.make_aware(datetime.combine(d, time.min))


def _event_start_weekly_call_et() -> datetime:
    """OHDSI weekly call: 2026-05-20 11:00 America/New_York."""
    et = ZoneInfo("America/New_York")
    naive = datetime(2026, 5, 20, 11, 0, 0)
    return naive.replace(tzinfo=et)


def _contact_definitions():
    """All Step 1 contacts: keys match Contact model; email only where known."""
    return [
        {
            "first_name": "Tyler",
            "last_name": "Winkelman",
            "organization": "Hennepin Healthcare Research Institute",
            "title": "Co-Director, Health Homelessness and Criminal Justice Lab; MNEHRC Co-Founder",
            "email": "tyler.winkelman@hcmed.org",
            "phone": "",
            "contact_type": ContactType.RESEARCH,
            "notes": (
                "Co-founder and inaugural president of MNEHRC. Division Director of General "
                "Internal Medicine at Hennepin Healthcare. Leads the Health, Homelessness, and "
                "Criminal Justice Lab. Primary architect of HTAC and the federated OMOP "
                "implementation. Most important relationship in this ecosystem."
            ),
        },
        {
            "first_name": "Katherine",
            "last_name": "Diaz Vickery",
            "organization": "Hennepin Healthcare Research Institute",
            "title": "Co-Director, Health Homelessness and Criminal Justice Lab",
            "email": "",
            "phone": "",
            "contact_type": ContactType.RESEARCH,
            "notes": (
                "Co-Director of the HHCJ Lab alongside Winkelman. Co-first author on the COVID "
                "vaccination paper and MNEHRC research. Key collaborator on homelessness and "
                "incarceration health data work."
            ),
        },
        {
            "first_name": "Peter",
            "last_name": "Bodurtha",
            "organization": "Hennepin Healthcare Research Institute",
            "title": "Research Analyst, MNEHRC",
            "email": "",
            "phone": "",
            "contact_type": ContactType.RESEARCH,
            "notes": (
                "Core MNEHRC analyst. Co-author on multiple MNEHRC publications including HTAC "
                "and COVID vaccination studies. Day-to-day technical and analytical work for the "
                "consortium. Key contact for implementation-level conversations."
            ),
        },
        {
            "first_name": "Renee",
            "last_name": "Van Siclen",
            "organization": "Hennepin Healthcare Research Institute",
            "title": "Research Analyst, MNEHRC",
            "email": "",
            "phone": "",
            "contact_type": ContactType.RESEARCH,
            "notes": (
                "Statistical analyst for MNEHRC. Co-author on the health condition prevalence "
                "paper. Handles direct standardization and prevalence estimation methods."
            ),
        },
        {
            "first_name": "Steven",
            "last_name": "Johnson",
            "organization": "University of Minnesota — Institute for Health Informatics",
            "title": "Research Scientist",
            "email": "",
            "phone": "",
            "contact_type": ContactType.RESEARCH,
            "notes": (
                "Lead author on the 2026 Learning Health Systems paper describing the MNEHRC "
                "architecture. Deep expertise in OMOP CDM implementation, data quality, and "
                "federated network infrastructure. Key technical contact at U of M side of the "
                "consortium."
            ),
        },
        {
            "first_name": "Paul",
            "last_name": "Drawz",
            "organization": "University of Minnesota — Division of Nephrology and Hypertension",
            "title": "Associate Professor",
            "email": "",
            "phone": "",
            "contact_type": ContactType.RESEARCH,
            "notes": (
                "MNEHRC co-investigator. Corresponding author on the COVID vaccine effectiveness "
                "paper. Strong relationship with MDH. Data infrastructure and clinical research "
                "focus."
            ),
        },
        {
            "first_name": "Alanna",
            "last_name": "Chamberlain",
            "organization": "Mayo Clinic — Department of Quantitative Health Sciences",
            "title": "Associate Professor",
            "email": "",
            "phone": "",
            "contact_type": ContactType.RESEARCH,
            "notes": (
                "MNEHRC co-investigator representing Mayo Clinic. Co-author on multiple MNEHRC "
                "publications. Key contact for the Mayo Clinic node of the consortium."
            ),
        },
        {
            "first_name": "Karen",
            "last_name": "Margolis",
            "organization": "HealthPartners Institute",
            "title": "Senior Investigator",
            "email": "",
            "phone": "",
            "contact_type": ContactType.RESEARCH,
            "notes": (
                "MNEHRC co-investigator representing HealthPartners. Co-author on HTAC and COVID "
                "studies. HealthPartners Institute is a major research arm of one of the 11 "
                "consortium health systems."
            ),
        },
        {
            "first_name": "Rebecca",
            "last_name": "Rossom",
            "organization": "HealthPartners Institute",
            "title": "Senior Investigator",
            "email": "",
            "phone": "",
            "contact_type": ContactType.RESEARCH,
            "notes": (
                "MNEHRC co-investigator. Co-author on health condition prevalence paper. Mental "
                "health and primary care research focus."
            ),
        },
        {
            "first_name": "Stephen",
            "last_name": "Waring",
            "organization": "Essentia Institute of Rural Health",
            "title": "Director of Research",
            "email": "",
            "phone": "",
            "contact_type": ContactType.RESEARCH,
            "notes": (
                "MNEHRC co-investigator representing Essentia Health, the primary rural health "
                "system in the consortium. Key contact for rural data representation and Essentia "
                "node."
            ),
        },
        {
            "first_name": "Miriam",
            "last_name": "Halstead Muscoplat",
            "organization": "Minnesota Department of Health",
            "title": "Epidemiologist",
            "email": "",
            "phone": "",
            "contact_type": ContactType.GOVERNMENT,
            "notes": (
                "MDH collaborator acknowledged in the MNEHRC architecture paper. Key "
                "government-side contact for the consortium's MDH partnership. Involved in "
                "immunization data linkage and surveillance work."
            ),
        },
        {
            "first_name": "Karen",
            "last_name": "Soderberg",
            "organization": "Minnesota Department of Health",
            "title": "Epidemiologist",
            "email": "",
            "phone": "",
            "contact_type": ContactType.GOVERNMENT,
            "notes": (
                "MDH collaborator acknowledged in the MNEHRC architecture paper. Key "
                "government-side technical contact alongside Halstead Muscoplat."
            ),
        },
        {
            "first_name": "Samuel",
            "last_name": "Patnoe",
            "organization": "HealthPartners Institute",
            "title": "Research Analyst",
            "email": "",
            "phone": "",
            "contact_type": ContactType.RESEARCH,
            "notes": (
                "Co-author on the 2026 MNEHRC architecture paper. Presented HTAC at OHDSI "
                "Community Call in November 2024. Active OHDSI community participant. Good "
                "contact for OHDSI engagement."
            ),
        },
        {
            "first_name": "Alicia",
            "last_name": "Waters",
            "organization": (
                "Minnesota Department of Health — Public Health Strategy and Partnership Division"
            ),
            "title": "Grants and Budget Administrator, CDC PHIG",
            "email": "alicia.waters@state.mn.us",
            "phone": "",
            "contact_type": ContactType.GOVERNMENT,
            "notes": (
                "Primary MDH contact for the CDC Public Health Infrastructure Grant (PHIG) which "
                "distributes $42.9M to Minnesota community health boards. This is the gateway for "
                "any consulting work supporting PHIG-funded county health departments on data "
                "modernization."
            ),
        },
        {
            "first_name": "(Contact Name)",
            "last_name": "—",
            "organization": "Minnesota Department of Health — Center for Community Health",
            "title": "Director",
            "email": "",
            "phone": "",
            "contact_type": ContactType.GOVERNMENT,
            "notes": (
                "The Center for Community Health is a co-lead partner on HTAC alongside MNEHRC "
                "and Hennepin County. Identify the current director and establish a relationship. "
                "Key for state-level public health collaboration opportunities."
            ),
        },
        {
            "first_name": "David",
            "last_name": "Johnson",
            "organization": "Hennepin County Public Health",
            "title": "Public Health Data and Epidemiology Lead",
            "email": "",
            "phone": "",
            "contact_type": ContactType.PUBLIC_HEALTH,
            "notes": (
                "Quoted extensively in Healthcare Innovation article about HTAC. Described as "
                "leading the private/public health informatics collaborative that preceded HTAC. "
                "Key Hennepin County contact for HTAC use and CHNA data work. Hennepin County "
                "completed its 2025 Community Health Assessment using HTAC data."
            ),
        },
        {
            "first_name": "(Contact Name)",
            "last_name": "—",
            "organization": "MN Community Measurement (MNCM)",
            "title": "MNEHRC Liaison",
            "email": "support@mncm.org",
            "phone": "",
            "contact_type": ContactType.RESEARCH,
            "notes": (
                "MNCM is a core MNEHRC partner facilitating rural provider participation. Contact "
                "listed on MNCM blog for CHIRP and MNEHRC participation inquiries. Potential "
                "partner for rural FQHC and small clinic outreach, which is a documented gap in "
                "MNEHRC coverage."
            ),
        },
        {
            "first_name": "(Contact Name)",
            "last_name": "(Contact Name)",
            "organization": "Ramsey County Public Health",
            "title": "(Public Health Director)",
            "email": "",
            "phone": "",
            "contact_type": ContactType.PUBLIC_HEALTH,
            "notes": (
                "Second-largest metro county. Ramsey County (St. Paul) public health conducts "
                "CHNAs on a 5-year cycle. HTAC dashboard directly applicable to their assessment "
                "work. High-priority outreach target for CHNA data support services."
            ),
        },
        {
            "first_name": "(Contact Name)",
            "last_name": "(Contact Name)",
            "organization": "Anoka County Community Health and Environmental Services",
            "title": "(Public Health Director)",
            "email": "",
            "phone": "",
            "contact_type": ContactType.PUBLIC_HEALTH,
            "notes": (
                "Large north metro county. Community health board receiving CDC PHIG funding "
                "through MDH distribution. Data modernization is an eligible PHIG activity — "
                "potential pathway for consulting engagement."
            ),
        },
        {
            "first_name": "(Contact Name)",
            "last_name": "(Contact Name)",
            "organization": "Dakota County Public Health",
            "title": "(Public Health Director)",
            "email": "",
            "phone": "",
            "contact_type": ContactType.PUBLIC_HEALTH,
            "notes": (
                "Large south metro county. Community health board receiving CDC PHIG funding. "
                "Active CHNA cycle. Strong candidate for HTAC-based CHNA data support engagement."
            ),
        },
        {
            "first_name": "(Contact Name)",
            "last_name": "(Contact Name)",
            "organization": "Washington County Public Health",
            "title": "(Public Health Director)",
            "email": "",
            "phone": "",
            "contact_type": ContactType.PUBLIC_HEALTH,
            "notes": (
                "East metro county. Community health board receiving CDC PHIG funding. CHNA data "
                "support candidate."
            ),
        },
        {
            "first_name": "(Contact Name)",
            "last_name": "(Contact Name)",
            "organization": "St. Louis County Public Health",
            "title": "(Public Health Director)",
            "email": "",
            "phone": "",
            "contact_type": ContactType.PUBLIC_HEALTH,
            "notes": (
                "Largest county by area in Minnesota. Duluth-based. Essentia Health (MNEHRC "
                "member) is the dominant health system here — warm introduction possible through "
                "Stephen Waring."
            ),
        },
        {
            "first_name": "(Contact Name)",
            "last_name": "(Contact Name)",
            "organization": "Olmsted County Public Health",
            "title": "(Public Health Director)",
            "email": "",
            "phone": "",
            "contact_type": ContactType.PUBLIC_HEALTH,
            "notes": (
                "Rochester area. Mayo Clinic (MNEHRC member) is dominant health system — warm "
                "introduction possible through Alanna Chamberlain. Strong candidate for CHNA data "
                "support."
            ),
        },
        {
            "first_name": "(Contact Name)",
            "last_name": "(Contact Name)",
            "organization": "Wilder Research",
            "title": "(Director of Research)",
            "email": "",
            "phone": "",
            "contact_type": ContactType.RESEARCH,
            "notes": (
                "Research arm of Amherst H. Wilder Foundation. Conducts the statewide homelessness "
                "survey (Minnesota Homeless Study) every three years. Key data partner for "
                "homelessness prevalence work. Potential collaborator on HMIS-linked research."
            ),
        },
        {
            "first_name": "(Contact Name)",
            "last_name": "(Contact Name)",
            "organization": "Simpson Housing Services",
            "title": "(Executive Director)",
            "email": "",
            "phone": "",
            "contact_type": ContactType.COMMUNITY,
            "notes": (
                "Major Twin Cities homeless services provider. Uses HMIS data. Potential client for "
                "population health data support and grant technical assistance."
            ),
        },
        {
            "first_name": "(Contact Name)",
            "last_name": "(Contact Name)",
            "organization": (
                "Minnesota Alliance of Health Advocates (MAHA) / Advocates for Human Rights"
            ),
            "title": "(Director)",
            "email": "",
            "phone": "",
            "contact_type": ContactType.COMMUNITY,
            "notes": (
                "Community advocacy organizations intersecting with justice-involved and homeless "
                "populations. Potential collaborators for community data projects and grant "
                "applications targeting these populations."
            ),
        },
        {
            "first_name": "(Contact Name)",
            "last_name": "(Contact Name)",
            "organization": "Council on Crime and Justice",
            "title": "(Research Director)",
            "email": "",
            "phone": "",
            "contact_type": ContactType.COMMUNITY,
            "notes": (
                "Minnesota-based criminal justice reform organization. Intersection with health "
                "data for justice-involved populations. Potential collaborator on 1115 Reentry "
                "Waiver evaluation work."
            ),
        },
        {
            "first_name": "(Contact Name)",
            "last_name": "(Contact Name)",
            "organization": "PCORnet — National Patient-Centered Clinical Research Network",
            "title": "(Network Coordinating Center)",
            "email": "",
            "phone": "",
            "contact_type": ContactType.RESEARCH,
            "notes": (
                "National federated research network. MNEHRC adapted PPRL methods from PCORnet. "
                "Membership and participation in PCORnet workgroups is a credentialing "
                "opportunity and potential source of subcontract work."
            ),
        },
        {
            "first_name": "(Contact Name)",
            "last_name": "(Contact Name)",
            "organization": "National Network of Public Health Institutes (NNPHI)",
            "title": "(DMI Program Contact)",
            "email": "DMI@nnphi.org",
            "phone": "",
            "contact_type": ContactType.RESEARCH,
            "notes": (
                "PHIG Component B national partner. Issued an RFP for Data Modernization Initiative "
                "technical assistance providers in early 2025 (up to $20k per domain area). "
                "Monitor for future TA provider opportunities — this is a direct path to paid work "
                "supporting PHIG-funded health departments."
            ),
        },
        {
            "first_name": "(Contact Name)",
            "last_name": "(Contact Name)",
            "organization": "Robert Wood Johnson Foundation",
            "title": "(Program Officer — Health Data)",
            "email": "",
            "phone": "",
            "contact_type": ContactType.FUNDER,
            "notes": (
                "Major national funder of health equity and data infrastructure. Tyler Winkelman "
                "completed a RWJF Clinical Scholars fellowship — warm network connection exists. "
                "Relevant for nonprofit transition phase. Monitor for data equity and public health "
                "infrastructure program areas."
            ),
        },
        {
            "first_name": "(Contact Name)",
            "last_name": "(Contact Name)",
            "organization": "Blue Cross and Blue Shield of Minnesota Foundation",
            "title": "(Grants Program)",
            "email": "",
            "phone": "",
            "contact_type": ContactType.FUNDER,
            "notes": (
                "Minnesota-based foundation. 2023-2026 funding cycle focuses on building healthy "
                "generations and health equity. Monitor for health data and equity-focused grant "
                "opportunities aligned with CHNA and population health work."
            ),
        },
        {
            "first_name": "(Contact Name)",
            "last_name": "(Contact Name)",
            "organization": "Otto Bremer Trust",
            "title": "(Program Officer — Health)",
            "email": "",
            "phone": "",
            "contact_type": ContactType.FUNDER,
            "notes": (
                "St. Paul-based trust. Funds health and community well-being in Minnesota, North "
                "Dakota, and Wisconsin. Health equity focus. Relevant for nonprofit launch "
                "phase. Accepts letters of inquiry year-round."
            ),
        },
        {
            "first_name": "(Contact Name)",
            "last_name": "(Contact Name)",
            "organization": "McKnight Foundation",
            "title": "(Program Officer — Health)",
            "email": "",
            "phone": "",
            "contact_type": ContactType.FUNDER,
            "notes": (
                "Minneapolis-based foundation. Health program focuses on health equity and "
                "systems change. Relevant for nonprofit transition. Competitive but well-aligned "
                "with mission."
            ),
        },
        {
            "first_name": "(Contact Name)",
            "last_name": "(Contact Name)",
            "organization": "Bush Foundation",
            "title": "(Program Officer)",
            "email": "",
            "phone": "",
            "contact_type": ContactType.FUNDER,
            "notes": (
                "St. Paul-based foundation. Funds community-centered leadership and innovation "
                "across Minnesota, North Dakota, and South Dakota. Health equity and data work "
                "eligible. Relevant for nonprofit phase."
            ),
        },
        {
            "first_name": "(Contact Name)",
            "last_name": "(Contact Name)",
            "organization": "Common Health Coalition",
            "title": "(Partnership Contact)",
            "email": "",
            "phone": "",
            "contact_type": ContactType.RESEARCH,
            "notes": (
                "MNEHRC joined the Common Health Coalition in October 2024. The Coalition published "
                "a case study about MNEHRC. Membership or affiliation with Common Health Coalition "
                "would provide national visibility and partnership opportunities. Research the "
                "Coalition's membership structure."
            ),
        },
    ]


def _event_definitions(project_bd):
    """Step 2: conferences default-linked to Business Development project."""
    p4 = project_bd
    return [
        {
            "title": "OHDSI Global Symposium 2026",
            "description": "",
            "notes": (
                "12th annual OHDSI Global Symposium. Hyatt Regency, New Brunswick, NJ. Oct 20-22. "
                "Primary OMOP/OHDSI community conference. Collaborator Showcase submission deadline "
                "is June 5, 2026. Registration is open. Highest priority conference for technical "
                "credibility and community building. Submit a demo or poster showcasing the HTAC "
                "implementation."
            ),
            "event_type": EventType.MEETING,
            "project": p4,
            "start_datetime": _event_start_all_day(date(2026, 10, 20)),
            "end_datetime": None,
            "all_day": True,
        },
        {
            "title": "OHDSI Collaborator Showcase Submission Deadline",
            "description": "",
            "notes": (
                "Deadline to submit brief reports for the 2026 OHDSI Global Symposium Collaborator "
                "Showcase. Submit the erickvale.com HTAC demo as a showcase entry. Submission deadline "
                "8pm ET."
            ),
            "event_type": EventType.MILESTONE,
            "project": p4,
            "start_datetime": _event_start_all_day(date(2026, 6, 5)),
            "end_datetime": None,
            "all_day": True,
        },
        {
            "title": "OHDSI Summer School 2026",
            "description": "",
            "notes": (
                "Columbia University Department of Biomedical Informatics. June 22-26, 2026. "
                "Immersive hands-on training in OMOP CDM, real-world evidence, and OHDSI tools. "
                "Highly recommended for building OMOP expertise. Registration is open."
            ),
            "event_type": EventType.MEETING,
            "project": p4,
            "start_datetime": _event_start_all_day(date(2026, 6, 22)),
            "end_datetime": None,
            "all_day": True,
        },
        {
            "title": "OHDSI Europe Symposium 2026",
            "description": "",
            "notes": (
                "Rotterdam, Netherlands. April 18-20. Main conference April 20 on SS Rotterdam. "
                "Workshops April 18-19 at Erasmus University Medical Center. Monitor for remote "
                "participation options if travel is not feasible."
            ),
            "event_type": EventType.MEETING,
            "project": p4,
            "start_datetime": _event_start_all_day(date(2026, 4, 18)),
            "end_datetime": None,
            "all_day": True,
        },
        {
            "title": "OHDSI Weekly Community Call — Ongoing",
            "description": "",
            "notes": (
                "Every Tuesday 11am ET. Free and open to all. Primary ongoing touchpoint with the "
                "OHDSI community. Join immediately and participate regularly. Introduce the HTAC "
                "demo in an appropriate session. URL: ohdsi.org/community-calls-2026"
            ),
            "event_type": EventType.MEETING,
            "project": p4,
            "start_datetime": _event_start_weekly_call_et(),
            "end_datetime": _event_start_weekly_call_et() + timedelta(hours=1),
            "all_day": False,
        },
        {
            "title": "NACCHO360 Annual Conference 2026",
            "description": "",
            "notes": (
                "NACCHO's annual conference for local health department staff and partners. Exact "
                "dates TBD — monitor naccho.org/conferences. Primary conference for reaching local "
                "public health directors and county health department clients. The PHI*con public "
                "health informatics track runs alongside it."
            ),
            "event_type": EventType.MEETING,
            "project": p4,
            "start_datetime": _event_start_all_day(date(2026, 7, 1)),
            "end_datetime": None,
            "all_day": True,
        },
        {
            "title": "PHI*con 2026 — Public Health Informatics Conference",
            "description": "",
            "notes": (
                "Louisville, KY. July 13-14, 2026 (also virtual). Hosted by NACCHO. Theme: "
                "Transforming Public Health Through Health IT and Data Modernization. Directly "
                "aligned with HTAC/OMOP data modernization work. Early-bird registration extended "
                "to April 17, 2026. High priority — present or exhibit."
            ),
            "event_type": EventType.MEETING,
            "project": p4,
            "start_datetime": _event_start_all_day(date(2026, 7, 13)),
            "end_datetime": None,
            "all_day": True,
        },
        {
            "title": "APHA Annual Meeting 2026",
            "description": "",
            "notes": (
                "San Antonio, TX. November 1-4, 2026. Largest US public health conference (~11,000 "
                "attendees). Abstract submission typically opens in winter. Good for visibility with "
                "academic public health and policy audiences. Lower priority than OHDSI and NACCHO "
                "for direct client development but important for field presence."
            ),
            "event_type": EventType.MEETING,
            "project": p4,
            "start_datetime": _event_start_all_day(date(2026, 11, 1)),
            "end_datetime": None,
            "all_day": True,
        },
        {
            "title": "Minnesota Public Health Association Annual Conference",
            "description": "",
            "notes": (
                "Annual conference of MPHA, the Minnesota state affiliate of APHA. Exact dates TBD "
                "— monitor mpha.net. Primary in-state conference for reaching Minnesota county and "
                "local public health professionals. Highest priority Minnesota-specific conference "
                "for client development. Abstract submission typically spring."
            ),
            "event_type": EventType.MEETING,
            "project": p4,
            "start_datetime": _event_start_all_day(date(2026, 10, 1)),
            "end_datetime": None,
            "all_day": True,
        },
        {
            "title": "Rural MN Health Forum — Annual",
            "description": "",
            "notes": (
                "Annual rural health forum. MNCM presented MNEHRC/HTAC at the 2025 forum in "
                "Alexandria, MN. Good venue for rural county public health outreach. Monitor "
                "Medi-Sota and MN Rural Health Cooperative for 2026/2027 dates."
            ),
            "event_type": EventType.MEETING,
            "project": p4,
            "start_datetime": _event_start_all_day(date(2027, 1, 1)),
            "end_datetime": None,
            "all_day": True,
        },
        {
            "title": "PHIG Annual Recipient Convening",
            "description": "",
            "notes": (
                "CDC convenes PHIG-funded health departments annually. 2025 convening was August "
                "in St. Louis (900+ attendees). 2026 dates TBD. Not directly open to consultants "
                "but monitor for subcontractor networking opportunities. NNPHI and ASTHO "
                "(Component B partners) attend and are accessible."
            ),
            "event_type": EventType.MEETING,
            "project": p4,
            "start_datetime": _event_start_all_day(date(2026, 8, 1)),
            "end_datetime": None,
            "all_day": True,
        },
    ]


def _funding_task_definitions():
    """Parent title, due offset days, description, subtask titles."""
    return [
        (
            "CDC Public Health Infrastructure Grant (PHIG) — Subcontract Pathway",
            60,
            (
                "PHIG is a 5-year grant (Dec 2022–Nov 2027) awarding $42.9M to Minnesota. Funds flow "
                "from MDH to 87 community health boards for workforce, foundational capabilities, and "
                "data modernization. LLCs and for-profits are NOT direct PHIG recipients — the "
                "pathway is as a subcontractor to a funded health department. MDH contact: Alicia "
                "Waters (alicia.waters@state.mn.us). Strategy: identify county health boards using "
                "PHIG for data modernization and offer technical assistance services as a "
                "subcontractor."
            ),
            [
                "Download and read the full CDC PHIG NOFO from grants.gov (search OE22-2203)",
                "Contact Alicia Waters at MDH to understand which MN community health boards are "
                "using PHIG funds for data modernization",
                "Identify 3-5 county health boards to approach about data modernization technical assistance",
                "Draft a one-page capability brief specific to PHIG data modernization activities",
            ],
        ),
        (
            "NNPHI Data Modernization Initiative TA Provider — Monitor for Next Cycle",
            90,
            (
                "NNPHI (PHIG Component B national partner) issued an RFP in early 2025 for DMI "
                "technical assistance providers at up to $20,000 per domain area with potential "
                "extension through November 2027. LLCs and individuals are eligible. Contact: "
                "DMI@nnphi.org. Monitor for a second cycle of this RFP as PHIG period of performance "
                "continues through 2027."
            ),
            [
                "Email DMI@nnphi.org to introduce the practice and ask about future TA provider opportunities",
                "Monitor nnphi.org for new RFPs related to data modernization technical assistance",
                "Review the original 2025 RFP domain areas to assess alignment with current capabilities",
            ],
        ),
        (
            "Minnesota Public Health Infrastructure Fund — Monitor for New Cohorts",
            45,
            (
                "MDH state-funded program supporting local innovation projects among community "
                "health boards. Multiple active projects (2022-2026, 2024-2026, 2025-2027 cohorts) "
                "include population health data sharing and rural data infrastructure projects. "
                "While grants go directly to community health boards, consulting services can be "
                "embedded in board applications. Monitor for new cohort announcements."
            ),
            [
                "Bookmark and subscribe to health.state.mn.us/communities/practice/systemtransformation/infrastructurefund.html",
                "Identify which active cohort projects involve data infrastructure or HTAC — these boards are warm leads",
                "Research the Aitkin-Itasca-Koochiching cohort (2025-2027) exploring rural population health data — contact their fiscal host",
            ],
        ),
        (
            "NIH R01/R21 — Health Services Research, Homelessness and Incarceration",
            120,
            (
                "NIH funds observational health services research through multiple mechanisms. R21 "
                "(exploratory) and R01 (standard research) are relevant for EHR-linked studies of "
                "homeless and justice-involved populations. Eligibility as LLC subcontractor to "
                "academic PI (e.g., U of M, Hennepin Healthcare Research Institute). This is a "
                "longer-term opportunity requiring academic partnership. NIAID, NIDA, NIMH, and "
                "NHLBI are relevant institutes."
            ),
            [
                "Identify current NIH-funded grants involving MNEHRC researchers (search NIH Reporter for Winkelman, Drawz, Johnson)",
                "Reach out to HHRI or U of M researchers about serving as a technical subcontractor on future submissions",
                "Review PA-25-XXX mechanisms for health services research relevant to homelessness and incarceration",
                "Identify upcoming NIDA and NIMH program announcements related to EHR-based population health research",
            ],
        ),
        (
            "HRSA Health Center Program — Data Infrastructure Technical Assistance",
            90,
            (
                "HRSA funds Federally Qualified Health Centers (FQHCs) through the Health Center "
                "Program. FQHCs are a documented gap in MNEHRC coverage. Several MN FQHCs may be "
                "seeking data infrastructure support. This is primarily a direct client pathway "
                "rather than a direct grant — FQHCs receive HRSA funding and can contract for "
                "technical services. Identify MN FQHCs not currently in MNEHRC and approach them."
            ),
            [
                "Download HRSA's list of Minnesota-funded FQHCs from findahealthcenter.hrsa.gov",
                "Cross-reference with MNEHRC member health systems to identify FQHCs NOT in the consortium",
                "Prioritize FQHCs serving homeless, uninsured, or justice-involved populations",
                "Draft outreach approach specific to FQHC data infrastructure needs",
            ],
        ),
        (
            "Medicaid 1115 Reentry Waiver Evaluation — Minnesota and Neighboring States",
            60,
            (
                "CMS has made Medicaid coverage for people leaving incarceration available through "
                "1115 waivers with mandatory evaluation requirements. This is a major emerging "
                "funding stream. Minnesota may be pursuing a reentry waiver; neighboring states "
                "(Wisconsin, Iowa, Illinois, North Dakota) may already have approved waivers. "
                "Evaluation contracts flow from state Medicaid agencies, often through prime "
                "contractors. LLC-eligible. This is a high-priority market opportunity."
            ),
            [
                "Check KFF 1115 waiver tracker for current status of MN, WI, IA, IL, ND reentry waivers",
                "Identify which states have approved waivers and who holds the evaluation contracts",
                "Research CMS evaluation requirements for reentry waivers to understand data infrastructure needs",
                "Draft one-page capability brief specific to reentry waiver evaluation data infrastructure",
                "Contact Minnesota DHS to understand MN's reentry waiver timeline and evaluation planning",
            ],
        ),
        (
            "Blue Cross and Blue Shield of MN Foundation — Health Equity Grants",
            90,
            (
                "Minnesota-based foundation with a 2023-2026 funding cycle focused on building healthy "
                "generations and health equity. Foundation grants are NOT available to for-profits — "
                "this is a nonprofit-phase opportunity. However, research their current grantees to "
                "understand the landscape and identify potential collaborators. Monitor for 2027+ "
                "funding cycle announcements."
            ),
            [
                "Review bluecrossmnfoundation.org for current grant programs and priorities",
                "Identify current grantees working on health data and equity — potential collaborators",
                "Subscribe to foundation grant notifications for next funding cycle",
                "Flag as a priority application for Year 3 nonprofit phase",
            ],
        ),
        (
            "Otto Bremer Trust — Health Program",
            120,
            (
                "St. Paul-based trust funding health and community wellbeing in MN, ND, and WI. "
                "Accepts letters of inquiry on a rolling basis. Health equity focus is well-aligned. "
                "Requires nonprofit status for most programs. Priority for Year 3 nonprofit launch."
            ),
            [
                "Review ottobremer.org for current health program guidelines",
                "Determine whether LLC is eligible for any Bremer programs or if nonprofit status is required",
                "Draft a letter of inquiry concept (2 paragraphs) describing the practice's mission for future use",
                "Identify a program officer contact for an introductory conversation",
            ],
        ),
        (
            "McKnight Foundation — Health Equity Program",
            120,
            (
                "Minneapolis foundation with health equity and systems change focus. Competitive but "
                "well-aligned with long-term nonprofit mission. Requires nonprofit status. Priority for "
                "Year 3."
            ),
            [
                "Review mcknight.org for current health program priorities",
                "Identify recent grantees in health data and equity space",
                "Determine application timeline and process for future submission",
            ],
        ),
        (
            "MDH Health Equity Funding — American Indian Health Special Emphasis Grant",
            30,
            (
                "MDH Office of Minority and Multicultural Health issues targeted grants including "
                "American Indian Health Special Emphasis grants. HTAC has documented gaps in Tribal "
                "data sovereignty and Indigenous health data — this is both a mission alignment and "
                "a potential funding pathway for work addressing those gaps. Eligibility varies by "
                "program."
            ),
            [
                "Review health.state.mn.us/communities/equity/funding for current open opportunities",
                "Subscribe to MDH grant notifications",
                "Assess eligibility of LLC vs nonprofit for equity-focused MDH programs",
                "Identify Tribal health contacts in Minnesota for partnership conversations around data sovereignty",
            ],
        ),
    ]


def _mnehrc_keys():
    return {
        ("Tyler", "Winkelman", "Hennepin Healthcare Research Institute"),
        ("Katherine", "Diaz Vickery", "Hennepin Healthcare Research Institute"),
        ("Peter", "Bodurtha", "Hennepin Healthcare Research Institute"),
        ("Renee", "Van Siclen", "Hennepin Healthcare Research Institute"),
        ("Steven", "Johnson", "University of Minnesota — Institute for Health Informatics"),
        ("Paul", "Drawz", "University of Minnesota — Division of Nephrology and Hypertension"),
        ("Alanna", "Chamberlain", "Mayo Clinic — Department of Quantitative Health Sciences"),
        ("Karen", "Margolis", "HealthPartners Institute"),
        ("Rebecca", "Rossom", "HealthPartners Institute"),
        ("Stephen", "Waring", "Essentia Institute of Rural Health"),
        ("Miriam", "Halstead Muscoplat", "Minnesota Department of Health"),
        ("Karen", "Soderberg", "Minnesota Department of Health"),
        ("Samuel", "Patnoe", "HealthPartners Institute"),
    }


def _county_organizations():
    return {
        "Ramsey County Public Health",
        "Anoka County Community Health and Environmental Services",
        "Dakota County Public Health",
        "Washington County Public Health",
        "St. Louis County Public Health",
        "Olmsted County Public Health",
    }


def _funder_organizations():
    return {
        "Robert Wood Johnson Foundation",
        "Blue Cross and Blue Shield of Minnesota Foundation",
        "Otto Bremer Trust",
        "McKnight Foundation",
        "Bush Foundation",
        "National Network of Public Health Institutes (NNPHI)",
    }


def _network_p4_organizations():
    return {
        "Common Health Coalition",
        "PCORnet — National Patient-Centered Clinical Research Network",
        "Wilder Research",
    }


def _is_mdh_contact(organization: str) -> bool:
    o = organization or ""
    return o.startswith("Minnesota Department of Health")


def _projects_to_link(contact: Contact, p4, p5, p6, p7) -> list[Project]:
    key = (contact.first_name, contact.last_name, contact.organization)
    projects: list[Project] = []
    org = contact.organization or ""

    if key in _mnehrc_keys():
        projects.extend([p7, p4])
    if _is_mdh_contact(org):
        projects.extend([p5, p4])
    if org in _county_organizations():
        projects.extend([p5, p4])
    if org in _funder_organizations():
        projects.extend([p6, p5])
    if org in _network_p4_organizations():
        projects.append(p4)

    # Dedupe preserving order
    seen = set()
    out = []
    for p in projects:
        if p.pk not in seen:
            seen.add(p.pk)
            out.append(p)
    return out


def _link_contact_projects(contact: Contact, projects: list[Project]) -> int:
    added = 0
    for p in projects:
        if not contact.projects.filter(pk=p.pk).exists():
            contact.projects.add(p)
            added += 1
    return added


class Command(BaseCommand):
    help = (
        "Seed network contacts, conference events, and Funding Pipeline tasks. "
        "Requires seeded practice projects from seed_initial_tasks. "
        "Use --user (CTO) and optional --cspo for funding task assignees."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--user",
            required=True,
            help="Username or email for the CTO (same as seed_initial_tasks).",
        )
        parser.add_argument(
            "--cspo",
            default="",
            help="Username or email for CSPO; funding tasks assign to CSPO when set, else CTO.",
        )

    def handle(self, *args, **options):
        cto_user = _resolve_user(options["user"], label="CTO (--user)")
        cspo_raw = (options.get("cspo") or "").strip()
        cspo_user = _resolve_user(cspo_raw, label="CSPO (--cspo)") if cspo_raw else None
        assignee = cspo_user or cto_user

        p4 = _require_project(P4)
        p5 = _require_project(P5)
        p6 = _require_project(P6)
        p7 = _require_project(P7)

        stats = {
            "contacts_seeded": 0,
            "contacts_skipped": 0,
            "events_seeded": 0,
            "funding_tasks_seeded": 0,
            "funding_subtasks_seeded": 0,
            "contact_links_added": 0,
        }

        # --- Step 1: Contacts ---
        contact_defs = _contact_definitions()
        for cdef in contact_defs:
            fn = cdef["first_name"].strip()
            ln = cdef["last_name"].strip()
            org = (cdef.get("organization") or "").strip()

            exists = Contact.objects.filter(
                first_name=fn,
                last_name=ln,
                organization=org,
            ).first()
            if exists:
                stats["contacts_skipped"] += 1
                logger.info(
                    "Skipped existing contact: %s %s @ %s",
                    fn,
                    ln,
                    org,
                )
                self.stdout.write(
                    self.style.WARNING(
                        f'Skipped existing contact: "{fn}" "{ln}" @ {org}'
                    )
                )
                contact = exists
            else:
                contact = Contact.objects.create(
                    first_name=fn,
                    last_name=ln,
                    organization=org,
                    title=(cdef.get("title") or "").strip(),
                    email=(cdef.get("email") or "").strip(),
                    phone=(cdef.get("phone") or "").strip(),
                    contact_type=cdef["contact_type"],
                    notes=cdef.get("notes", ""),
                    added_by=cto_user,
                )
                stats["contacts_seeded"] += 1

            stats["contact_links_added"] += _link_contact_projects(
                contact,
                _projects_to_link(contact, p4, p5, p6, p7),
            )

        # --- Step 2: Events ---
        event_attendees = [cto_user] + ([cspo_user] if cspo_user else [])
        for ed in _event_definitions(p4):
            desc = ed.get("notes") or ed.get("description") or ""
            start = ed["start_datetime"]
            if Event.objects.filter(title=ed["title"], start_datetime=start).exists():
                continue
            ev = Event.objects.create(
                title=ed["title"],
                description=desc,
                event_type=ed["event_type"],
                project=ed.get("project"),
                task=None,
                start_datetime=start,
                end_datetime=ed.get("end_datetime"),
                all_day=ed["all_day"],
                created_by=cto_user,
            )
            for u in event_attendees:
                ev.attendees.add(u)
            stats["events_seeded"] += 1

        # --- Step 3: Funding Pipeline ---
        today = timezone.now().date()
        funding_project = Project.objects.filter(name=FUNDING_PROJECT_NAME).first()
        project_created = False
        if funding_project is None:
            funding_project = Project.objects.create(
                name=FUNDING_PROJECT_NAME,
                description="Funding opportunities to research and pursue.",
                status=ProjectStatus.ACTIVE,
                priority=Priority.HIGH,
                owner=cto_user,
            )
            project_created = True
            ProjectMembership.objects.get_or_create(
                project=funding_project,
                user=cto_user,
                defaults={"role": MembershipRole.OWNER},
            )
            if cspo_user:
                ProjectMembership.objects.get_or_create(
                    project=funding_project,
                    user=cspo_user,
                    defaults={"role": MembershipRole.ADMIN},
                )
        else:
            ProjectMembership.objects.get_or_create(
                project=funding_project,
                user=cto_user,
                defaults={"role": MembershipRole.OWNER},
            )
            if cspo_user:
                ProjectMembership.objects.get_or_create(
                    project=funding_project,
                    user=cspo_user,
                    defaults={"role": MembershipRole.ADMIN},
                )
            self.stdout.write(
                self.style.WARNING(
                    f'Project "{FUNDING_PROJECT_NAME}" already exists; creating missing tasks only.'
                )
            )

        if project_created:
            self.stdout.write(
                self.style.SUCCESS(f'Created project "{FUNDING_PROJECT_NAME}".')
            )

        for title, due_days, description, subtasks in _funding_task_definitions():
            due = today + timedelta(days=due_days)
            parent = Task.objects.filter(
                project=funding_project,
                parent_task__isnull=True,
                title=title,
            ).first()
            if parent is None:
                parent = Task.objects.create(
                    project=funding_project,
                    parent_task=None,
                    title=title,
                    description=description,
                    status=TaskStatus.TODO,
                    priority=Priority.HIGH,
                    created_by=cto_user,
                    due_date=due,
                    order=0,
                )
                parent.assignees.set([assignee])
                stats["funding_tasks_seeded"] += 1
            else:
                if description and not parent.description:
                    parent.description = description
                    parent.save(update_fields=["description"])

            for stitle in subtasks:
                if Task.objects.filter(
                    project=funding_project,
                    parent_task=parent,
                    title=stitle,
                ).exists():
                    continue
                sub = Task.objects.create(
                    project=funding_project,
                    parent_task=parent,
                    title=stitle,
                    description="",
                    status=TaskStatus.BACKLOG,
                    priority=Priority.HIGH,
                    created_by=cto_user,
                    due_date=None,
                    order=0,
                )
                sub.assignees.set([assignee])
                stats["funding_subtasks_seeded"] += 1

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("Network seed summary"))
        self.stdout.write(f"Seeded Contacts:              {stats['contacts_seeded']}")
        if stats["contacts_skipped"]:
            self.stdout.write(
                f"Skipped contacts (existing):  {stats['contacts_skipped']}"
            )
        self.stdout.write(f"Seeded Conference Events:     {stats['events_seeded']}")
        self.stdout.write(f"Seeded Funding Tasks:         {stats['funding_tasks_seeded']}")
        self.stdout.write(f"Funding subtasks:             {stats['funding_subtasks_seeded']}")
        self.stdout.write(f"Contacts linked to projects:  {stats['contact_links_added']}")
