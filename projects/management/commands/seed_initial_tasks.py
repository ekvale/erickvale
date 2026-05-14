"""
Seed projects, tasks, subtasks, events, and contacts for local/demo use.

This command did not exist in the repository history; it was added to match the
co-owner assignment spec (CTO via --user, optional CSPO via --cspo).

Run:
  python manage.py seed_initial_tasks --user <cto_username_or_email> [--cspo <cspo_username_or_email>]

If --cspo is omitted, all task assignees default to the CTO user (backward compatible).
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

# --- Exact project titles (used for assignment routing) ---
P1 = "LLC Formation and Legal"
P2 = "Brand and Professional Identity"
P3 = "Website Development"
P4 = "Business Development and Market Entry"
P5 = "Grant Applications"
P6 = "Nonprofit Transition Planning"
P7 = "OMOP and Technical Skill Development"

# Assign keys: "cto" | "cspo" | "both" | "inherit" (inherit only for nested subtasks — use parent key)


def _assignee_users(assign_key: str, cto_user, cspo_user):
    """Resolve assign key to a list of User instances (no duplicates)."""
    if assign_key == "cto":
        return [cto_user]
    if assign_key == "cspo":
        return [cspo_user or cto_user]
    if assign_key == "both":
        if cspo_user:
            return [cto_user, cspo_user]
        return [cto_user]
    raise ValueError(f"Unknown assign_key: {assign_key}")


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


def _seed_project_definitions():
    """Nested seed: each task has title, assign, optional subtasks (str or {title, assign})."""
    return [
        {
            "name": P1,
            "description": "Legal entity formation, tax registration, and operating agreements.",
            "tasks": [
                {
                    "title": "Choose and register LLC name with Minnesota Secretary of State",
                    "assign": "cspo",
                    "subtasks": [
                        "Verify name availability in Minnesota Business Entity Search",
                        "Prepare and file Articles of Organization",
                    ],
                },
                {
                    "title": "Obtain Employer Identification Number (EIN) from IRS",
                    "assign": "cspo",
                    "subtasks": [
                        "Complete IRS Form SS-4 online application",
                        "Store EIN confirmation letter with business records",
                    ],
                },
                {
                    "title": "Open a dedicated business checking account",
                    "assign": "cspo",
                    "subtasks": [
                        "Compare business account options at local banks",
                        "Provide EIN and operating agreement to bank",
                    ],
                },
                {
                    "title": "Draft Operating Agreement",
                    "assign": "cspo",
                    "subtasks": [
                        "Outline member roles and capital contributions",
                        "Review draft with legal counsel template",
                    ],
                },
                {
                    "title": "Register for Minnesota state taxes",
                    "assign": "cspo",
                    "subtasks": [
                        "Create Minnesota e-Services account",
                        "Complete sales and withholding tax registration as applicable",
                    ],
                },
                {
                    "title": "Obtain professional liability (E&O) insurance",
                    "assign": "cspo",
                    "subtasks": [
                        "Request quotes from at least three carriers",
                        "Bind policy and store certificate of insurance",
                    ],
                },
                {
                    "title": "Set up accounting system",
                    "assign": "cto",
                    "subtasks": [
                        "Select chart of accounts aligned with consulting revenue",
                        "Configure recurring expense categories",
                    ],
                },
            ],
        },
        {
            "name": P2,
            "description": "Brand positioning, digital presence, and client-facing materials.",
            "tasks": [
                {
                    "title": "Set up project intake process",
                    "assign": "cto",
                    "subtasks": [
                        "Define intake form fields and routing rules",
                        "Pilot intake with first prospective client",
                    ],
                },
                {
                    "title": "Establish custom domain email address",
                    "assign": "cspo",
                    "subtasks": [
                        "Purchase domain and configure DNS MX records",
                        "Provision mailboxes for core roles",
                    ],
                },
                {
                    "title": "Develop one-page capability statement",
                    "assign": "cspo",
                    "subtasks": [
                        "Draft service lines and differentiators",
                        "Finalize layout for print and PDF",
                    ],
                },
                {
                    "title": "Create LinkedIn profile optimized for this work",
                    "assign": "cspo",
                    "subtasks": [
                        "Align headline with positioning statement",
                        "Add featured projects and publications",
                    ],
                },
                {
                    "title": "Develop standard consulting agreement template",
                    "assign": "cspo",
                    "subtasks": [
                        "Define scope, fees, and IP clauses with counsel review",
                        "Publish template in shared drive",
                    ],
                },
            ],
        },
        {
            "name": P3,
            "description": "Public site, HTAC demo integration, and deployment hardening.",
            "tasks": [
                {
                    "title": "Deploy production Django application",
                    "assign": "cto",
                    "subtasks": [
                        "Configure production database and secrets",
                        "Run collectstatic and smoke tests",
                    ],
                },
                {
                    "title": "Configure DNS and TLS certificates",
                    "assign": "cto",
                    "subtasks": [
                        "Point apex and www to application host",
                        "Automate certificate renewal",
                    ],
                },
                {
                    "title": "Implement monitoring and error alerting",
                    "assign": "cto",
                    "subtasks": [
                        "Add uptime checks for critical routes",
                        "Wire log aggregation for 5xx errors",
                    ],
                },
            ],
        },
        {
            "name": P4,
            "description": "Pipeline development, partnerships, and referral network.",
            "tasks": [
                {
                    "title": "Define ideal customer profile for consulting engagements",
                    "assign": "cspo",
                    "subtasks": [
                        "Interview three reference clients",
                        "Document ICP assumptions and exclusions",
                    ],
                },
                {
                    "title": "Build target account list for outreach",
                    "assign": "cspo",
                    "subtasks": [
                        "Segment by agency type and geography",
                        "Prioritize Tier 1 accounts for Q1",
                    ],
                },
                {
                    "title": "Establish referral relationships",
                    "assign": "both",
                    "subtasks": [
                        "Identify three partner organizations for warm intros",
                        "Schedule quarterly partner check-ins",
                    ],
                },
                {
                    "title": "Prepare conference and workshop attendance plan",
                    "assign": "cspo",
                    "subtasks": [
                        "Select two priority conferences for population health",
                        "Draft booth or speaking submission calendar",
                    ],
                },
            ],
        },
        {
            "name": P5,
            "description": "Federal and state funding opportunities aligned with technical services.",
            "tasks": [
                {
                    "title": "Develop boilerplate grant technical sections",
                    "assign": "cto",
                    "subtasks": [
                        "Standardize OMOP and federated network language blocks",
                        "Prepare data security and linkage appendix text",
                    ],
                },
                {
                    "title": "Research CDC Public Health Infrastructure Grant opportunities",
                    "assign": "cspo",
                    "subtasks": [
                        "Track NOFO release dates and eligibility",
                        "Summarize match requirements for state applicants",
                    ],
                },
                {
                    "title": "Research HRSA Health Center Program supplemental funding",
                    "assign": "cspo",
                    "subtasks": [
                        "Map FQHC technical assistance needs to our services",
                        "Maintain contact list for health center consortia",
                    ],
                },
                {
                    "title": "Monitor Medicaid 1115 Reentry Waiver evaluation opportunities",
                    "assign": "cspo",
                    "subtasks": [
                        "Subscribe to CMS evaluation guidance updates",
                        "Draft evaluation design talking points",
                    ],
                },
                {
                    "title": "Identify Minnesota-specific grant opportunities",
                    "assign": "cspo",
                    "subtasks": [
                        "Scan MDH and DHS procurement calendars",
                        "Log deadlines in shared grants tracker",
                    ],
                },
                {
                    "title": "Prepare quarterly grants pipeline summary",
                    "assign": "both",
                    "subtasks": [
                        "Reconcile active applications and decision dates",
                        "Circulate summary to leadership",
                    ],
                },
                {
                    "title": "Document proposal review checklist",
                    "assign": "both",
                    "subtasks": [
                        "List compliance and budget checks before submission",
                        "Assign reviewers for each section",
                    ],
                },
                {
                    "title": "Map funder eligibility matrix",
                    "assign": "both",
                    "subtasks": [
                        "Crosswalk services to allowable cost categories",
                        "Flag restrictions on subcontracting",
                    ],
                },
            ],
        },
        {
            "name": P6,
            "description": "Governance, mission alignment, and operational readiness for nonprofit structure.",
            "tasks": [
                {
                    "title": "Draft mission and theory of change statement",
                    "assign": "cspo",
                    "subtasks": [
                        "Facilitate stakeholder input session",
                        "Finalize one-page narrative for board packet",
                    ],
                },
                {
                    "title": "Compare fiscal sponsorship vs independent 501(c)(3) formation",
                    "assign": "cspo",
                    "subtasks": [
                        "Model three-year administrative cost scenarios",
                        "Summarize decision criteria for founders",
                    ],
                },
                {
                    "title": "Outline board composition and recruitment plan",
                    "assign": "cspo",
                    "subtasks": [
                        "Define required committees",
                        "Create board candidate rubric",
                    ],
                },
            ],
        },
        {
            "name": P7,
            "description": "OMOP CDM skills, OHDSI tooling, and technical depth for client delivery.",
            "tasks": [
                {
                    "title": "Complete OHDSI Foundations self-paced curriculum",
                    "assign": "cto",
                    "subtasks": [
                        "Finish SQL and CDM modules with exercises",
                        "Document key takeaways in team wiki",
                    ],
                },
                {
                    "title": "Run Achilles and Data Quality Dashboard on sample OMOP dataset",
                    "assign": "cto",
                    "subtasks": [
                        "Install Broadsea or local OHDSI stack",
                        "Export DQD findings for retrospective review",
                    ],
                },
                {
                    "title": "Prototype federated prevalence query against HTAC demo API",
                    "assign": "cto",
                    "subtasks": [
                        "Author cohort JSON for one condition",
                        "Validate response schema and suppression rules",
                    ],
                },
            ],
        },
    ]


def _seed_events(cto_user, cspo_user):
    """11 calendar events; created_by=CTO, attendees both when CSPO present."""
    base = timezone.now().replace(hour=10, minute=0, second=0, microsecond=0)
    rows = [
        ("LLC formation kickoff", EventType.MEETING, base + timedelta(days=3)),
        ("Operating agreement review session", EventType.REVIEW, base + timedelta(days=10)),
        ("Brand positioning workshop", EventType.MEETING, base + timedelta(days=14)),
        ("Website launch readiness review", EventType.REVIEW, base + timedelta(days=21)),
        ("Business development weekly sync", EventType.MEETING, base + timedelta(days=7, hours=2)),
        ("Grant pipeline quarterly planning", EventType.MEETING, base + timedelta(days=28)),
        ("CDC infrastructure NOFO deadline checkpoint", EventType.DEADLINE, base + timedelta(days=35)),
        ("Nonprofit transition steering committee", EventType.MEETING, base + timedelta(days=42)),
        ("OMOP study-a-thon prep block", EventType.MILESTONE, base + timedelta(days=49)),
        ("Partner referral relationship check-in", EventType.MEETING, base + timedelta(days=56)),
        ("EIN and bank account milestone", EventType.MILESTONE, base + timedelta(days=17)),
    ]
    out = []
    for title, etype, start in rows:
        out.append(
            {
                "title": title,
                "description": "",
                "event_type": etype,
                "start_datetime": start,
                "end_datetime": start + timedelta(hours=1),
                "all_day": False,
                "created_by": cto_user,
                "attendees": [cto_user] + ([cspo_user] if cspo_user else []),
            }
        )
    return out


def _seed_contacts():
    """Seven contacts; added_by=cspo_user when present else CTO passed in caller."""
    return [
        {
            "first_name": "Jordan",
            "last_name": "Ellis",
            "organization": "Hennepin County Public Health",
            "title": "Epidemiology Manager",
            "email": "jordan.ellis@example.local",
            "phone": "",
            "contact_type": ContactType.PUBLIC_HEALTH,
            "notes": "CHNA data cadence and homelessness prevalence workstream.",
        },
        {
            "first_name": "Sam",
            "last_name": "Nguyen",
            "organization": "NorthStar Health Alliance",
            "title": "Chief Informatics Officer",
            "email": "sam.nguyen@example.local",
            "phone": "",
            "contact_type": ContactType.HEALTH_SYSTEM,
            "notes": "OMOP network and federated analytics interest.",
        },
        {
            "first_name": "Riley",
            "last_name": "Patel",
            "organization": "University of Minnesota School of Public Health",
            "title": "Research Faculty",
            "email": "riley.patel@example.local",
            "phone": "",
            "contact_type": ContactType.RESEARCH,
            "notes": "Linked administrative data for incarceration and Medicaid.",
        },
        {
            "first_name": "Morgan",
            "last_name": "Lee",
            "organization": "Twin Cities Harm Reduction Coalition",
            "title": "Program Director",
            "email": "morgan.lee@example.local",
            "phone": "",
            "contact_type": ContactType.COMMUNITY,
            "notes": "Community advisory for equity framing on dashboards.",
        },
        {
            "first_name": "Casey",
            "last_name": "Brooks",
            "organization": "Minnesota Department of Health",
            "title": "Grants Officer",
            "email": "casey.brooks@example.local",
            "phone": "",
            "contact_type": ContactType.GOVERNMENT,
            "notes": "State infrastructure grant timelines.",
        },
        {
            "first_name": "Taylor",
            "last_name": "Morgan",
            "organization": "Robert Wood Johnson Foundation",
            "title": "Program Officer",
            "email": "taylor.morgan@example.local",
            "phone": "",
            "contact_type": ContactType.FUNDER,
            "notes": "Population health data modernization portfolio.",
        },
        {
            "first_name": "Alex",
            "last_name": "Rivera",
            "organization": "Independent Consultant",
            "title": "Managing Partner",
            "email": "alex.rivera@example.local",
            "phone": "",
            "contact_type": ContactType.OTHER,
            "notes": "Referral partner for rural health system engagements.",
        },
    ]


class Command(BaseCommand):
    help = (
        "Seed seven practice projects with tasks, subtasks, 11 events, and 7 contacts. "
        "Use --user for CTO (username or email) and optional --cspo for CSPO."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--user",
            required=True,
            help="Username or email for the CTO (technical lead).",
        )
        parser.add_argument(
            "--cspo",
            default="",
            help="Username or email for the Chief Strategy and Partnerships Officer. "
            "If omitted, all tasks are assigned to the CTO only (backward compatible).",
        )

    def handle(self, *args, **options):
        cto_user = _resolve_user(options["user"], label="CTO (--user)")
        cspo_raw = (options.get("cspo") or "").strip()
        cspo_user = _resolve_user(cspo_raw, label="CSPO (--cspo)") if cspo_raw else None

        stats = {
            "projects_created": 0,
            "tasks_created": 0,
            "subtasks_created": 0,
            "events_created": 0,
            "contacts_created": 0,
            "cto_task_assignments": 0,
            "cspo_task_assignments": 0,
            "shared_task_assignments": 0,
        }

        project_defs = _seed_project_definitions()
        event_defs = _seed_events(cto_user, cspo_user)
        contact_defs = _seed_contacts()

        for pdef in project_defs:
            name = pdef["name"]
            if Project.objects.filter(name=name).exists():
                self.stdout.write(self.style.WARNING(f'Skipping existing project "{name}".'))
                self._warn_missing_assignments_for_skipped_project(
                    name, pdef["tasks"], cto_user, cspo_user
                )
                continue

            project = Project.objects.create(
                name=name,
                description=pdef.get("description", ""),
                status=ProjectStatus.ACTIVE,
                priority=Priority.MEDIUM,
                owner=cto_user,
            )
            stats["projects_created"] += 1

            ProjectMembership.objects.get_or_create(
                project=project,
                user=cto_user,
                defaults={"role": MembershipRole.OWNER},
            )
            if cspo_user:
                ProjectMembership.objects.get_or_create(
                    project=project,
                    user=cspo_user,
                    defaults={"role": MembershipRole.ADMIN},
                )

            for tdef in pdef["tasks"]:
                stats.update(
                    self._create_task_tree(
                        project=project,
                        tdef=tdef,
                        parent=None,
                        created_by=cto_user,
                        cto_user=cto_user,
                        cspo_user=cspo_user,
                    )
                )

        # Events: idempotent on title + start (avoid duplicates on re-run)
        for ed in event_defs:
            exists = Event.objects.filter(
                title=ed["title"],
                start_datetime=ed["start_datetime"],
            ).exists()
            if exists:
                continue
            ev = Event.objects.create(
                title=ed["title"],
                description=ed["description"],
                event_type=ed["event_type"],
                project=None,
                task=None,
                start_datetime=ed["start_datetime"],
                end_datetime=ed["end_datetime"],
                all_day=ed["all_day"],
                created_by=ed["created_by"],
            )
            for u in ed["attendees"]:
                ev.attendees.add(u)
            stats["events_created"] += 1

        added_by = cspo_user if cspo_user else cto_user
        for cdef in contact_defs:
            if Contact.objects.filter(
                first_name=cdef["first_name"],
                last_name=cdef["last_name"],
                email=cdef["email"],
            ).exists():
                continue
            Contact.objects.create(**cdef, added_by=added_by)
            stats["contacts_created"] += 1

        self._print_summary(cto_user, cspo_user, stats)

    def _create_task_tree(
        self,
        *,
        project,
        tdef,
        parent,
        created_by,
        cto_user,
        cspo_user,
    ):
        stats = {"tasks_created": 0, "subtasks_created": 0, "cto_task_assignments": 0, "cspo_task_assignments": 0, "shared_task_assignments": 0}
        assign_key = tdef["assign"]
        task = Task.objects.create(
            project=project,
            parent_task=parent,
            title=tdef["title"],
            description="",
            status=TaskStatus.TODO if parent is None else TaskStatus.BACKLOG,
            priority=Priority.MEDIUM,
            created_by=created_by,
            order=0,
        )
        if parent is None:
            stats["tasks_created"] += 1
        else:
            stats["subtasks_created"] += 1

        self._apply_assignees_and_count(task, assign_key, cto_user, cspo_user, stats)

        for sub in tdef.get("subtasks") or []:
            if isinstance(sub, str):
                stdef = {"title": sub, "assign": assign_key, "subtasks": []}
            else:
                stdef = dict(sub)
                stdef.setdefault("assign", assign_key)
            sub_stats = self._create_task_tree(
                project=project,
                tdef=stdef,
                parent=task,
                created_by=created_by,
                cto_user=cto_user,
                cspo_user=cspo_user,
            )
            for k, v in sub_stats.items():
                stats[k] += v

        return stats

    def _apply_assignees_and_count(self, task, assign_key, cto_user, cspo_user, stats):
        users = _assignee_users(assign_key, cto_user, cspo_user)
        task._actor_id = cto_user.id
        for u in users:
            task.assignees.add(u)

        if assign_key == "both" and cspo_user:
            stats["shared_task_assignments"] += 1
        elif assign_key == "both":
            stats["cto_task_assignments"] += 1
        elif assign_key == "cto":
            stats["cto_task_assignments"] += 1
        elif assign_key == "cspo" and cspo_user:
            stats["cspo_task_assignments"] += 1
        else:
            stats["cto_task_assignments"] += 1

    def _warn_missing_assignments_for_skipped_project(
        self, project_name, task_defs, cto_user, cspo_user
    ):
        """If project was skipped, warn for each seed title not present (exact match)."""
        existing_titles = set(
            Task.objects.filter(project__name=project_name).values_list("title", flat=True)
        )
        for tdef in task_defs:
            self._warn_if_title_missing(project_name, tdef["title"], existing_titles)
            for sub in tdef.get("subtasks") or []:
                stitle = sub if isinstance(sub, str) else sub.get("title")
                if stitle:
                    self._warn_if_title_missing(project_name, stitle, existing_titles)

    def _warn_if_title_missing(self, project_name, title, existing_titles):
        if title not in existing_titles:
            logger.warning(
                'Seed assignment target not found (project skipped or title mismatch): '
                'project="%s" title="%s"',
                project_name,
                title,
            )
            self.stdout.write(
                self.style.WARNING(
                    f'Warning: task title not found for assignment context — '
                    f'project="{project_name}" title="{title}"'
                )
            )

    def _print_summary(self, cto_user, cspo_user, stats):
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("Seed summary"))
        self.stdout.write(f"Seeded Projects:          {stats['projects_created']}")
        self.stdout.write(f"Seeded Tasks:             {stats['tasks_created']}")
        self.stdout.write(f"Seeded Subtasks:          {stats['subtasks_created']}")
        self.stdout.write(f"Seeded Events:            {stats['events_created']}")
        self.stdout.write(f"Seeded Contacts:          {stats['contacts_created']}")
        self.stdout.write(f"CTO assigned to:          {cto_user.get_username()}")
        self.stdout.write(
            f"CSPO assigned to:         {cspo_user.get_username() if cspo_user else '(not provided — CTO only)'}"
        )
        self.stdout.write(f"CTO task count:           {stats['cto_task_assignments']}")
        self.stdout.write(f"CSPO task count:          {stats['cspo_task_assignments']}")
        self.stdout.write(f"Shared task count:        {stats['shared_task_assignments']}")
