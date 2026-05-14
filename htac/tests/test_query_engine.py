"""
htac/tests/test_query_engine.py

Tests for htac/services/query_engine.py.

No PII appears in these fixtures — all patient data is synthetic and
obviously fictitious (zero-padded source values, placeholder names, etc.).
"""

import datetime
from decimal import Decimal

import pytest

from htac.services.query_engine import (
    _age_group,
    _ethnicity_label,
    _gender_label,
    _race_label,
    apply_suppression,
    get_condition_cohort,
    stratify_cohort,
)


# ─── Label helpers ────────────────────────────────────────────────────────────

class TestLabelHelpers:
    def test_gender_known(self):
        assert _gender_label(8507) == "Male"
        assert _gender_label(8532) == "Female"
        assert _gender_label(8521) == "Unknown"

    def test_gender_unknown_concept(self):
        assert _gender_label(9999) == "Concept:9999"

    def test_race_known(self):
        assert _race_label(8527) == "White"
        assert _race_label(8516) == "Black or African American"
        assert _race_label(0)    == "Unknown"

    def test_race_unknown_concept(self):
        assert _race_label(9999) == "Concept:9999"

    def test_ethnicity_known(self):
        assert _ethnicity_label(38003563) == "Hispanic or Latino"
        assert _ethnicity_label(38003564) == "Not Hispanic or Latino"
        assert _ethnicity_label(0)        == "Unknown"

    def test_ethnicity_unknown_concept(self):
        assert _ethnicity_label(9999) == "Concept:9999"


# ─── _age_group ───────────────────────────────────────────────────────────────

class TestAgeGroup:
    REF = 2024   # fixed reference year for deterministic tests

    def test_child(self):
        assert _age_group(2024 - 10, self.REF) == "0-17"

    def test_boundary_0(self):
        assert _age_group(2024, self.REF) == "0-17"

    def test_boundary_17(self):
        assert _age_group(2024 - 17, self.REF) == "0-17"

    def test_boundary_18(self):
        assert _age_group(2024 - 18, self.REF) == "18-34"

    def test_middle_adult(self):
        assert _age_group(2024 - 40, self.REF) == "35-49"

    def test_older_adult(self):
        assert _age_group(2024 - 55, self.REF) == "50-64"

    def test_senior(self):
        assert _age_group(2024 - 70, self.REF) == "65+"

    def test_boundary_65(self):
        assert _age_group(2024 - 65, self.REF) == "65+"


# ─── apply_suppression ────────────────────────────────────────────────────────

class TestApplySuppression:
    def _run(self, numerator, denominator, threshold=11):
        data = {"All": {"numerator": numerator, "denominator": denominator}}
        return apply_suppression(data, threshold)["All"]

    def test_cell_above_threshold_not_suppressed(self):
        result = self._run(20, 100)
        assert result["is_suppressed"] is False
        assert result["numerator"] == 20
        assert result["denominator"] == 100

    def test_cell_at_threshold_not_suppressed(self):
        result = self._run(11, 50)
        assert result["is_suppressed"] is False

    def test_cell_below_threshold_suppressed(self):
        result = self._run(10, 100)
        assert result["is_suppressed"] is True
        assert result["numerator"] is None
        assert result["denominator"] is None
        assert result["prevalence_rate"] is None

    def test_zero_numerator_suppressed(self):
        result = self._run(0, 100)
        assert result["is_suppressed"] is True

    def test_prevalence_rate_computed(self):
        result = self._run(50, 200)
        assert result["prevalence_rate"] == Decimal("0.2500")

    def test_prevalence_rate_rounded_half_up(self):
        # 1 / 3 = 0.333333... → rounds to 0.3333
        result = self._run(100, 300)
        assert result["prevalence_rate"] == Decimal("0.3333")

    def test_zero_denominator_rate_is_none(self):
        result = self._run(20, 0)
        assert result["is_suppressed"] is False
        assert result["prevalence_rate"] is None

    def test_custom_threshold(self):
        result = self._run(5, 100, threshold=5)
        assert result["is_suppressed"] is False

    def test_empty_dict(self):
        assert apply_suppression({}) == {}

    def test_multiple_strata(self):
        data = {
            "Male":   {"numerator": 30, "denominator": 100},
            "Female": {"numerator": 5,  "denominator": 80},
        }
        out = apply_suppression(data)
        assert out["Male"]["is_suppressed"] is False
        assert out["Female"]["is_suppressed"] is True

    def test_rate_precision_4_decimal_places(self):
        result = self._run(1234, 10000)
        # 1234/10000 = 0.1234
        assert result["prevalence_rate"] == Decimal("0.1234")


