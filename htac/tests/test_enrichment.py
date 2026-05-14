"""
htac/tests/test_enrichment.py

Tests for htac/services/enrichment.py.

No PII appears here — all token values are SHA-256 digests of placeholder
bytes (e.g. b"token-A"), making it obvious they are synthetic.
"""

import datetime
import hashlib
from datetime import date

import pytest

from htac.services.enrichment import (
    enrich_from_doc,
    enrich_from_hmis,
    enrich_from_medicaid,
    enrich_from_miic,
    enrich_from_vitals,
)


# ─── Shared fixtures ──────────────────────────────────────────────────────────

TOKEN_A = hashlib.sha256(b"token-A").hexdigest()
TOKEN_B = hashlib.sha256(b"token-B").hexdigest()
TOKEN_C = hashlib.sha256(b"token-C").hexdigest()   # never in any staging table


@pytest.fixture()
def site(db):
    from htac.models import HealthSystem
    return HealthSystem.objects.create(name="Enrich Site", short_code="ENR")


@pytest.fixture()
def roster(site):
    """Three DeduplicatedRoster rows — A, B, and C (C is always unmatched)."""
    from htac.models import DeduplicatedRoster
    today = date.today()
    rows = DeduplicatedRoster.objects.bulk_create([
        DeduplicatedRoster(canonical_token=TOKEN_A, canonical_site=site, site_count=1, roster_version=today),
        DeduplicatedRoster(canonical_token=TOKEN_B, canonical_site=site, site_count=1, roster_version=today),
        DeduplicatedRoster(canonical_token=TOKEN_C, canonical_site=site, site_count=1, roster_version=today),
    ])
    return rows


def _get(token):
    from htac.models import DeduplicatedRoster
    return DeduplicatedRoster.objects.get(canonical_token=token)


def _all_qs():
    from htac.models import DeduplicatedRoster
    return DeduplicatedRoster.objects.all()


# ─── enrich_from_medicaid ─────────────────────────────────────────────────────

@pytest.mark.django_db
class TestEnrichFromMedicaid:
    @pytest.fixture(autouse=True)
    def _roster(self, roster):
        pass

    def test_matched_token_flag_set_true(self, db):
        from htac.models import MedicaidEnrollment
        MedicaidEnrollment.objects.create(
            token_hash=TOKEN_A,
            effective_date=datetime.date(2020, 1, 1),
            end_date=datetime.date(2020, 12, 31),
            coverage_type="MA",
        )
        enrich_from_medicaid(_all_qs())
        assert _get(TOKEN_A).medicaid_flag is True

    def test_matched_token_earliest_date(self, db):
        from htac.models import MedicaidEnrollment
        MedicaidEnrollment.objects.create(
            token_hash=TOKEN_A, effective_date=datetime.date(2020, 6, 1),
            end_date=datetime.date(2020, 12, 31), coverage_type="MA",
        )
        MedicaidEnrollment.objects.create(
            token_hash=TOKEN_A, effective_date=datetime.date(2019, 3, 1),
            end_date=datetime.date(2019, 12, 31), coverage_type="MA",
        )
        enrich_from_medicaid(_all_qs())
        assert _get(TOKEN_A).medicaid_effective_date == datetime.date(2019, 3, 1)

    def test_unmatched_token_flag_false(self, db):
        from htac.models import MedicaidEnrollment
        MedicaidEnrollment.objects.create(
            token_hash=TOKEN_A, effective_date=datetime.date(2020, 1, 1),
            end_date=datetime.date(2020, 12, 31), coverage_type="MA",
        )
        enrich_from_medicaid(_all_qs())
        rec_b = _get(TOKEN_B)
        assert rec_b.medicaid_flag is False
        assert rec_b.medicaid_effective_date is None

    def test_returns_matched_count(self, db):
        from htac.models import MedicaidEnrollment
        MedicaidEnrollment.objects.create(
            token_hash=TOKEN_A, effective_date=datetime.date(2020, 1, 1),
            end_date=datetime.date(2020, 12, 31), coverage_type="MA",
        )
        count = enrich_from_medicaid(_all_qs())
        assert count == 1

    def test_idempotent(self, db):
        from htac.models import MedicaidEnrollment
        MedicaidEnrollment.objects.create(
            token_hash=TOKEN_A, effective_date=datetime.date(2020, 1, 1),
            end_date=datetime.date(2020, 12, 31), coverage_type="MA",
        )
        enrich_from_medicaid(_all_qs())
        enrich_from_medicaid(_all_qs())
        assert _get(TOKEN_A).medicaid_flag is True
        assert _get(TOKEN_B).medicaid_flag is False

    def test_empty_staging_clears_flags(self, db):
        """Re-run with no staging data must set all flags to False (complete refresh)."""
        enrich_from_medicaid(_all_qs())
        for tok in (TOKEN_A, TOKEN_B, TOKEN_C):
            rec = _get(tok)
            assert rec.medicaid_flag is False
            assert rec.medicaid_effective_date is None

    def test_no_staging_returns_zero(self, db):
        assert enrich_from_medicaid(_all_qs()) == 0


