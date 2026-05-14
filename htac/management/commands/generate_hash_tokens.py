"""
htac/management/commands/generate_hash_tokens.py

Read a PII CSV (from file or stdin), compute a SHA-256 token for each row,
and write the token to the HashToken table.

PRIVACY CONTRACT
----------------
- The six PII fields (first_name, last_name, dob, sex, phone, zip_code) are
  read from the CSV row into local variables ONLY.
- They are passed to compute_token() and then immediately deleted from the
  local namespace with `del`.
- They are NEVER written to the database, logged, or included in any output.
- Only the resulting 64-char hex digest is persisted (in HashToken.token).

CSV FORMAT
----------
Required columns (header row must use these exact names):
  person_source_value  — site-internal patient ID matching Person.person_source_value
  first_name
  last_name
  dob                  — date of birth: YYYYMMDD or YYYY-MM-DD or MM/DD/YYYY
  sex                  — first character used: M / F / U
  phone                — any format; only digits are hashed
  zip_code             — any format; first 5 characters are hashed

Optional column:
  site                 — HealthSystem.short_code; required if --site is not given

USAGE EXAMPLES
--------------
  # Process one site from a file
  python manage.py generate_hash_tokens --site ALLINA --input patients.csv

  # Process one site from stdin (no file on disk)
  python manage.py generate_hash_tokens --site ALLINA < patients.csv

  # Process multiple sites (CSV must include a 'site' column)
  python manage.py generate_hash_tokens --input all_sites.csv

  # Validate without writing
  python manage.py generate_hash_tokens --site ALLINA --input patients.csv --dry-run
"""

import csv
import sys
from io import TextIOWrapper

from django.core.management.base import BaseCommand, CommandError

from htac.models import HashToken, HealthSystem, Person
from htac.services.pprl import compute_token

_REQUIRED_COLUMNS = {
    "person_source_value",
    "first_name",
    "last_name",
    "dob",
    "sex",
    "phone",
    "zip_code",
}


class Command(BaseCommand):
    help = (
        "Generate SHA-256 PPRL tokens from a PII CSV and write to HashToken. "
        "PII is used transiently and never persisted."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--site",
            metavar="SHORT_CODE",
            help=(
                "HealthSystem.short_code to process. If omitted, the CSV "
                "must include a 'site' column."
            ),
        )
        parser.add_argument(
            "--input",
            metavar="FILE",
            default="-",
            help="Path to PII CSV. Use '-' or omit to read from stdin (default: stdin).",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Parse and validate without writing to the database.",
        )

    def handle(self, *args, **options):
        site_code: str | None = options["site"]
        input_path: str = options["input"]
        dry_run: bool = options["dry_run"]

        if dry_run:
            self.stdout.write(self.style.WARNING("[DRY RUN] No data will be written."))

        # Pre-load health system map (avoid per-row DB hits)
        if site_code:
            try:
                hs = HealthSystem.objects.get(short_code=site_code)
            except HealthSystem.DoesNotExist:
                raise CommandError(
                    f"HealthSystem with short_code '{site_code}' does not exist."
                )
            site_map = {site_code: hs}
        else:
            site_map = {hs.short_code: hs for hs in HealthSystem.objects.all()}

        if input_path == "-":
            # Wrap binary stdin so csv.DictReader gets text
            stream = TextIOWrapper(sys.stdin.buffer, encoding="utf-8", newline="")
            self._process(stream, site_map, site_code, dry_run)
        else:
            try:
                with open(input_path, newline="", encoding="utf-8") as fh:
                    self._process(fh, site_map, site_code, dry_run)
            except FileNotFoundError:
                raise CommandError(f"Input file not found: {input_path}")

    # ── Core processing ───────────────────────────────────────────────────────

    def _process(self, stream, site_map: dict, default_site_code: str | None, dry_run: bool):
        reader = csv.DictReader(stream)

        # Validate header row before touching any data
        if reader.fieldnames is None:
            raise CommandError("CSV appears to be empty — no header row found.")

        fieldnames = set(reader.fieldnames)
        missing = _REQUIRED_COLUMNS - fieldnames
        if missing:
            raise CommandError(
                f"CSV is missing required column(s): {', '.join(sorted(missing))}"
            )

        has_site_column = "site" in fieldnames
        if not default_site_code and not has_site_column:
            raise CommandError(
                "No --site flag provided and CSV has no 'site' column. "
                "Provide one or the other."
            )

        created = updated = skipped = errors = 0

        for row_num, row in enumerate(reader, start=2):
            # ── Resolve health system ─────────────────────────────────────────
            raw_site = (row.get("site") or "").strip() or default_site_code
            health_system = site_map.get(raw_site)
            if health_system is None:
                self.stderr.write(
                    f"Row {row_num}: unknown site '{raw_site}' — skipping."
                )
                errors += 1
                continue

            # ── Extract and validate fields ───────────────────────────────────
            person_source_value = row["person_source_value"].strip()

            # PII — stored in local variables only; deleted after token is derived
            first_name = row["first_name"].strip()
            last_name  = row["last_name"].strip()
            dob        = row["dob"].strip()
            sex        = row["sex"].strip()
            phone      = row["phone"].strip()
            zip_code   = row["zip_code"].strip()

            if not all([person_source_value, first_name, last_name, dob, sex]):
                self.stderr.write(
                    f"Row {row_num}: one or more required fields are blank — skipping."
                )
                # Discard PII before continuing
                del first_name, last_name, dob, sex, phone, zip_code
                errors += 1
                continue

            # ── Resolve Person record ─────────────────────────────────────────
            try:
                person = Person.objects.get(
                    health_system=health_system,
                    person_source_value=person_source_value,
                )
            except Person.DoesNotExist:
                self.stderr.write(
                    f"Row {row_num}: Person '{person_source_value}' not found at "
                    f"'{raw_site}' — skipping."
                )
                del first_name, last_name, dob, sex, phone, zip_code
                skipped += 1
                continue

            # ── Compute token — PII used here and immediately discarded ────────
            try:
                token = compute_token(first_name, last_name, dob, sex, phone, zip_code)
            except Exception as exc:
                self.stderr.write(
                    f"Row {row_num}: token computation failed ({exc}) — skipping."
                )
                del first_name, last_name, dob, sex, phone, zip_code
                errors += 1
                continue
            finally:
                # Unconditional PII deletion — runs even if compute_token raised
                del first_name, last_name, dob, sex, phone, zip_code

            # ── Write (or preview) ────────────────────────────────────────────
            if dry_run:
                self.stdout.write(
                    f"[DRY RUN] Row {row_num}: site={raw_site} "
                    f"person={person.id} → token={token[:8]}…"
                )
                del token
                created += 1  # count as "would create/update"
                continue

            try:
                _, was_created = HashToken.objects.update_or_create(
                    person=person,
                    health_system=health_system,
                    defaults={"token": token},
                )
            except Exception as exc:
                self.stderr.write(
                    f"Row {row_num}: DB write failed ({exc}) — skipping."
                )
                del token
                errors += 1
                continue

            del token   # discard token after write is confirmed

            if was_created:
                created += 1
            else:
                updated += 1

        # ── Summary ──────────────────────────────────────────────────────────
        prefix = "[DRY RUN] " if dry_run else ""
        msg = (
            f"{prefix}Complete — "
            f"created: {created}, updated: {updated}, "
            f"skipped: {skipped}, errors: {errors}"
        )
        if errors:
            self.stdout.write(self.style.WARNING(msg))
        else:
            self.stdout.write(self.style.SUCCESS(msg))