# ─── get_condition_cohort ─────────────────────────────────────────────────────

@pytest.fixture()
def site(db):
    from htac.models import HealthSystem
    return HealthSystem.objects.create(name="Test Site", short_code="TEST")


@pytest.fixture()
def condition(db):
    from htac.models import Condition
    return Condition.objects.create(
        name="Test Condition",
        slug="test-condition",
        htac_category="chronic",
    )


@pytest.fixture()
def study_period():
    return (datetime.date(2022, 1, 1), datetime.date(2022, 12, 31))


def _make_person(site, source_value="P001", gender=8507, yob=1970,
                 race=8527, ethnicity=38003564):
    from htac.models import Person
    return Person.objects.create(
        health_system=site,
        person_source_value=source_value,
        gender_concept_id=gender,
        year_of_birth=yob,
        race_concept_id=race,
        ethnicity_concept_id=ethnicity,
    )


@pytest.mark.django_db
class TestGetConditionCohort:
    def test_no_concept_codes_returns_empty(self, condition, site, study_period):
        _make_person(site)
        qs = get_condition_cohort(condition, site, study_period)
        assert qs.count() == 0

    def test_condition_domain_match(self, condition, site, study_period):
        from htac.models import ConceptCode, ConditionOccurrence
        ConceptCode.objects.create(
            condition=condition, concept_id=201826,
            concept_name="Diabetes", domain="condition",
            vocabulary_id="SNOMED",
        )
        p = _make_person(site)
        ConditionOccurrence.objects.create(
            person=p, health_system=site,
            condition_concept_id=201826,
            condition_start_date=datetime.date(2022, 3, 1),
            condition_type_concept_id=32020,
        )
        qs = get_condition_cohort(condition, site, study_period)
        assert p in qs

    def test_drug_domain_match(self, condition, site, study_period):
        from htac.models import ConceptCode, DrugExposure
        ConceptCode.objects.create(
            condition=condition, concept_id=1503297,
            concept_name="Metformin", domain="drug",
            vocabulary_id="RxNorm",
        )
        p = _make_person(site)
        DrugExposure.objects.create(
            person=p, health_system=site,
            drug_concept_id=1503297,
            drug_exposure_start_date=datetime.date(2022, 6, 1),
        )
        qs = get_condition_cohort(condition, site, study_period)
        assert p in qs

    def test_measurement_domain_match(self, condition, site, study_period):
        from htac.models import ConceptCode, Measurement
        ConceptCode.objects.create(
            condition=condition, concept_id=3004410,
            concept_name="HbA1c", domain="measurement",
            vocabulary_id="LOINC",
        )
        p = _make_person(site)
        Measurement.objects.create(
            person=p, health_system=site,
            measurement_concept_id=3004410,
            measurement_date=datetime.date(2022, 4, 15),
        )
        qs = get_condition_cohort(condition, site, study_period)
        assert p in qs

    def test_observation_domain_match(self, condition, site, study_period):
        from htac.models import ConceptCode, Observation
        ConceptCode.objects.create(
            condition=condition, concept_id=4274025,
            concept_name="Tobacco use", domain="observation",
            vocabulary_id="SNOMED",
        )
        p = _make_person(site)
        Observation.objects.create(
            person=p, health_system=site,
            observation_concept_id=4274025,
            observation_date=datetime.date(2022, 7, 1),
        )
        qs = get_condition_cohort(condition, site, study_period)
        assert p in qs

    def test_outside_study_period_excluded(self, condition, site, study_period):
        from htac.models import ConceptCode, ConditionOccurrence
        ConceptCode.objects.create(
            condition=condition, concept_id=201826,
            concept_name="Diabetes", domain="condition",
            vocabulary_id="SNOMED",
        )
        p = _make_person(site)
        ConditionOccurrence.objects.create(
            person=p, health_system=site,
            condition_concept_id=201826,
            condition_start_date=datetime.date(2021, 12, 31),  # before window
            condition_type_concept_id=32020,
        )
        qs = get_condition_cohort(condition, site, study_period)
        assert p not in qs

    def test_excluded_concept_removes_person(self, condition, site, study_period):
        from htac.models import ConceptCode, ConditionOccurrence
        ConceptCode.objects.create(
            condition=condition, concept_id=201826,
            concept_name="Diabetes", domain="condition",
            vocabulary_id="SNOMED",
        )
        ConceptCode.objects.create(
            condition=condition, concept_id=999999,
            concept_name="Exclusion code", domain="condition",
            vocabulary_id="SNOMED", is_excluded=True,
        )
        p = _make_person(site)
        # Qualifying event
        ConditionOccurrence.objects.create(
            person=p, health_system=site,
            condition_concept_id=201826,
            condition_start_date=datetime.date(2022, 3, 1),
            condition_type_concept_id=32020,
        )
        # Exclusion event
        ConditionOccurrence.objects.create(
            person=p, health_system=site,
            condition_concept_id=999999,
            condition_start_date=datetime.date(2022, 5, 1),
            condition_type_concept_id=32020,
        )
        qs = get_condition_cohort(condition, site, study_period)
        assert p not in qs

    def test_person_at_other_site_not_included(self, condition, site, study_period, db):
        from htac.models import ConceptCode, ConditionOccurrence, HealthSystem
        ConceptCode.objects.create(
            condition=condition, concept_id=201826,
            concept_name="Diabetes", domain="condition",
            vocabulary_id="SNOMED",
        )
        other_site = HealthSystem.objects.create(name="Other", short_code="OTH")
        p_other = _make_person(other_site, source_value="P999")
        ConditionOccurrence.objects.create(
            person=p_other, health_system=other_site,
            condition_concept_id=201826,
            condition_start_date=datetime.date(2022, 3, 1),
            condition_type_concept_id=32020,
        )
        qs = get_condition_cohort(condition, site, study_period)
        assert p_other not in qs

    def test_or_logic_across_domains(self, condition, site, study_period):
        """A person qualifying in any one domain is included."""
        from htac.models import ConceptCode, ConditionOccurrence, DrugExposure
        ConceptCode.objects.create(
            condition=condition, concept_id=201826,
            concept_name="Dx", domain="condition", vocabulary_id="SNOMED",
        )
        ConceptCode.objects.create(
            condition=condition, concept_id=1503297,
            concept_name="Rx", domain="drug", vocabulary_id="RxNorm",
        )
        p1 = _make_person(site, source_value="P001")
        p2 = _make_person(site, source_value="P002")

        ConditionOccurrence.objects.create(
            person=p1, health_system=site,
            condition_concept_id=201826,
            condition_start_date=datetime.date(2022, 2, 1),
            condition_type_concept_id=32020,
        )
        DrugExposure.objects.create(
            person=p2, health_system=site,
            drug_concept_id=1503297,
            drug_exposure_start_date=datetime.date(2022, 9, 1),
        )
        qs = get_condition_cohort(condition, site, study_period)
        assert {p1.pk, p2.pk} == set(qs.values_list("id", flat=True))