# ─── enrich_from_hmis ─────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestEnrichFromHmis:
    @pytest.fixture(autouse=True)
    def _roster(self, roster):
        pass

    def test_matched_token_homeless_true(self, db):
        from htac.models import HMISRecord
        HMISRecord.objects.create(
            token_hash=TOKEN_B,
            service_type="emergency_shelter",
            entry_date=datetime.date(2021, 5, 1),
        )
        enrich_from_hmis(_all_qs())
        assert _get(TOKEN_B).homeless_flag is True

    def test_earliest_entry_date_stored(self, db):
        from htac.models import HMISRecord
        HMISRecord.objects.create(
            token_hash=TOKEN_B, service_type="emergency_shelter",
            entry_date=datetime.date(2021, 5, 1),
        )
        HMISRecord.objects.create(
            token_hash=TOKEN_B, service_type="transitional_housing",
            entry_date=datetime.date(2018, 9, 15),
        )
        enrich_from_hmis(_all_qs())
        assert _get(TOKEN_B).homeless_first_service_date == datetime.date(2018, 9, 15)

    def test_unmatched_flag_false(self, db):
        from htac.models import HMISRecord
        HMISRecord.objects.create(
            token_hash=TOKEN_B, service_type="emergency_shelter",
            entry_date=datetime.date(2021, 5, 1),
        )
        enrich_from_hmis(_all_qs())
        rec_a = _get(TOKEN_A)
        assert rec_a.homeless_flag is False
        assert rec_a.homeless_first_service_date is None

    def test_returns_matched_count(self, db):
        from htac.models import HMISRecord
        HMISRecord.objects.create(
            token_hash=TOKEN_A, service_type="emergency_shelter",
            entry_date=datetime.date(2021, 1, 1),
        )
        HMISRecord.objects.create(
            token_hash=TOKEN_B, service_type="transitional_housing",
            entry_date=datetime.date(2021, 2, 1),
        )
        assert enrich_from_hmis(_all_qs()) == 2

    def test_no_staging_returns_zero(self, db):
        assert enrich_from_hmis(_all_qs()) == 0


