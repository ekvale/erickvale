"""
htac/management/commands/execute_condition_queries.py

Run condition prevalence queries for a StudyRun and write PrevalenceEstimate rows.

For every (Condition × HealthSystem × geo_level × geo_value × stratifier) cell:
  1. Call get_condition_cohort()  → Person queryset meeting codeset criteria
  2. Call stratify_cohort()       → {stratum: {numerator, denominator}}
  3. Call apply_suppression()     → adds prevalence_rate, nulls cells where n < 11
  4. Bulk-create PrevalenceEstimate rows

After all sites are processed, statewide (health_system=None) estimates are
derived by summing non-suppressed site cells and re-applying suppression.

The command is idempotent: existing estimates for the StudyRun (and optional
condition filter) are deleted before new ones are written.

Study period
------------
Clinical events are filtered to [--start-date, --end-date].  If omitted,
defaults to the calendar year ending on the StudyRun's run_date.

USAGE
-----
  python manage.py execute_condition_queries --study-run-id 1
  python manage.py execute_condition_queries --study-run-id 1 --condition diabetes hypertension
  python manage.py execute_condition_queries --study-run-id 1 --start-date 2022-01-01 --end-date 2022-12-31
  python manage.py execute_condition_queries --study-run-id 1 --dry-run
"""

import datetime
from collections import defaultdict

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from htac.models import (
    DeduplicatedRoster,
    HealthSystem,
    Person,
    PrevalenceEstimate,
    StudyRun,
)
from htac.services.query_engine import (
    apply_suppression,
    get_condition_cohort,
    stratify_cohort,
)

STRATIFIERS = [
    "total",
    "race",
    "ethnicity",
    "language",
    "sex",
    "age_group",
    "homeless",
    "incarceration",
    "medicaid",
]

# (geo_level, person_field_for_grouping)  — None field = no filter (state level)
GEO_LEVELS = [
    ("state",        None),
    ("county",       "county_fips"),
    ("zip",          "zip_code"),
    ("census_tract", "census_tract"),
]


class Command(BaseCommand):
    help = (
        "Execute condition prevalence queries for a StudyRun and write "
        "PrevalenceEstimate records. Idempotent."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--study-run-id",
            type=int,
            required=True,
            metavar="ID",
            help="Primary key of the StudyRun to execute.",
        )
        parser.add_argument(
            "--condition",
            nargs="*",
            metavar="SLUG",
            default=[],
            help=(
                "One or more condition slugs to process. "
                "If omitted, all conditions in the StudyRun are processed."
            ),
        )
        parser.add_argument(
            "--start-date",
            metavar="YYYY-MM-DD",
            help=(
                "Start of the clinical data study period (inclusive). "
                "Defaults to Jan 1 of the year before run_date."
            ),
        )
        parser.add_argument(
            "--end-date",
            metavar="YYYY-MM-DD",
            help=(
                "End of the clinical data study period (inclusive). "
                "Defaults to Dec 31 of the year before run_date."
            ),
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Report expected estimate counts without writing to the database.",
        )

    # ── Entry point ───────────────────────────────────────────────────────────

    def handle(self, *args, **options):
        dry_run: bool = options["dry_run"]
        verbosity: int = options["verbosity"]

        if dry_run:
            self.stdout.write(self.style.WARNING("[DRY RUN] No data will be written.\n"))

        # ── Resolve StudyRun ──────────────────────────────────────────────────
        try:
            study_run = StudyRun.objects.get(pk=options["study_run_id"])
        except StudyRun.DoesNotExist:
            raise CommandError(
                f"StudyRun with id={options['study_run_id']} does not exist."
            )

        if study_run.status == "running" and not dry_run:
            raise CommandError(
                f"StudyRun '{study_run.name}' is already running. "
                "Wait for it to finish or mark it failed before re-running."
            )

        # ── Resolve conditions ────────────────────────────────────────────────
        conditions_qs = study_run.conditions.filter(is_active=True)
        if options["condition"]:
            conditions_qs = conditions_qs.filter(slug__in=options["condition"])
        conditions = list(conditions_qs)

        if not conditions:
            raise CommandError("No active conditions found for this StudyRun.")

        # ── Resolve study period ──────────────────────────────────────────────
        study_period = _resolve_study_period(
            options["start_date"], options["end_date"], study_run.run_date
        )
        self.stdout.write(
            f"StudyRun    : [{study_run.pk}] {study_run.name}\n"
            f"Conditions  : {len(conditions)}\n"
            f"Study period: {study_period[0]} → {study_period[1]}\n"
            f"Dry run     : {dry_run}\n"
        )

        # ── Execute ───────────────────────────────────────────────────────────
        health_systems = list(HealthSystem.objects.filter(is_active=True))

        if not dry_run:
            study_run.status = "running"
            study_run.save(update_fields=["status"])

        try:
            estimates, stats = self._build_estimates(
                study_run, conditions, health_systems, study_period, dry_run, verbosity
            )

            if dry_run:
                self.stdout.write(
                    self.style.WARNING(
                        f"\n[DRY RUN] Would write {len(estimates)} PrevalenceEstimate rows "
                        f"({stats['suppressed']} suppressed)."
                    )
                )
                return

            # Delete stale rows and bulk-insert in one transaction
            with transaction.atomic():
                deleted_qs = PrevalenceEstimate.objects.filter(study_run=study_run)
                if options["condition"]:
                    deleted_qs = deleted_qs.filter(
                        condition__slug__in=options["condition"]
                    )
                n_deleted, _ = deleted_qs.delete()
                if n_deleted and verbosity >= 1:
                    self.stdout.write(f"Cleared {n_deleted} stale estimates.")

                PrevalenceEstimate.objects.bulk_create(estimates, batch_size=500)

            study_run.status = "complete"
            study_run.save(update_fields=["status"])

            self.stdout.write(
                self.style.SUCCESS(
                    f"Done — {len(estimates)} rows written "
                    f"({stats['suppressed']} suppressed, "
                    f"{stats['statewide']} statewide)."
                )
            )

        except Exception:
            if not dry_run:
                study_run.status = "failed"
                study_run.save(update_fields=["status"])
            raise

    # ── Core builder ─────────────────────────────────────────────────────────

    def _build_estimates(
        self, study_run, conditions, health_systems, study_period, dry_run, verbosity
    ):
        estimates = []
        stats = {"suppressed": 0, "statewide": 0}

        for condition in conditions:
            if verbosity >= 1:
                self.stdout.write(f"  Condition: {condition.name}")

            # Accumulate statewide counts across sites (state geo only)
            # {stratifier: {stratum_val: {numerator, denominator}}}
            statewide: dict = defaultdict(lambda: defaultdict(lambda: {"numerator": 0, "denominator": 0}))

            for health_system in health_systems:
                cohort_qs = get_condition_cohort(
                    condition, health_system, study_period
                )
                roster_qs = DeduplicatedRoster.objects.filter(
                    canonical_site=health_system
                )

                site_estimates, site_stats = _build_site_estimates(
                    study_run, condition, health_system,
                    cohort_qs, roster_qs, statewide,
                )
                estimates.extend(site_estimates)
                stats["suppressed"] += site_stats["suppressed"]

                if verbosity >= 2:
                    self.stdout.write(
                        f"    {health_system.short_code:<20} "
                        f"cohort={cohort_qs.count():>4}  "
                        f"estimates={len(site_estimates):>4}"
                    )

            # Statewide estimates (health_system=None, geo_level='state')
            sw_rows = _build_statewide_estimates(study_run, condition, statewide)
            estimates.extend(sw_rows)
            stats["suppressed"] += sum(1 for e in sw_rows if e.is_suppressed)
            stats["statewide"] += len(sw_rows)

        return estimates, stats


