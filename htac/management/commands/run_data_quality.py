"""
htac/management/commands/run_data_quality.py

Compute per-site data quality metrics and write DataQualityReport rows.

Metrics
-------
  total_persons               — total Person records at the site
  total_visits                — total VisitOccurrence records
  total_condition_occurrences — total ConditionOccurrence records
  pct_persons_with_condition  — % of persons with ≥ 1 ConditionOccurrence
  pct_valid_zip               — % of persons with a non-empty zip_code
  pct_race_populated          — % of persons with race_concept_id ≠ 0
  pct_ethnicity_populated     — % of persons with ethnicity_concept_id ≠ 0

Flag thresholds
---------------
  Metric                       pass       warn        fail
  total_persons                ≥ 10       1–9         0
  total_visits                 ≥ 10       1–9         0
  total_condition_occurrences  ≥ 1        —           0
  pct_persons_with_condition   ≥ 10 %     1–10 %      < 1 %
  pct_valid_zip                ≥ 80 %     50–80 %     < 50 %
  pct_race_populated           ≥ 80 %     50–80 %     < 50 %
  pct_ethnicity_populated      ≥ 80 %     50–80 %     < 50 %

Idempotent: existing DataQualityReport rows for the same (health_system,
run_date) are deleted before new ones are written.

USAGE
-----
  python manage.py run_data_quality
  python manage.py run_data_quality --site ALLINA
  python manage.py run_data_quality --run-date 2024-01-15
  python manage.py run_data_quality --dry-run
  python manage.py run_data_quality --verbosity 2   # per-metric detail
"""

import datetime
from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db.models import Count, Q

from htac.models import (
    ConditionOccurrence,
    DataQualityReport,
    HealthSystem,
    Person,
    VisitOccurrence,
)

# ── Metric definitions ────────────────────────────────────────────────────────
# (name, warn_threshold, fail_threshold)
# Percentage metrics stored as 0–100 Decimal values.
# Count metrics stored as raw integers (as Decimal for the model field).

_METRICS: list[tuple[str, float, float]] = [
    ("total_persons",                10.0,  1.0),
    ("total_visits",                 10.0,  1.0),
    ("total_condition_occurrences",   1.0,  0.0),   # warn == fail == 1/0
    ("pct_persons_with_condition",   10.0,  1.0),
    ("pct_valid_zip",                80.0, 50.0),
    ("pct_race_populated",           80.0, 50.0),
    ("pct_ethnicity_populated",      80.0, 50.0),
]

_WARN_THRESHOLD = {name: warn for name, warn, _ in _METRICS}
_FAIL_THRESHOLD = {name: fail for name, _, fail in _METRICS}


def _flag(metric_name: str, value: float) -> str:
    if value < _FAIL_THRESHOLD[metric_name]:
        return "fail"
    if value < _WARN_THRESHOLD[metric_name]:
        return "warn"
    return "pass"


# ── Command ───────────────────────────────────────────────────────────────────

