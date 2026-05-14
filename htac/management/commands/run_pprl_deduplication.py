"""
htac/management/commands/run_pprl_deduplication.py

Cross-site PPRL deduplication.

Reads all HashToken records, matches tokens that appear at more than one
HealthSystem, and writes (or updates) one DeduplicatedRoster row per unique
token.  Single-site tokens also get a roster row (site_count=1).

Canonical site selection: the HealthSystem whose Person had the most recent
VisitOccurrence across all persons sharing that token.  If no visits exist,
the first site found is used.

The operation is fully idempotent — re-running produces the same roster
state for the same underlying HashToken data.  Enrichment flags on existing
roster rows are left untouched; run `enrich_roster` separately to populate
or refresh them.

USAGE
-----
  python manage.py run_pprl_deduplication
  python manage.py run_pprl_deduplication --dry-run
  python manage.py run_pprl_deduplication --verbosity 2   # per-token detail
"""

import datetime

from django.core.management.base import BaseCommand, CommandError
from django.db.models import Count


class Command(BaseCommand):
    help = (
        "Match HashToken records across sites and populate DeduplicatedRoster. "
        "Idempotent — safe to re-run."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help=(
                "Analyse token overlap and report what would be written "
                "without touching the database."
            ),
        )

    def handle(self, *args, **options):
        dry_run: bool = options["dry_run"]
        verbosity: int = options["verbosity"]

        if dry_run:
            self.stdout.write(self.style.WARNING("[DRY RUN] No data will be written.\n"))

        from htac.models import DeduplicatedRoster, HashToken
        from htac.services.pprl import deduplicate_tokens

        # ── Pre-flight summary ────────────────────────────────────────────────
        total_token_rows = HashToken.objects.count()

        if total_token_rows == 0:
            self.stdout.write(
                self.style.WARNING(
                    "No HashToken records found. "
                    "Run generate_hash_tokens first."
                )
            )
            return

        token_stats = (
            HashToken.objects
            .values("token")
            .annotate(site_count=Count("health_system", distinct=True))
            .order_by()
        )

        distinct_tokens  = token_stats.count()
        multi_site_count = token_stats.filter(site_count__gt=1).count()
        single_site_count = distinct_tokens - multi_site_count

        self.stdout.write(
            f"HashToken rows       : {total_token_rows}\n"
            f"Distinct token values: {distinct_tokens}\n"
            f"  → single-site      : {single_site_count}\n"
            f"  → multi-site (dups): {multi_site_count}"
        )

        if verbosity >= 2 and multi_site_count:
            self.stdout.write("\nMulti-site token breakdown:")
            for row in token_stats.filter(site_count__gt=1).order_by("-site_count")[:20]:
                self.stdout.write(
                    f"  {row['token'][:12]}…  sites={row['site_count']}"
                )
            if multi_site_count > 20:
                self.stdout.write(f"  … and {multi_site_count - 20} more.")

        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f"\n[DRY RUN] Would upsert {distinct_tokens} DeduplicatedRoster rows "
                    f"({multi_site_count} merged, {single_site_count} single-site)."
                )
            )
            return

        # ── Run deduplication ─────────────────────────────────────────────────
        self.stdout.write("\nRunning deduplication…")
        started_at = datetime.datetime.now()

        qs = HashToken.objects.all()
        upserted = deduplicate_tokens(qs)

        elapsed = (datetime.datetime.now() - started_at).total_seconds()

        # ── Post-run stats ────────────────────────────────────────────────────
        merged = DeduplicatedRoster.objects.filter(site_count__gt=1).count()
        single = DeduplicatedRoster.objects.filter(site_count=1).count()

        self.stdout.write(
            self.style.SUCCESS(
                f"Done ({elapsed:.1f}s) — "
                f"{upserted} roster rows upserted "
                f"({merged} multi-site, {single} single-site)."
            )
        )

        if verbosity >= 2:
            self.stdout.write("\nTop canonical sites by roster count:")
            from htac.models import HealthSystem
            for hs in (
                HealthSystem.objects
                .annotate(roster_count=Count("canonical_roster_entries"))
                .order_by("-roster_count")[:11]
            ):
                self.stdout.write(f"  {hs.short_code:<20} {hs.roster_count}")