# ─── enrich_from_doc ──────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestEnrichFromDoc:
    @pytest.fixture(autouse=True)
    def _roster(self, roster):
        pass

    def test_jail_flag_set(self, db):
        from htac.models import DOCRecord
        DOCRecord.objects.create(
            token_hash=TOKEN_A, record_type="jail",
            admission_date=datetime.date(2019, 3, 1),
        )
        enrich_from_doc(_all_qs())
        assert _get(TOKEN_A).jail_flag is True
        assert _get(TOKEN_A).prison_flag is False

    def test_prison_flag_set(self, db):
        from htac.models import DOCRecord
        DOCRecord.objects.create(
            token_hash=TOKEN_A, record_type="prison",
            admission_date=datetime.date(2018, 7, 15),
        )
        enrich_from_doc(_all_qs())
        assert _get(TOKEN_A).prison_flag is True
        assert _get(TOKEN_A).jail_flag is False

    def test_both_flags_set_for_same_token(self, db):
        from htac.models import DOCRecord
        DOCRecord.objects.create(
            token_hash=TOKEN_A, record_type="jail",
            admission_date=datetime.date(2017, 1, 1),
        )
        DOCRecord.objects.create(
            token_hash=TOKEN_A, record_type="prison",
            admission_date=datetime.date(2018, 1, 1),
        )
        enrich_from_doc(_all_qs())
        rec = _get(TOKEN_A)
        assert rec.jail_flag is True
        assert rec.prison_flag is True

    def test_earliest_jail_date(self, db):
        from htac.models import DOCRecord
        DOCRecord.objects.create(
            token_hash=TOKEN_A, record_type="jail",
            admission_date=datetime.date(2019, 6, 1),
        )
        DOCRecord.objects.create(
            token_hash=TOKEN_A, record_type="jail",
            admission_date=datetime.date(2017, 2, 1),
        )
        enrich_from_doc(_all_qs())
        assert _get(TOKEN_A).jail_admission_date == datetime.date(2017, 2, 1)

    def test_unmatched_token_both_flags_false(self, db):
        from htac.models import DOCRecord
        DOCRecord.objects.create(
            token_hash=TOKEN_A, record_type="jail",
            admission_date=datetime.date(2019, 1, 1),
        )
        enrich_from_doc(_all_qs())
        rec_b = _get(TOKEN_B)
        assert rec_b.jail_flag is False
        assert rec_b.prison_flag is False
        assert rec_b.jail_admission_date is None
        assert rec_b.prison_admission_date is None

    def test_returns_union_count(self, db):
        """Token with both jail and prison counts once in the return value."""
        from htac.models import DOCRecord
        DOCRecord.objects.create(
            token_hash=TOKEN_A, record_type="jail",
            admission_date=datetime.date(2019, 1, 1),
        )
        DOCRecord.objects.create(
            token_hash=TOKEN_A, record_type="prison",
            admission_date=datetime.date(2020, 1, 1),
        )
        DOCRecord.objects.create(
            token_hash=TOKEN_B, record_type="jail",
            admission_date=datetime.date(2021, 1, 1),
        )
        # TOKEN_A + TOKEN_B = 2 distinct tokens
        assert enrich_from_doc(_all_qs()) == 2

    def test_no_staging_returns_zero(self, db):
        assert enrich_from_doc(_all_qs()) == 0


# ─── enrich_from_miic ────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestEnrichFromMiic:
    @pytest.fixture(autouse=True)
    def _roster(self, roster):
        pass

    def test_covid_flag_and_date(self, db):
        from htac.models import MIICRecord
        MIICRecord.objects.create(
            token_hash=TOKEN_A, vaccine_type="covid",
            vaccination_date=datetime.date(2021, 4, 1), cvx_code="212",
        )
        enrich_from_miic(_all_qs())
        rec = _get(TOKEN_A)
        assert rec.covid_vaccinated_flag is True
        assert rec.covid_vaccine_date == datetime.date(2021, 4, 1)

    def test_covid_earliest_date(self, db):
        from htac.models import MIICRecord
        MIICRecord.objects.create(
            token_hash=TOKEN_A, vaccine_type="covid",
            vaccination_date=datetime.date(2021, 10, 1), cvx_code="212",
        )
        MIICRecord.objects.create(
            token_hash=TOKEN_A, vaccine_type="covid",
            vaccination_date=datetime.date(2021, 4, 1), cvx_code="212",
        )
        enrich_from_miic(_all_qs())
        assert _get(TOKEN_A).covid_vaccine_date == datetime.date(2021, 4, 1)

    def test_influenza_flag_no_date(self, db):
        from htac.models import MIICRecord
        MIICRecord.objects.create(
            token_hash=TOKEN_B, vaccine_type="influenza",
            vaccination_date=datetime.date(2022, 10, 15), cvx_code="141",
        )
        enrich_from_miic(_all_qs())
        rec = _get(TOKEN_B)
        assert rec.influenza_vaccinated_flag is True

    def test_unmatched_flags_false(self, db):
        from htac.models import MIICRecord
        MIICRecord.objects.create(
            token_hash=TOKEN_A, vaccine_type="covid",
            vaccination_date=datetime.date(2021, 4, 1), cvx_code="212",
        )
        enrich_from_miic(_all_qs())
        rec_b = _get(TOKEN_B)
        assert rec_b.covid_vaccinated_flag is False
        assert rec_b.covid_vaccine_date is None
        assert rec_b.influenza_vaccinated_flag is False

    def test_returns_union_count(self, db):
        """Token with covid only + token with flu only + overlapping token = 3 distinct."""
        from htac.models import MIICRecord
        MIICRecord.objects.create(
            token_hash=TOKEN_A, vaccine_type="covid",
            vaccination_date=datetime.date(2021, 4, 1), cvx_code="212",
        )
        MIICRecord.objects.create(
            token_hash=TOKEN_B, vaccine_type="influenza",
            vaccination_date=datetime.date(2022, 10, 1), cvx_code="141",
        )
        assert enrich_from_miic(_all_qs()) == 2

    def test_same_token_both_vaccine_types(self, db):
        from htac.models import MIICRecord
        MIICRecord.objects.create(
            token_hash=TOKEN_A, vaccine_type="covid",
            vaccination_date=datetime.date(2021, 4, 1), cvx_code="212",
        )
        MIICRecord.objects.create(
            token_hash=TOKEN_A, vaccine_type="influenza",
            vaccination_date=datetime.date(2021, 10, 1), cvx_code="141",
        )
        enrich_from_miic(_all_qs())
        rec = _get(TOKEN_A)
        assert rec.covid_vaccinated_flag is True
        assert rec.influenza_vaccinated_flag is True
        # Union count = 1 distinct token
        assert enrich_from_miic(_all_qs()) == 1

    def test_no_staging_returns_zero(self, db):
        assert enrich_from_miic(_all_qs()) == 0


