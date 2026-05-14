"""
htac/tests/test_pprl.py

Tests for htac/services/pprl.py.

PII policy: no real names, dates-of-birth, or phone numbers appear in
this file.  All PII-shaped inputs are synthetic and obviously fictitious
(e.g. "Aaa", "Bbb", "19000101").  The SHA-256 values asserted below were
computed from those synthetic inputs — they are hashes of fictional data.
"""

import datetime
import hashlib
import pytest

from htac.services.pprl import _digits_only, _format_dob, compute_token


# ─── _digits_only ─────────────────────────────────────────────────────────────

class TestDigitsOnly:
    def test_plain_digits_unchanged(self):
        assert _digits_only("1234567890") == "1234567890"

    def test_strips_dashes_and_parens(self):
        assert _digits_only("(555) 000-1111") == "5550001111"

    def test_strips_dots(self):
        assert _digits_only("555.000.1111") == "5550001111"

    def test_empty_string(self):
        assert _digits_only("") == ""

    def test_no_digits_returns_empty(self):
        assert _digits_only("abc-xyz") == ""

    def test_mixed(self):
        assert _digits_only("+1 (800) 555-0000") == "18005550000"


# ─── _format_dob ──────────────────────────────────────────────────────────────

class TestFormatDob:
    def test_date_object(self):
        assert _format_dob(datetime.date(1900, 1, 1)) == "19000101"

    def test_datetime_object(self):
        assert _format_dob(datetime.datetime(1900, 6, 15, 0, 0)) == "19000615"

    def test_iso_string(self):
        assert _format_dob("1900-01-01") == "19000101"

    def test_slash_string(self):
        # MM/DD/YYYY — strip non-digits → same 8-char blob
        assert _format_dob("01/01/1900") == "01011900"

    def test_already_yyyymmdd(self):
        assert _format_dob("19000101") == "19000101"


# ─── compute_token ────────────────────────────────────────────────────────────

def _expected_token(fn, ln, dob_str, sex_char, phone_digits, zip5):
    """Reference implementation — mirrors pprl.compute_token exactly."""
    preimage = fn + ln + dob_str + sex_char + phone_digits + zip5
    return hashlib.sha256(preimage.encode("utf-8")).hexdigest()


class TestComputeToken:
    # Canonical synthetic inputs — obviously not real PII
    FN    = "aaa"       # first name lower
    LN    = "bbb"       # last name lower
    DOB   = "19000101"  # dob string (YYYYMMDD after normalisation)
    SEX   = "m"
    PHONE = "5550001111"
    ZIP   = "00000"

    def _token(self, **overrides):
        params = dict(
            first_name="Aaa",
            last_name="Bbb",
            dob="1900-01-01",
            sex="M",
            phone="555-000-1111",
            zip_code="00000-1234",
        )
        params.update(overrides)
        return compute_token(**params)

    def test_returns_64_char_hex(self):
        tok = self._token()
        assert len(tok) == 64
        assert all(c in "0123456789abcdef" for c in tok)

    def test_deterministic(self):
        assert self._token() == self._token()

    def test_matches_reference_implementation(self):
        expected = _expected_token(
            self.FN, self.LN, self.DOB, self.SEX, self.PHONE, self.ZIP
        )
        assert self._token() == expected

    def test_case_insensitive_name(self):
        """Upper-case and mixed-case names must produce the same token."""
        assert self._token(first_name="AAA") == self._token(first_name="aaa")
        assert self._token(last_name="BBB") == self._token(last_name="bbb")

    def test_case_insensitive_sex(self):
        assert self._token(sex="M") == self._token(sex="m")

    def test_phone_format_invariant(self):
        """Stripping non-digit chars must not change the token."""
        assert (
            self._token(phone="555-000-1111")
            == self._token(phone="5550001111")
            == self._token(phone="(555) 000-1111")
        )

    def test_zip_truncated_to_5(self):
        """Only the first 5 zip chars are hashed."""
        assert self._token(zip_code="00000") == self._token(zip_code="00000-1234")

    def test_date_object_accepted(self):
        """compute_token must accept a datetime.date as dob."""
        tok_str  = self._token(dob="1900-01-01")
        tok_date = self._token(dob=datetime.date(1900, 1, 1))
        assert tok_str == tok_date

    def test_different_first_name_gives_different_token(self):
        assert self._token(first_name="Aaa") != self._token(first_name="Ccc")

    def test_different_last_name_gives_different_token(self):
        assert self._token(last_name="Bbb") != self._token(last_name="Ddd")

    def test_different_dob_gives_different_token(self):
        assert self._token(dob="1900-01-01") != self._token(dob="1900-01-02")

    def test_different_sex_gives_different_token(self):
        assert self._token(sex="M") != self._token(sex="F")

    def test_different_phone_gives_different_token(self):
        assert (
            self._token(phone="5550001111") != self._token(phone="5550002222")
        )

    def test_different_zip_gives_different_token(self):
        assert self._token(zip_code="00000") != self._token(zip_code="11111")

    def test_sex_uses_only_first_char(self):
        """'Male' and 'M' must hash identically."""
        assert self._token(sex="M") == self._token(sex="Male")