# ── Site-level estimate builder ───────────────────────────────────────────────

def _build_site_estimates(
    study_run, condition, health_system,
    cohort_qs, roster_qs, statewide_accumulator,
):
    rows = []
    stats = {"suppressed": 0}

    for geo_level, geo_field in GEO_LEVELS:
        # Determine (geo_value, filtered_cohort) pairs for this geo level
        if geo_field is None:
            geo_pairs = [(None, cohort_qs)]
        else:
            geo_vals = (
                Person.objects
                .filter(health_system=health_system)
                .exclude(**{f"{geo_field}__exact": ""})
                .values_list(geo_field, flat=True)
                .distinct()
            )
            geo_pairs = [
                (val, cohort_qs.filter(**{geo_field: val}))
                for val in geo_vals
            ]

        for geo_value, filtered_cohort in geo_pairs:
            for stratifier in STRATIFIERS:
                raw = stratify_cohort(filtered_cohort, stratifier, roster_qs)
                if not raw:
                    continue

                suppressed = apply_suppression(raw)

                for stratum_val, cell in suppressed.items():
                    rows.append(PrevalenceEstimate(
                        study_run=study_run,
                        condition=condition,
                        health_system=health_system,
                        geo_level=geo_level,
                        geo_value=geo_value,
                        stratifier=stratifier,
                        stratifier_value=stratum_val,
                        numerator=cell["numerator"],
                        denominator=cell["denominator"],
                        prevalence_rate=cell["prevalence_rate"],
                        is_suppressed=cell["is_suppressed"],
                    ))
                    if cell["is_suppressed"]:
                        stats["suppressed"] += 1

                    # Accumulate into statewide totals (state geo, non-suppressed only)
                    if geo_level == "state" and not cell["is_suppressed"]:
                        bucket = statewide_accumulator[stratifier][stratum_val]
                        bucket["numerator"]   += cell["numerator"]
                        bucket["denominator"] += cell["denominator"]

    return rows, stats


# ── Statewide estimate builder ────────────────────────────────────────────────

def _build_statewide_estimates(study_run, condition, statewide_accumulator):
    rows = []
    for stratifier, strata in statewide_accumulator.items():
        raw = {
            val: {"numerator": counts["numerator"], "denominator": counts["denominator"]}
            for val, counts in strata.items()
        }
        suppressed = apply_suppression(raw)
        for stratum_val, cell in suppressed.items():
            rows.append(PrevalenceEstimate(
                study_run=study_run,
                condition=condition,
                health_system=None,      # null = statewide
                geo_level="state",
                geo_value=None,
                stratifier=stratifier,
                stratifier_value=stratum_val,
                numerator=cell["numerator"],
                denominator=cell["denominator"],
                prevalence_rate=cell["prevalence_rate"],
                is_suppressed=cell["is_suppressed"],
            ))
    return rows


# ── Helpers ───────────────────────────────────────────────────────────────────

def _resolve_study_period(
    start_raw: str | None,
    end_raw: str | None,
    run_date: datetime.date,
) -> tuple[datetime.date, datetime.date]:
    """
    Parse --start-date / --end-date or derive defaults from run_date.
    Default: calendar year ending on Dec 31 of the year before run_date.
    """
    try:
        start = (
            datetime.date.fromisoformat(start_raw)
            if start_raw
            else datetime.date(run_date.year - 1, 1, 1)
        )
        end = (
            datetime.date.fromisoformat(end_raw)
            if end_raw
            else datetime.date(run_date.year - 1, 12, 31)
        )
    except ValueError as exc:
        raise CommandError(f"Invalid date: {exc}")

    if start > end:
        raise CommandError(
            f"--start-date ({start}) must be before --end-date ({end})."
        )
    return start, end