# ─── enrich_from_vitals ───────────────────────────────────────────────────────

@pytest.mark.django_db
class TestEnrichFromVitals:
    @pytest.fixture(autouse=True)
    def _roster(self, roster):
        pass

    def test_deceased_flag_set(self, db):
        from htac.models import VitalStatisticsRecord
        VitalStatisticsRecord.objects.create(
            token_hash=TOKEN_A,
            death_date=datetime.date(2023, 7, 4),
        )
        enrich_from_vitals(_all_qs())
        rec = _get(TOKEN_A)
        assert rec.deceased_flag is True
        assert rec.death_date == datetime.date(2023, 7, 4)

    def test_latest_death_date_used_for_duplicates(self, db):
        """When multiple records exist for one token, take the Max(death_date)."""
        from htac.models import VitalStatisticsRecord
        VitalStatisticsRecord.objects.create(
            token_hash=TOKEN_A, death_date=datetime.date(2022, 1, 1),
        )
        VitalStatisticsRecord.objects.create(
            token_hash=TOKEN_A, death_date=datetime.date(2023, 6, 30),
        )
        enrich_from_vitals(_all_qs())
        assert _get(TOKEN_A).death_date == datetime.date(2023, 6, 30)

    def test_unmatched_flag_false(self, db):
        from htac.models import VitalStatisticsRecord
        VitalStatisticsRecord.objects.create(
            token_hash=TOKEN_A, death_date=datetime.date(2023, 7, 4),
        )
        enrich_from_vitals(_all_qs())
        rec_b = _get(TOKEN_B)
        assert rec_b.deceased_flag is False
        assert rec_b.death_date is None

    def test_returns_matched_count(self, db):
        from htac.models import VitalStatisticsRecord
        VitalStatisticsRecord.objects.create(
            token_hash=TOKEN_A, death_date=datetime.date(2023, 1, 1),
        )
        VitalStatisticsRecord.objects.create(
            token_hash=TOKEN_B, death_date=datetime.date(2022, 5, 20),
        )
        assert enrich_from_vitals(_all_qs()) == 2

    def test_idempotent(self, db):
        from htac.models import VitalStatisticsRecord
        VitalStatisticsRecord.objects.create(
            token_hash=TOKEN_A, death_date=datetime.date(2023, 7, 4),
        )
        enrich_from_vitals(_all_qs())
        enrich_from_vitals(_all_qs())
        assert _get(TOKEN_A).deceased_flag is True
        assert _get(TOKEN_B).deceased_flag is False

    def test_complete_refresh_clears_stale_flags(self, db):
        """Running with no staging data resets deceased_flag to False for all rows."""
        enrich_from_vitals(_all_qs())
        for tok in (TOKEN_A, TOKEN_B, TOKEN_C):
            rec = _get(tok)
            assert rec.deceased_flag is False
            assert rec.death_date is None

    def test_no_staging_returns_zero(self, db):
        assert enrich_from_vitals(_all_qs()) == 0