class Command(BaseCommand):
    help = (
        "Compute per-site data quality metrics and write DataQualityReport rows. "
        "Idempotent."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--site",
            metavar="SHORT_CODE",
            help="Limit to one HealthSystem. If omitted, all active sites are processed.",
        )
        parser.add_argument(
            "--run-date",
            metavar="YYYY-MM-DD",
            help="Report date to stamp on rows. Defaults to today.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Compute and display metrics without writing to the database.",
        )

    def handle(self, *args, **options):
        dry_run: bool  = options["dry_run"]
        verbosity: int = options["verbosity"]

        if dry_run:
            self.stdout.write(self.style.WARNING("[DRY RUN] No data will be written.\n"))

        # ── Run date ──────────────────────────────────────────────────────────
        raw_date = options.get("run_date")
        try:
            run_date = (
                datetime.date.fromisoformat(raw_date)
                if raw_date
                else datetime.date.today()
            )
        except ValueError:
            raise CommandError(
                f"Invalid --run-date '{raw_date}'. Use YYYY-MM-DD format."
            )

        # ── Health systems ────────────────────────────────────────────────────
        hs_qs = HealthSystem.objects.filter(is_active=True)
        if options["site"]:
            hs_qs = hs_qs.filter(short_code=options["site"])
            if not hs_qs.exists():
                raise CommandError(
                    f"No active HealthSystem with short_code='{options['site']}'."
                )

        health_systems = list(hs_qs.order_by("name"))
        self.stdout.write(
            f"Run date : {run_date}\n"
            f"Sites    : {len(health_systems)}\n"
        )

        all_rows: list[DataQualityReport] = []
        site_summaries: list[dict] = []

        for hs in health_systems:
            metrics = _compute_metrics(hs)
            rows = []
            flags = []

            for metric_name, value in metrics.items():
                flag = _flag(metric_name, float(value))
                flags.append(flag)
                rows.append(DataQualityReport(
                    health_system=hs,
                    run_date=run_date,
                    metric_name=metric_name,
                    metric_value=Decimal(str(value)),
                    flag=flag,
                    threshold=Decimal(str(_WARN_THRESHOLD[metric_name])),
                ))

            all_rows.extend(rows)

            # Worst flag for this site
            worst = "fail" if "fail" in flags else ("warn" if "warn" in flags else "pass")
            site_summaries.append({"hs": hs, "rows": rows, "worst": worst})

        # ── Output summary ────────────────────────────────────────────────────
        for summary in site_summaries:
            hs    = summary["hs"]
            worst = summary["worst"]
            style_fn = {
                "pass": self.style.SUCCESS,
                "warn": self.style.WARNING,
                "fail": self.style.ERROR,
            }[worst]

            self.stdout.write(
                style_fn(f"  {hs.short_code:<24} [{worst.upper()}]")
            )

            if verbosity >= 2:
                for row in summary["rows"]:
                    flag_str = {
                        "pass": "PASS",
                        "warn": "WARN",
                        "fail": "FAIL",
                    }[row.flag]
                    self.stdout.write(
                        f"    {row.metric_name:<35} "
                        f"{float(row.metric_value):>10.2f}  "
                        f"[{flag_str}]  (warn<{float(row.threshold):.1f})"
                    )

        if dry_run:
            total_warn = sum(1 for s in site_summaries if s["worst"] == "warn")
            total_fail = sum(1 for s in site_summaries if s["worst"] == "fail")
            self.stdout.write(
                self.style.WARNING(
                    f"\n[DRY RUN] Would write {len(all_rows)} DataQualityReport rows. "
                    f"Sites: {len(health_systems) - total_warn - total_fail} pass, "
                    f"{total_warn} warn, {total_fail} fail."
                )
            )
            return

        # ── Write ─────────────────────────────────────────────────────────────
        # Delete stale rows for the same (site, run_date) combos being written
        hs_ids = [s["hs"].pk for s in site_summaries]
        deleted, _ = DataQualityReport.objects.filter(
            health_system_id__in=hs_ids,
            run_date=run_date,
        ).delete()
        if deleted and verbosity >= 1:
            self.stdout.write(f"Cleared {deleted} stale rows for {run_date}.")

        DataQualityReport.objects.bulk_create(all_rows, batch_size=200)

        total_warn = sum(1 for s in site_summaries if s["worst"] == "warn")
        total_fail = sum(1 for s in site_summaries if s["worst"] == "fail")
        msg = (
            f"\nDone — {len(all_rows)} rows written across {len(health_systems)} sites.  "
            f"Pass: {len(health_systems) - total_warn - total_fail}  "
            f"Warn: {total_warn}  Fail: {total_fail}"
        )
        style_fn = self.style.ERROR if total_fail else (
            self.style.WARNING if total_warn else self.style.SUCCESS
        )
        self.stdout.write(style_fn(msg))


# ── Metric computation ────────────────────────────────────────────────────────

def _compute_metrics(health_system: HealthSystem) -> dict[str, float]:
    """
    Return {metric_name: float_value} for all defined metrics at one site.
    Uses four DB queries regardless of person count.
    """
    # Query 1: person aggregates
    person_agg = Person.objects.filter(health_system=health_system).aggregate(
        total=Count("id"),
        valid_zip=Count("id", filter=Q(zip_code__gt="")),
        race_ok=Count("id", filter=Q(race_concept_id__gt=0)),
        eth_ok=Count("id", filter=Q(ethnicity_concept_id__gt=0)),
    )
    total = person_agg["total"]

    def pct(numerator: int) -> float:
        return round(numerator / total * 100, 4) if total > 0 else 0.0

    # Query 2: visit count
    total_visits = VisitOccurrence.objects.filter(
        health_system=health_system
    ).count()

    # Query 3: condition occurrence count
    total_co = ConditionOccurrence.objects.filter(
        health_system=health_system
    ).count()

    # Query 4: persons with ≥ 1 condition occurrence (distinct person IDs)
    persons_with_cond = (
        ConditionOccurrence.objects
        .filter(health_system=health_system)
        .values("person_id")
        .distinct()
        .count()
    )

    return {
        "total_persons":               float(total),
        "total_visits":                float(total_visits),
        "total_condition_occurrences": float(total_co),
        "pct_persons_with_condition":  pct(persons_with_cond),
        "pct_valid_zip":               pct(person_agg["valid_zip"]),
        "pct_race_populated":          pct(person_agg["race_ok"]),
        "pct_ethnicity_populated":     pct(person_agg["eth_ok"]),
    }