# ─── stratify_cohort ──────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestStratifyCohort:
    """
    Fixtures: one site with 3 persons — 2 in cohort, 1 not.
    """

    @pytest.fixture(autouse=True)
    def setup(self, db):
        from htac.models import DeduplicatedRoster, HashToken, HealthSystem, Person
        import hashlib

        self.site = HealthSystem.objects.create(name="Stratify Site", short_code="STR")

        # p1 — Male, White, Not Hispanic, born 1970, language="English"
        self.p1 = Person.objects.create(
            health_system=self.site, person_source_value="SP01",
            gender_concept_id=8507, year_of_birth=1970,
            race_concept_id=8527, ethnicity_concept_id=38003564,
            preferred_language="English",
        )
        # p2 — Female, Black, Hispanic, born 1990, language="Spanish"
        self.p2 = Person.objects.create(
            health_system=self.site, person_source_value="SP02",
            gender_concept_id=8532, year_of_birth=1990,
            race_concept_id=8516, ethnicity_concept_id=38003563,
            preferred_language="Spanish",
        )
        # p3 — not in cohort
        self.p3 = Person.objects.create(
            health_system=self.site, person_source_value="SP03",
            gender_concept_id=8507, year_of_birth=1985,
            race_concept_id=8527, ethnicity_concept_id=38003564,
            preferred_language="English",
        )

        self.cohort_qs = Person.objects.filter(pk__in=[self.p1.pk, self.p2.pk])
        self.denom_qs  = Person.objects.filter(health_system=self.site)
        self.roster_qs = DeduplicatedRoster.objects.none()

        # Roster + tokens for enrichment-flag tests
        tok1 = hashlib.sha256(b"tok-p1").hexdigest()
        tok2 = hashlib.sha256(b"tok-p2").hexdigest()
        tok3 = hashlib.sha256(b"tok-p3").hexdigest()

        today = datetime.date.today()
        self.roster1 = DeduplicatedRoster.objects.create(
            canonical_token=tok1, canonical_site=self.site, site_count=1,
            roster_version=today,
            homeless_flag=True, medicaid_flag=True,
            jail_flag=False, prison_flag=False,
        )
        self.roster2 = DeduplicatedRoster.objects.create(
            canonical_token=tok2, canonical_site=self.site, site_count=1,
            roster_version=today,
            homeless_flag=False, medicaid_flag=False,
            jail_flag=True, prison_flag=False,
        )
        self.roster3 = DeduplicatedRoster.objects.create(
            canonical_token=tok3, canonical_site=self.site, site_count=1,
            roster_version=today,
            homeless_flag=False, medicaid_flag=False,
            jail_flag=False, prison_flag=False,
        )
        HashToken.objects.create(health_system=self.site, person=self.p1, token=tok1)
        HashToken.objects.create(health_system=self.site, person=self.p2, token=tok2)
        HashToken.objects.create(health_system=self.site, person=self.p3, token=tok3)

        self.full_roster_qs = DeduplicatedRoster.objects.all()

    # ── total ──────────────────────────────────────────────────────────────────

    def test_total_numerator_denominator(self):
        result = stratify_cohort(self.cohort_qs, "total", self.roster_qs)
        assert result["All"]["numerator"]   == 2
        assert result["All"]["denominator"] == 3

    def test_empty_cohort_returns_empty(self):
        from htac.models import Person
        empty = Person.objects.none()
        result = stratify_cohort(empty, "total", self.roster_qs)
        assert result == {}

    # ── sex ────────────────────────────────────────────────────────────────────

    def test_sex_stratifier(self):
        result = stratify_cohort(self.cohort_qs, "sex", self.roster_qs)
        assert result["Male"]["numerator"]   == 1
        assert result["Male"]["denominator"] == 2   # p1 + p3 at site
        assert result["Female"]["numerator"]   == 1
        assert result["Female"]["denominator"] == 1

    # ── race ───────────────────────────────────────────────────────────────────

    def test_race_stratifier(self):
        result = stratify_cohort(self.cohort_qs, "race", self.roster_qs)
        assert result["White"]["numerator"] == 1
        assert result["Black or African American"]["numerator"] == 1

    # ── ethnicity ──────────────────────────────────────────────────────────────

    def test_ethnicity_stratifier(self):
        result = stratify_cohort(self.cohort_qs, "ethnicity", self.roster_qs)
        assert result["Hispanic or Latino"]["numerator"] == 1
        assert result["Not Hispanic or Latino"]["numerator"] == 1

    # ── language ───────────────────────────────────────────────────────────────

    def test_language_stratifier(self):
        result = stratify_cohort(self.cohort_qs, "language", self.roster_qs)
        assert result["English"]["numerator"] == 1
        assert result["Spanish"]["numerator"] == 1

    # ── age_group ──────────────────────────────────────────────────────────────

    def test_age_group_stratifier_present(self):
        result = stratify_cohort(self.cohort_qs, "age_group", self.roster_qs)
        # At least one bucket must be non-empty
        assert any(v["numerator"] > 0 for v in result.values())

    # ── unknown stratifier ─────────────────────────────────────────────────────

    def test_unknown_stratifier_returns_empty(self):
        result = stratify_cohort(self.cohort_qs, "foobar", self.roster_qs)
        assert result == {}

    # ── enrichment flags ───────────────────────────────────────────────────────

    def test_homeless_stratifier(self):
        result = stratify_cohort(self.cohort_qs, "homeless", self.full_roster_qs)
        # p1 is homeless (in cohort), p2 is not homeless (in cohort)
        assert result["True"]["numerator"]  == 1
        assert result["False"]["numerator"] == 1

    def test_medicaid_stratifier(self):
        result = stratify_cohort(self.cohort_qs, "medicaid", self.full_roster_qs)
        assert result["True"]["numerator"]  == 1   # p1
        assert result["False"]["numerator"] == 1   # p2

    def test_incarceration_stratifier(self):
        # p2 has jail_flag=True → incarceration=True
        result = stratify_cohort(self.cohort_qs, "incarceration", self.full_roster_qs)
        assert result["True"]["numerator"]  == 1   # p2
        assert result["False"]["numerator"] == 1   # p1
