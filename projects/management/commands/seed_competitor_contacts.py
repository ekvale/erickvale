"""
Seed competitive landscape contacts, tasks, and project links for the practice.

Idempotent: skips contacts that already exist with the same organization name
and first name. Reuses project
"Competitive Intelligence and Market Positioning" if present.

Run:
  python manage.py seed_competitor_contacts --user <username_or_email> [--cspo <cspo_username_or_email>]

Optional --cspo assigns competitive-intelligence tasks to CSPO; otherwise tasks
assign to --user (and a note is logged).
"""

from __future__ import annotations

import logging
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q
from django.utils import timezone

from projects.models import (
    Contact,
    ContactType,
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

COMPETITIVE_PROJECT_NAME = "Competitive Intelligence and Market Positioning"
P4 = "Business Development and Market Entry"
P5 = "Grant Applications"

# Role placeholders: match seed_network_data — last_name "(Contact Name)" for unknown individuals.
_ROLE_LAST = "(Contact Name)"


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


def _link_contact_projects(contact: Contact, projects: list[Project]) -> int:
    added = 0
    for p in projects:
        if not contact.projects.filter(pk=p.pk).exists():
            contact.projects.add(p)
            added += 1
    return added


def _get_project_by_name(name: str) -> Project | None:
    return Project.objects.filter(name=name).first()


def _contact_definitions():
    """All competitor / landscape contacts; email blank unless known."""
    return [
        {
            "first_name": "(Contracting Lead)",
            "last_name": _ROLE_LAST,
            "organization": "Booz Allen Hamilton — Health",
            "title": "Health Division Contracting and Partnerships",
            "email": "",
            "phone": "",
            "contact_type": ContactType.OTHER,
            "notes": (
                "Tier 1 federal IT prime. Holds the CDC Data Modernization Accelerator (DMAC) "
                "contract — a $1.67B task order on GSA Alliant 2 (Award ID: 47QFCA23F0058). Also "
                "holds CDC Infrastructure IT Services Bridge contract. Booz Allen is publicly "
                "traded, ~10% operating margins, primarily federal IDIQ and GSA schedule revenue. "
                "Minimum engagement size and overhead structure make them noncompetitive for county "
                "and regional public health clients — but they generate subcontracting "
                "opportunities. Monitor CDC and HHS contract awards via usaspending.gov for Booz "
                "Allen task orders where OMOP or public health data infrastructure is in scope. "
                "Identify their subcontractor roster on DMAC as a relationship target."
            ),
        },
        {
            "first_name": "(Contracting Lead)",
            "last_name": _ROLE_LAST,
            "organization": "Leidos — Health and Civil",
            "title": "Health Division",
            "email": "",
            "phone": "",
            "contact_type": ContactType.OTHER,
            "notes": (
                "Tier 1 federal IT prime. $17.2B FY2025 revenue, 3% YoY growth. Competes with Booz "
                "Allen for enterprise IT contracts in the $500M–$2B range. Has health data "
                "analytics capabilities. Not in OHDSI community or federated public health "
                "surveillance space. Subcontracting opportunity if they win HHS or CDC health data "
                "infrastructure vehicles. Monitor SAM.gov for Leidos health data solicitations."
            ),
        },
        {
            "first_name": "(Contracting Lead)",
            "last_name": _ROLE_LAST,
            "organization": "Peraton — Health",
            "title": "Health Division",
            "email": "",
            "phone": "",
            "contact_type": ContactType.OTHER,
            "notes": (
                "Tier 1 federal IT prime. Approaching $8B annual revenue. Veritas Capital-backed, "
                "potential IPO candidate. Has health data analytics capabilities and recently "
                "cited health data analytics in contract announcements. Not in OHDSI or federated "
                "public health surveillance space. Same subcontracting opportunity profile as Booz "
                "Allen and Leidos. Monitor for HHS and CDC contract vehicles."
            ),
        },
        {
            "first_name": "(Research Director)",
            "last_name": _ROLE_LAST,
            "organization": "RTI International — Data Modernization Practice",
            "title": "Director, Data Modernization",
            "email": "",
            "phone": "",
            "contact_type": ContactType.RESEARCH,
            "notes": (
                "$1.4B revenue nonprofit research institute. 5,000–10,000 employees. Explicitly has "
                "a data modernization practice covering OMOP, health IT infrastructure, and public "
                "health surveillance. Their MENDS project is a multi-site OMOP demonstration "
                "directly adjacent to HTAC work. Primarily funded by HHS, CDC, NIH, and USAID "
                "federal contracts — 80–90% of revenue is federal. Cannot serve small and "
                "mid-sized organizations due to overhead structure and minimum engagement size. "
                "Target as a subcontracting partner on federal solicitations where RTI is the "
                "prime. Identify RTI's health IT and data modernization practice leads for "
                "introductory outreach. Search USAspending.gov for RTI awards in public health "
                "data infrastructure."
            ),
        },
        {
            "first_name": "(Research Director)",
            "last_name": _ROLE_LAST,
            "organization": "Mathematica Policy Research",
            "title": "Health Division",
            "email": "",
            "phone": "",
            "contact_type": ContactType.RESEARCH,
            "notes": (
                "Approximately $500M revenue. Major federal contractor for health program "
                "evaluation, Medicaid analytics, and data infrastructure. Primary clients: HHS, "
                "CMS, state Medicaid agencies. Has population health and data modernization "
                "capabilities. Same profile as RTI — too large and slow for county and regional "
                "engagements, strong subcontracting target for federal work. Mathematica holds "
                "significant CMS and Medicaid evaluation contracts — relevant to 1115 Reentry "
                "Waiver evaluation pipeline. Identify their health data and Medicaid evaluation "
                "practice leads."
            ),
        },
        {
            "first_name": "(Research Director)",
            "last_name": _ROLE_LAST,
            "organization": "ICF International — Public Health",
            "title": "Health Practice",
            "email": "",
            "phone": "",
            "contact_type": ContactType.RESEARCH,
            "notes": (
                "$2B+ revenue consulting and technology firm. CDC, HHS, and state government "
                "contracts. Has a public health data practice. Similar competitive profile to RTI "
                "and Mathematica — federal contractor too large for local public health clients. "
                "Subcontracting target. Monitor their CDC and HHS contract awards."
            ),
        },
        {
            "first_name": "(Research Director)",
            "last_name": _ROLE_LAST,
            "organization": "Westat",
            "title": "Health Research Division",
            "email": "",
            "phone": "",
            "contact_type": ContactType.RESEARCH,
            "notes": (
                "Approximately $600M revenue nonprofit research organization. Primarily federal "
                "survey and data collection contracts. Population health and surveillance focus. "
                "Less relevant to OMOP infrastructure specifically but competes for similar "
                "federal evaluation and surveillance contracts. Subcontracting target for "
                "survey-linked population health work."
            ),
        },
        {
            "first_name": "Maria",
            "last_name": "Chatzou Dunford",
            "organization": "Lifebit",
            "title": "CEO and Co-founder",
            "email": "",
            "phone": "",
            "contact_type": ContactType.RESEARCH,
            "notes": (
                "UK-based federated data platform company. Venture-backed — raised approximately "
                "$60M across Series A and B. Managing 275M+ records across 30+ countries. Clients "
                "include NIH, Genomics England, and Singapore Ministry of Health. Their Trusted "
                "Data Factory claims AI-powered OMOP harmonization in 48 hours. Primary market "
                "is biopharma R&D and national precision medicine programs — not state and local "
                "public health equity work. Revenue model: enterprise SaaS licensing to "
                "pharmaceutical companies and national health agencies. Not a direct competitor "
                "in the county public health or community organization market but actively "
                "writing OMOP content and expanding into US government. Monitor their US "
                "government and NIH relationships. Potential future competitive pressure if they "
                "move into state-level public health markets."
            ),
        },
        {
            "first_name": "(Business Development)",
            "last_name": _ROLE_LAST,
            "organization": "IQVIA — OMOP Health Data",
            "title": "Real World Data Division",
            "email": "",
            "phone": "",
            "contact_type": ContactType.OTHER,
            "notes": (
                "$15B+ revenue publicly traded company. Offers OMOP ETL pipeline tooling as a "
                "product (IQVIA OMOP Health Data) — a pipelining service for streaming OMOP "
                "dataset creation. Primary clients are pharmaceutical companies for real-world "
                "evidence studies. Has published on OMOP in federal health contexts including "
                "military health analytics. Not in public health equity or county-level "
                "surveillance space. Revenue: primarily pharmaceutical data products and consulting. "
                "Not a direct competitor. Relevant as a signal of enterprise demand for OMOP "
                "tooling and as a potential integration target if health system clients are "
                "already using IQVIA data products."
            ),
        },
        {
            "first_name": "(Business Development)",
            "last_name": _ROLE_LAST,
            "organization": "TriNetX",
            "title": "Federated Network Operations",
            "email": "",
            "phone": "",
            "contact_type": ContactType.RESEARCH,
            "notes": (
                "Global federated health research network. Provides real-time patient-level data "
                "access for clinical trial feasibility analysis and real-world evidence studies. "
                "Revenue from pharmaceutical and biotech clients paying for network access fees. "
                "Not a consulting firm and not in the public health equity or county surveillance "
                "space. Relevant as a comparable federated network model — their governance, "
                "data use agreement, and site onboarding approaches are worth studying. Not a "
                "competitor."
            ),
        },
        {
            "first_name": "(Business Development)",
            "last_name": _ROLE_LAST,
            "organization": "John Snow Labs",
            "title": "Healthcare AI Division",
            "email": "",
            "phone": "",
            "contact_type": ContactType.RESEARCH,
            "notes": (
                "Healthcare NLP and AI company. No venture funding — entirely revenue-funded from "
                "enterprise software licensing. 325% YoY cloud marketplace growth. 130M+ Spark NLP "
                "downloads. 26 partners including Oracle, AWS, Azure, Deloitte, Accenture, Booz "
                "Allen. Government clients include the VA. Their Patient Journey Intelligence "
                "product does OMOP harmonization — moving toward OMOP integration from an NLP "
                "entry point. Primary market remains healthcare NLP for clinical text: "
                "de-identification, entity recognition, clinical note extraction. Adjacent to but "
                "not overlapping with federated population health surveillance for public health "
                "equity. Revenue model: enterprise software licenses plus professional services. No "
                "outside investment. Relevant to watch as they expand their OMOP footprint — if "
                "they move toward federated public health surveillance they become a more direct "
                "competitor."
            ),
        },
        {
            "first_name": "(Business Development)",
            "last_name": _ROLE_LAST,
            "organization": "Arcadia",
            "title": "Health Data Platform",
            "email": "",
            "phone": "",
            "contact_type": ContactType.OTHER,
            "notes": (
                "US health data platform company. Serves health systems, ACOs, and payers for "
                "value-based care analytics. Has OMOP integration capabilities. Revenue primarily "
                "from health system SaaS contracts. Not in the federated public health surveillance "
                "or county health equity space. Relevant as a signal that health system clients may "
                "already have Arcadia-generated OMOP-adjacent data — potential integration "
                "consideration for clients considering OMOP implementation alongside existing "
                "Arcadia infrastructure."
            ),
        },
        {
            "first_name": "(Program Director)",
            "last_name": _ROLE_LAST,
            "organization": "Public Health Informatics Institute (PHII)",
            "title": "Technical Assistance Program",
            "email": "",
            "phone": "",
            "contact_type": ContactType.RESEARCH,
            "notes": (
                "Nonprofit providing public health IT consulting and technical assistance to health "
                "departments. Primarily funded by CDC cooperative agreements and foundation "
                "grants. Does not do OMOP implementation or federated network architecture — "
                "their work is more focused on health information exchange, public health IT "
                "strategy, and workforce development. Not a direct competitor in OMOP "
                "infrastructure but competes for CDC technical assistance funding. Relevant as a "
                "potential partner for public health agency engagements where PHII handles IT "
                "strategy and this practice handles OMOP implementation. Identify their program "
                "staff working on data modernization for introductory outreach."
            ),
        },
        {
            "first_name": "(Program Director)",
            "last_name": _ROLE_LAST,
            "organization": "ASTHO — Association of State and Territorial Health Officials",
            "title": "Data and Informatics Program",
            "email": "",
            "phone": "",
            "contact_type": ContactType.GOVERNMENT,
            "notes": (
                "National nonprofit representing state and territorial health officials. CDC "
                "PHIG Component B partner alongside NNPHI. Attends and co-hosts PHIG recipient "
                "convenings. Key intermediary between CDC funding and state health department "
                "implementation. Not a competitor but a potential referral source for state health "
                "departments seeking OMOP and federated data infrastructure technical assistance. "
                "Monitor ASTHO publications and convenings for state health department data "
                "modernization priorities."
            ),
        },
        {
            "first_name": "(Program Director)",
            "last_name": _ROLE_LAST,
            "organization": "Altarum Institute",
            "title": "Health Data and Analytics",
            "email": "",
            "phone": "",
            "contact_type": ContactType.RESEARCH,
            "notes": (
                "Nonprofit research and consulting organization. Health systems and policy focus. "
                "Has public health analytics capabilities. Some overlap with RTI and Mathematica "
                "in the federal research nonprofit space but smaller scale. Less relevant to OMOP "
                "infrastructure specifically. Monitor for federal contract vehicles where "
                "Altarum is prime and OMOP or public health data infrastructure is in scope."
            ),
        },
        {
            "first_name": "(Program Director)",
            "last_name": _ROLE_LAST,
            "organization": "Deloitte — Government and Public Services Health",
            "title": "Health Data Modernization Practice",
            "email": "",
            "phone": "",
            "contact_type": ContactType.OTHER,
            "notes": (
                "Big Four consulting firm. Has a government health practice that competes for "
                "large federal health IT contracts alongside Booz Allen and Leidos. Listed as a "
                "John Snow Labs partner — integrating healthcare NLP with Deloitte's government "
                "health data work. Relevant as a potential subcontracting target on federal health "
                "data modernization solicitations. Deloitte occasionally subcontracts specialized "
                "technical components to smaller firms. Their government health practice has CDC "
                "and HHS relationships. Not a competitor for county and regional public health "
                "engagements."
            ),
        },
    ]


def _task_definitions():
    """Parent title, due offset days, description, subtask titles."""
    return [
        (
            "Monitor Booz Allen CDC DMAC subcontractor roster",
            60,
            (
                "Track DMAC (Award ID 47QFCA23F0058) subcontractor ecosystem for OMOP and "
                "public health data infrastructure opportunities."
            ),
            [
                "Search USAspending.gov for DMAC task order (Award ID 47QFCA23F0058) subcontract awards",
                "Identify which subcontractors are receiving OMOP or public health data infrastructure task orders",
                "Research whether any subcontractors are small businesses or individuals — signals that small firm participation is viable",
                "Identify the Booz Allen program manager on DMAC for potential introductory outreach",
            ],
        ),
        (
            "Research RTI International MENDS project and identify practice leads",
            45,
            "Support federal subcontracting positioning adjacent to RTI OMOP and data modernization work.",
            [
                "Search for published materials on RTI's MENDS multi-site OMOP demonstration",
                "Identify RTI's health IT and data modernization practice leads by name",
                "Research whether RTI uses external subcontractors for OMOP implementation components",
                "Draft a brief introduction email for outreach to RTI health data practice",
            ],
        ),
        (
            "Monitor Mathematica CMS and Medicaid evaluation contract pipeline",
            60,
            "Track Mathematica awards relevant to Medicaid, 1115 waivers, and health data infrastructure.",
            [
                "Search USAspending.gov for Mathematica awards related to Medicaid evaluation and 1115 waivers",
                "Identify whether any Medicaid 1115 Reentry Waiver evaluation contracts are held by Mathematica",
                "Research Mathematica's subcontracting practices for health data infrastructure components",
                "Identify Mathematica health division contacts working on Medicaid and criminal justice health data",
            ],
        ),
        (
            "Track Lifebit US government expansion",
            90,
            "Monitor competitive pressure from Lifebit in US public-sector and OMOP-adjacent markets.",
            [
                "Monitor Lifebit press releases and blog posts for US state and local government announcements",
                "Determine whether Lifebit is pursuing state health department clients in addition to federal agencies",
                "Assess whether their 48-hour OMOP harmonization claim is technically credible for the public health surveillance use case",
                "Note: their primary market remains biopharma and national precision medicine — flag if this changes",
            ],
        ),
        (
            "Research PHII technical assistance programs and identify overlap",
            45,
            "Clarify partnership vs overlap with PHII on public health agency data modernization.",
            [
                "Review PHII current programs and technical assistance offerings at phii.org",
                "Identify which of their programs involve data modernization or OMOP-adjacent work",
                "Determine whether PHII and this practice could serve complementary roles on public health agency engagements",
                "Identify PHII program staff for introductory outreach",
            ],
        ),
        (
            "Monitor SAM.gov for health data infrastructure solicitations where subcontracting is viable",
            30,
            "Systematic opportunity tracking for small-business-friendly federal and state solicitations.",
            [
                "Set up SAM.gov alerts for NAICS 541512 (computer systems design) and 541611 (management consulting) awards at HHS, CDC, and state health departments",
                "Identify solicitations below $150,000 threshold where small business or individual subcontracting is common",
                "Monitor for CDC PHIG-related solicitations at state and local levels",
                "Create a tracking spreadsheet or project task for each viable opportunity identified",
            ],
        ),
    ]


def _extra_projects_for_org(org: str, p4: Project | None, p5: Project | None) -> list[Project]:
    """Step 4: additional project links by exact organization string."""
    extra: list[Project] = []
    tier1 = {
        "Booz Allen Hamilton — Health",
        "Leidos — Health and Civil",
        "Peraton — Health",
    }
    tier2_research = {
        "RTI International — Data Modernization Practice",
        "Mathematica Policy Research",
        "ICF International — Public Health",
        "Westat",
    }
    tier4_phii_astho = {
        "Public Health Informatics Institute (PHII)",
        "ASTHO — Association of State and Territorial Health Officials",
    }
    if org in tier1 and p5:
        extra.append(p5)
    if org in tier2_research:
        if p5:
            extra.append(p5)
        if p4:
            extra.append(p4)
    if org in tier4_phii_astho and p4:
        extra.append(p4)
    return extra


class Command(BaseCommand):
    help = (
        "Seed competitive intelligence project, contacts, tasks, and cross-project links. "
        "Optional --cspo assigns tasks to CSPO; otherwise assignees default to --user."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--user",
            required=True,
            help="Username or email for project owner and contact added_by (same as seed_network_data).",
        )
        parser.add_argument(
            "--cspo",
            default="",
            help="Username or email for CSPO; competitive intelligence tasks assign to CSPO when set, else --user.",
        )

    def handle(self, *args, **options):
        owner_user = _resolve_user(options["user"], label="Owner (--user)")
        cspo_raw = (options.get("cspo") or "").strip()
        cspo_user = _resolve_user(cspo_raw, label="CSPO (--cspo)") if cspo_raw else None
        assignee = cspo_user or owner_user

        if cspo_user is None:
            self.stdout.write(
                self.style.WARNING(
                    "CSPO (--cspo) was not specified; all competitive intelligence tasks "
                    "assigned to --user."
                )
            )

        p4 = _get_project_by_name(P4)
        p5 = _get_project_by_name(P5)
        if p4 is None:
            self.stdout.write(
                self.style.WARNING(
                    f'Project "{P4}" not found; skipping Business Development cross-links.'
                )
            )
        if p5 is None:
            self.stdout.write(
                self.style.WARNING(
                    f'Project "{P5}" not found; skipping Grant Applications cross-links.'
                )
            )

        stats = {
            "contacts_seeded": 0,
            "contacts_skipped": 0,
            "tasks_seeded": 0,
            "subtasks_seeded": 0,
            "contact_links_added": 0,
        }

        comp_project = _get_project_by_name(COMPETITIVE_PROJECT_NAME)
        project_created = False
        if comp_project is None:
            comp_project = Project.objects.create(
                name=COMPETITIVE_PROJECT_NAME,
                description=(
                    "Tracking competitors, adjacent organizations, and market context relevant to "
                    "positioning the practice. Includes federal IT primes, research nonprofits, "
                    "health data platform vendors, and organizations operating in adjacent spaces."
                ),
                status=ProjectStatus.ACTIVE,
                priority=Priority.MEDIUM,
                owner=owner_user,
            )
            project_created = True
            ProjectMembership.objects.get_or_create(
                project=comp_project,
                user=owner_user,
                defaults={"role": MembershipRole.OWNER},
            )
            if cspo_user:
                ProjectMembership.objects.get_or_create(
                    project=comp_project,
                    user=cspo_user,
                    defaults={"role": MembershipRole.ADMIN},
                )
            self.stdout.write(
                self.style.SUCCESS(f'Created project "{COMPETITIVE_PROJECT_NAME}".')
            )
        else:
            ProjectMembership.objects.get_or_create(
                project=comp_project,
                user=owner_user,
                defaults={"role": MembershipRole.OWNER},
            )
            if cspo_user:
                ProjectMembership.objects.get_or_create(
                    project=comp_project,
                    user=cspo_user,
                    defaults={"role": MembershipRole.ADMIN},
                )
            self.stdout.write(
                self.style.WARNING(
                    f'Project "{COMPETITIVE_PROJECT_NAME}" already exists; '
                    "creating missing contacts and tasks only."
                )
            )

        for cdef in _contact_definitions():
            fn = cdef["first_name"].strip()
            ln = cdef["last_name"].strip()
            org = (cdef.get("organization") or "").strip()

            exists = Contact.objects.filter(
                organization__iexact=org,
                first_name__iexact=fn,
            ).first()
            if exists:
                stats["contacts_skipped"] += 1
                logger.info(
                    "Skipped existing contact: %s @ %s",
                    fn,
                    org,
                )
                self.stdout.write(
                    self.style.WARNING(
                        f'Skipped existing contact: "{fn}" @ {org}'
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
                    added_by=owner_user,
                )
                stats["contacts_seeded"] += 1

            stats["contact_links_added"] += _link_contact_projects(contact, [comp_project])

            extras = _extra_projects_for_org(org, p4, p5)
            stats["contact_links_added"] += _link_contact_projects(contact, extras)

        today = timezone.now().date()
        for title, due_days, description, subtasks in _task_definitions():
            due = today + timedelta(days=due_days)
            parent = Task.objects.filter(
                project=comp_project,
                parent_task__isnull=True,
                title=title,
            ).first()
            if parent is None:
                parent = Task.objects.create(
                    project=comp_project,
                    parent_task=None,
                    title=title,
                    description=description,
                    status=TaskStatus.TODO,
                    priority=Priority.MEDIUM,
                    created_by=owner_user,
                    due_date=due,
                    order=0,
                )
                parent.assignees.set([assignee])
                stats["tasks_seeded"] += 1
            else:
                if description and not parent.description:
                    parent.description = description
                    parent.save(update_fields=["description"])

            for stitle in subtasks:
                if Task.objects.filter(
                    project=comp_project,
                    parent_task=parent,
                    title=stitle,
                ).exists():
                    continue
                sub = Task.objects.create(
                    project=comp_project,
                    parent_task=parent,
                    title=stitle,
                    description="",
                    status=TaskStatus.TODO,
                    priority=Priority.MEDIUM,
                    created_by=owner_user,
                    due_date=None,
                    order=0,
                )
                sub.assignees.set([assignee])
                stats["subtasks_seeded"] += 1

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("Competitive landscape seed summary"))
        self.stdout.write(
            f"Seeded Contacts:           {stats['contacts_seeded']} "
            f"({stats['contacts_skipped']} skipped as existing)"
        )
        self.stdout.write(f"Seeded Tasks:              {stats['tasks_seeded']}")
        self.stdout.write(f"Seeded Subtasks:           {stats['subtasks_seeded']}")
        if project_created:
            self.stdout.write(
                f"Project created:           {COMPETITIVE_PROJECT_NAME}"
            )
        else:
            self.stdout.write(
                f"Project created:           (existing - {COMPETITIVE_PROJECT_NAME})"
            )
        self.stdout.write(
            f"Contacts linked to projects: {stats['contact_links_added']} linkages"
        )