# ─── deduplicate_tokens ───────────────────────────────────────────────────────

@pytest.mark.django_db
class TestDeduplicateTokens:
    """
    Integration tests for deduplicate_tokens().

    Database fixtures use only synthetic tokens (pre-computed SHA-256 hex
    strings) — no PII appears in the fixture data.
    """

    # Two synthetic token values (SHA-256 of "placeholder" strings)
    TOKEN_A = hashlib.sha256(b"token-a-placeholder").hexdigest()
    TOKEN_B = hashlib.sha256(b"token-b-placeholder").hexdigest()

    @pytest.fixture()
    def two_sites(self, db):
        from htac.models import HealthSystem
        site1 = HealthSystem.objects.create(name="Site One", short_code="S1")
        site2 = HealthSystem.objects.create(name="Site Two", short_code="S2")
        return site1, site2

    @pytest.fixture()
    def persons_and_tokens(self, two_sites):
        from htac.models import HashToken, Person
        site1, site2 = two_sites

        # Shared token (TOKEN_A) appears at both sites
        p1 = Person.objects.create(
            health_system=site1, person_source_value="P001",
            gender_concept_id=8507, year_of_birth=1900,
            race_concept_id=8527, ethnicity_concept_id=38003563,
        )
        p2 = Person.objects.create(
            health_system=site2, person_source_value="P002",
            gender_concept_id=8507, year_of_birth=1900,
            race_concept_id=8527, ethnicity_concept_id=38003563,
        )
        # TOKEN_B appears only at site1
        p3 = Person.objects.create(
            health_system=site1, person_source_value="P003",
            gender_concept_id=8532, year_of_birth=1900,
            race_concept_id=8527, ethnicity_concept_id=38003563,
        )

        HashToken.objects.create(health_system=site1, person=p1, token=self.TOKEN_A)
        HashToken.objects.create(health_system=site2, person=p2, token=self.TOKEN_A)
        HashToken.objects.create(health_system=site1, person=p3, token=self.TOKEN_B)

        return site1, site2, p1, p2, p3

    def test_returns_upserted_count(self, persons_and_tokens):
        from htac.models import HashToken
        from htac.services.pprl import deduplicate_tokens

        count = deduplicate_tokens(HashToken.objects.all())
        assert count == 2  # TOKEN_A + TOKEN_B

    def test_creates_roster_rows(self, persons_and_tokens):
        from htac.models import DeduplicatedRoster, HashToken
        from htac.services.pprl import deduplicate_tokens

        deduplicate_tokens(HashToken.objects.all())
        assert DeduplicatedRoster.objects.count() == 2

    def test_multi_site_token_site_count(self, persons_and_tokens):
        from htac.models import DeduplicatedRoster, HashToken
        from htac.services.pprl import deduplicate_tokens

        deduplicate_tokens(HashToken.objects.all())
        roster_a = DeduplicatedRoster.objects.get(canonical_token=self.TOKEN_A)
        assert roster_a.site_count == 2

    def test_single_site_token_site_count(self, persons_and_tokens):
        from htac.models import DeduplicatedRoster, HashToken
        from htac.services.pprl import deduplicate_tokens

        deduplicate_tokens(HashToken.objects.all())
        roster_b = DeduplicatedRoster.objects.get(canonical_token=self.TOKEN_B)
        assert roster_b.site_count == 1

    def test_canonical_site_chosen_by_most_recent_visit(self, persons_and_tokens):
        """
        TOKEN_A appears at S1 and S2.  We give S2's person a more recent visit,
        so S2 should become the canonical site.
        """
        import datetime
        from htac.models import DeduplicatedRoster, HashToken, VisitOccurrence
        from htac.services.pprl import deduplicate_tokens

        site1, site2, p1, p2, _ = persons_and_tokens

        VisitOccurrence.objects.create(
            person=p1, health_system=site1,
            visit_concept_id=9202, visit_type_concept_id=44818517,
            visit_start_date=datetime.date(2020, 1, 1),
        )
        VisitOccurrence.objects.create(
            person=p2, health_system=site2,
            visit_concept_id=9202, visit_type_concept_id=44818517,
            visit_start_date=datetime.date(2023, 6, 1),  # more recent
        )

        deduplicate_tokens(HashToken.objects.all())

        roster_a = DeduplicatedRoster.objects.get(canonical_token=self.TOKEN_A)
        assert roster_a.canonical_site == site2

    def test_fallback_canonical_site_when_no_visits(self, persons_and_tokens):
        """Without any VisitOccurrence rows, the first HashToken's site is used."""
        from htac.models import DeduplicatedRoster, HashToken
        from htac.services.pprl import deduplicate_tokens

        deduplicate_tokens(HashToken.objects.all())
        # No visits were created, so canonical site must be one of {S1, S2}
        roster_a = DeduplicatedRoster.objects.get(canonical_token=self.TOKEN_A)
        assert roster_a.canonical_site is not None

    def test_idempotent(self, persons_and_tokens):
        """Running twice must not create duplicate rows."""
        from htac.models import DeduplicatedRoster, HashToken
        from htac.services.pprl import deduplicate_tokens

        deduplicate_tokens(HashToken.objects.all())
        deduplicate_tokens(HashToken.objects.all())
        assert DeduplicatedRoster.objects.count() == 2

    def test_roster_version_set_to_today(self, persons_and_tokens):
        import datetime
        from htac.models import DeduplicatedRoster, HashToken
        from htac.services.pprl import deduplicate_tokens

        deduplicate_tokens(HashToken.objects.all())
        today = datetime.date.today()
        assert all(
            r.roster_version == today
            for r in DeduplicatedRoster.objects.all()
        )

    def test_filtered_queryset_limits_scope(self, persons_and_tokens):
        """
        When deduplicate_tokens receives a site-filtered queryset,
        only tokens visible in that queryset are processed.
        TOKEN_A is at S1 and S2; TOKEN_B is only at S1.
        Filtering to S2 yields only TOKEN_A.
        """
        from htac.models import DeduplicatedRoster, HashToken
        from htac.services.pprl import deduplicate_tokens

        _, site2, *_ = persons_and_tokens
        qs = HashToken.objects.filter(health_system=site2)
        count = deduplicate_tokens(qs)

        assert count == 1
        assert DeduplicatedRoster.objects.count() == 1
        assert DeduplicatedRoster.objects.filter(canonical_token=self.TOKEN_A).exists()
