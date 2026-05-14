"""
htac/management/commands/enrich_roster.py

Populate enrichment flags on DeduplicatedRoster from state staging tables.

Each source is independent and touches only its own fields, so individual
sources can be re-run without disturbing flags set by other sources.

Sources
-------
  medicaid  → MedicaidEnrollment  → medicaid_flag, medicaid_effective_date
  hmis      → HMISRecord          → homeless_flag, homeless_first_service_date
  doc       → DOCRecord           → jail_flag, jail_admission_date,
                                     prison_flag, prison_admission_date
  miic      → MIICRecord          → covid_vaccinated_flag, covid_vaccine_date,
                                     influenza_vaccinated_flag
  vitals    → VitalStatisticsRecord → deceased_flag, death_date

USAGE
-----
  python manage.py enrich_roster                    # all sources
  python manage.py enrich_roster --source medicaid
  python manage.py enrich_roster --source doc miic
  python manage.py enrich_roster --source all --dry-run
  python manage.py enrich_roster --verbosity 2      # timing per source
"""

import datetime

from django.core.management.base import BaseCommand, CommandError

from htac.services.enrichment import (
    enrich_from_doc,
    enrich_from_hmis,
    enrich_from_medicaid,
    enrich_from_miic,
    enrich_from_vitals,
)

_SOURCE_MAP = {
    "medicaid": enrich_from_medicaid,
    "hmis":     enrich_from_hmis,
    "doc":      enrich_from_doc,
    "miic":     enrich_from_miic,
    "vitals":   enrich_from_vitals,
}

_ALL_SOURCES = list(_SOURCE_MAP.keys())


class Command(BaseCommand):
    help = (
        "Populate enrichment flags on DeduplicatedRoster from state staging tables. "
        "Each source only touches its own fields. Idempotent."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--source",
            nargs="+",
            metavar="SOURCE",
            default=["all"],
            choices=[*_ALL_SOURCES, "all"],
            help=(
                "One or more sources to enrich from, or 'all' (default). "
                f"Choices: {', '.join([*_ALL_SOURCES, 'all'])}"
            ),
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help=(
                "Count how many roster records would be matched per source "
                "without writing any flag changes."
            ),
        )

    def handle(self, *args, **options):
        requested: list[str] = options["source"]
        dry_run: bool        = options["dry_run"]
        verbosity: int       = options["verbosity"]

        # Expand 'all' to the canonical source order
        sources = _ALL_SOURCES if "all" in requested else requested

        if dry_run:
            self.stdout.write(self.style.WARNING("[DRY RUN] No data will be written.\n"))

        from htac.models import DeduplicatedRoster

        roster_qs   = DeduplicatedRoster.objects.all()
        roster_count = roster_qs.count()

        if roster_count == 0:
            self.stdout.write(
                self.style.WARNING(
                    "No DeduplicatedRoster records found. "
                    "Run run_pprl_deduplication first."
                )
            )
            return

        self.stdout.write(
            f"Roster size : {roster_count} records\n"
            f"Sources     : {', '.join(sources)}\n"
        )

        total_matched = 0

        for source_name in sources:
            fn = _SOURCE_MAP[source_name]

            if dry_run:
                matched = _dry_run_count(source_name, roster_qs)
                self.stdout.write(
                    f"  [DRY RUN] {source_name:<10} "
                    f"{matched:>6} roster records would be flagged "
                    f"({roster_count - matched} would be cleared)"
                )
                total_matched += matched
                continue

            t0 = datetime.datetime.now()
            matched = fn(roster_qs)
            elapsed = (datetime.datetime.now() - t0).total_seconds()

            line = (
                f"  {source_name:<10} "
                f"{matched:>6} matched  /  {roster_count - matched:>6} cleared"
            )
            if verbosity >= 2:
                line += f"  ({elapsed:.2f}s)"
            self.stdout.write(line)
            total_matched += matched

        # ── Summary ───────────────────────────────────────────────────────────
        prefix = "[DRY RUN] " if dry_run else ""
        self.stdout.write(
            self.style.SUCCESS(
                f"\n{prefix}Done — {total_matched} flag-sets matched across "
                f"{len(sources)} source(s)."
            )
        )

        if verbosity >= 2 and not dry_run:
            _print_flag_summary(self, roster_qs)


# ── Dry-run helpers ───────────────────────────────────────────────────────────

def _dry_run_count(source_name: str, roster_qs) -> int:
    """
    Count how many canonical tokens in *roster_qs* appear in the source's
    staging table.  Two DB queries; no writes.
    """
    from htac.models import (
        DOCRecord, HMISRecord, MedicaidEnrollment, MIICRecord,
        VitalStatisticsRecord,
    )

    _staging = {
        "medicaid": MedicaidEnrollment,
        "hmis":     HMISRecord,
        "doc":      DOCRecord,
        "miic":     MIICRecord,
        "vitals":   VitalStatisticsRecord,
    }

    tokens = list(roster_qs.values_list("canonical_token", flat=True))
    staging_model = _staging[source_name]

    return (
        staging_model.objects
        .filter(token_hash__in=tokens)
        .values("token_hash")
        .distinct()
        .count()
    )


def _print_flag_summary(cmd, roster_qs) -> None:
    """Print a flag-population summary table at --verbosity 2."""
    fields = [
        ("medicaid_flag",          "Medicaid"),
        ("homeless_flag",          "Homeless"),
        ("jail_flag",              "Jail"),
        ("prison_flag",            "Prison"),
        ("covid_vaccinated_flag",  "COVID vax"),
        ("influenza_vaccinated_flag", "Flu vax"),
        ("deceased_flag",          "Deceased"),
    ]
    total = roster_qs.count()
    cmd.stdout.write("\nFlag population summary:")
    for field, label in fields:
        n = roster_qs.filter(**{field: True}).count()
        pct = n / total * 100 if total else 0
        cmd.stdout.write(f"  {label:<22} {n:>6}  ({pct:5.1f}%)")
