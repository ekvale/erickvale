"""
htac/models.py

Full data model for the multi-site federated HTAC (Health Trends Across Communities) pipeline.

Layers:
  1  OMOP Core        — multi-tenant patient/clinical data (simulated federated EHR)
  2  Codeset          — OMOP concept ID lists defining each of 22 health conditions
  3  PPRL             — privacy-preserving record linkage (hash tokens + dedup roster)
  4  Enrichment       — staging tables for 5 state data sources
  5  Analytic Output  — study runs, prevalence estimates, data quality reports

Compatible with SQLite (development) and PostgreSQL (production).
"""

from django.conf import settings
from django.db import models


# ─── Layer 1: OMOP Core (simulated, multi-tenant) ────────────────────────────

class HealthSystem(models.Model):
    name = models.CharField(max_length=200)
    short_code = models.CharField(max_length=20, unique=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = "htac"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Person(models.Model):
    """
    One record per patient per site.  No PII (name, DOB, phone) is stored here —
    those fields exist only transiently during hash-token generation.
    """
    health_system = models.ForeignKey(
        HealthSystem, on_delete=models.CASCADE, related_name="persons"
    )
    person_source_value = models.CharField(
        max_length=100,
        help_text="Site-internal patient identifier — never shared across sites.",
    )
    gender_concept_id = models.IntegerField(db_index=True)
    year_of_birth = models.IntegerField()
    race_concept_id = models.IntegerField(db_index=True)
    ethnicity_concept_id = models.IntegerField(db_index=True)
    preferred_language = models.CharField(max_length=50, blank=True)
    county_fips = models.CharField(max_length=5, blank=True, db_index=True)
    zip_code = models.CharField(max_length=10, blank=True, db_index=True)
    census_tract = models.CharField(max_length=11, blank=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = "htac"
        indexes = [
            models.Index(fields=["health_system", "person_source_value"]),
        ]

    def __str__(self):
        return f"Person {self.pk} @ {self.health_system.short_code}"


class VisitOccurrence(models.Model):
    person = models.ForeignKey(
        Person, on_delete=models.CASCADE, related_name="visits"
    )
    health_system = models.ForeignKey(
        HealthSystem, on_delete=models.CASCADE, related_name="visits"
    )
    visit_concept_id = models.IntegerField(db_index=True)
    visit_start_date = models.DateField(db_index=True)
    visit_end_date = models.DateField(null=True, blank=True)
    visit_type_concept_id = models.IntegerField()
    care_site_id = models.IntegerField(null=True, blank=True)

    class Meta:
        app_label = "htac"
        indexes = [
            models.Index(fields=["person", "visit_start_date"]),
            models.Index(fields=["health_system", "visit_start_date"]),
        ]

    def __str__(self):
        return f"Visit {self.pk} – {self.visit_start_date}"


class ConditionOccurrence(models.Model):
    person = models.ForeignKey(
        Person, on_delete=models.CASCADE, related_name="condition_occurrences"
    )
    health_system = models.ForeignKey(
        HealthSystem, on_delete=models.CASCADE, related_name="condition_occurrences"
    )
    condition_concept_id = models.IntegerField(db_index=True)
    condition_start_date = models.DateField(db_index=True)
    condition_end_date = models.DateField(null=True, blank=True)
    condition_type_concept_id = models.IntegerField()
    visit_occurrence = models.ForeignKey(
        VisitOccurrence,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="condition_occurrences",
    )

    class Meta:
        app_label = "htac"
        indexes = [
            models.Index(fields=["person", "condition_concept_id"]),
            models.Index(fields=["health_system", "condition_concept_id"]),
            models.Index(fields=["condition_concept_id", "condition_start_date"]),
        ]

    def __str__(self):
        return f"Condition {self.condition_concept_id} — Person {self.person_id}"


class DrugExposure(models.Model):
    person = models.ForeignKey(
        Person, on_delete=models.CASCADE, related_name="drug_exposures"
    )
    health_system = models.ForeignKey(
        HealthSystem, on_delete=models.CASCADE, related_name="drug_exposures"
    )
    drug_concept_id = models.IntegerField(db_index=True)
    drug_exposure_start_date = models.DateField(db_index=True)
    drug_exposure_end_date = models.DateField(null=True, blank=True)
    drug_type_concept_id = models.IntegerField(default=32817)  # 32817 = EHR encounter record
    quantity = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
    days_supply = models.IntegerField(null=True, blank=True)

    class Meta:
        app_label = "htac"
        indexes = [
            models.Index(fields=["person", "drug_concept_id"]),
            models.Index(fields=["health_system", "drug_concept_id"]),
            models.Index(fields=["drug_concept_id", "drug_exposure_start_date"]),
        ]

    def __str__(self):
        return f"Drug {self.drug_concept_id} — Person {self.person_id}"


class Measurement(models.Model):
    person = models.ForeignKey(
        Person, on_delete=models.CASCADE, related_name="measurements"
    )
    health_system = models.ForeignKey(
        HealthSystem, on_delete=models.CASCADE, related_name="measurements"
    )
    measurement_concept_id = models.IntegerField(db_index=True)
    measurement_date = models.DateField(db_index=True)
    measurement_type_concept_id = models.IntegerField(default=44818702)  # 44818702 = Lab result
    value_as_number = models.DecimalField(
        max_digits=20, decimal_places=6, null=True, blank=True
    )
    value_as_concept_id = models.IntegerField(null=True, blank=True)
    unit_concept_id = models.IntegerField(null=True, blank=True)

    class Meta:
        app_label = "htac"
        indexes = [
            models.Index(fields=["person", "measurement_concept_id"]),
            models.Index(fields=["health_system", "measurement_concept_id"]),
            models.Index(fields=["measurement_concept_id", "measurement_date"]),
        ]

    def __str__(self):
        return f"Measurement {self.measurement_concept_id} — Person {self.person_id}"


class Observation(models.Model):
    person = models.ForeignKey(
        Person, on_delete=models.CASCADE, related_name="observations"
    )
    health_system = models.ForeignKey(
        HealthSystem, on_delete=models.CASCADE, related_name="observations"
    )
    observation_concept_id = models.IntegerField(db_index=True)
    observation_date = models.DateField(db_index=True)
    observation_type_concept_id = models.IntegerField(default=38000280)  # 38000280 = Observation from EHR
    value_as_string = models.CharField(max_length=500, null=True, blank=True)
    value_as_number = models.DecimalField(max_digits=20, decimal_places=6, null=True, blank=True)
    value_as_concept_id = models.IntegerField(null=True, blank=True)
    unit_concept_id = models.IntegerField(null=True, blank=True)

    class Meta:
        app_label = "htac"
        indexes = [
            models.Index(fields=["person", "observation_concept_id"]),
            models.Index(fields=["health_system", "observation_concept_id"]),
            models.Index(fields=["observation_concept_id", "observation_date"]),
        ]

    def __str__(self):
        return f"Observation {self.observation_concept_id} — Person {self.person_id}"


# ─── Layer 2: Codeset ────────────────────────────────────────────────────────

class Condition(models.Model):
    """
    One of 22 HTAC health conditions, defined by a set of OMOP concept codes.
    The slug is the stable identifier used in API routes and seed fixtures.
    """
    CATEGORY_CHOICES = [
        ("cardiometabolic", "Cardiometabolic"),
        ("respiratory", "Respiratory"),
        ("mental_health", "Mental Health"),
        ("substance_use", "Substance Use"),
        ("infectious", "Infectious Disease"),
        ("neurological", "Neurological"),
        ("endocrine", "Endocrine"),
        ("renal", "Renal"),
        ("other", "Other"),
    ]

    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    htac_category = models.CharField(max_length=30, choices=CATEGORY_CHOICES)

    class Meta:
        app_label = "htac"
        ordering = ["name"]

    def __str__(self):
        return self.name


class ConceptCode(models.Model):
    DOMAIN_CHOICES = [
        ("condition", "Condition"),
        ("drug", "Drug"),
        ("measurement", "Measurement"),
        ("observation", "Observation"),
    ]
    VOCABULARY_CHOICES = [
        ("ICD10CM",  "ICD-10-CM"),
        ("SNOMED",   "SNOMED CT"),
        ("RxNorm",   "RxNorm"),
        ("LOINC",    "LOINC"),
        ("NDC",      "NDC"),
        ("CPT4",     "CPT-4"),
        ("HCPCS",    "HCPCS"),
        ("ICD10PCS", "ICD-10-PCS"),
        ("RxNorm Extension", "RxNorm Extension"),
    ]

    condition = models.ForeignKey(
        Condition, on_delete=models.CASCADE, related_name="concept_codes"
    )
    domain = models.CharField(max_length=20, choices=DOMAIN_CHOICES, db_index=True)
    concept_id = models.IntegerField(db_index=True)
    concept_name = models.CharField(max_length=500)
    vocabulary_id = models.CharField(max_length=20, choices=VOCABULARY_CHOICES)
    is_excluded = models.BooleanField(default=False)
    added_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="added_concept_codes",
    )
    added_date = models.DateField(auto_now_add=True)
    notes = models.TextField(blank=True)

    class Meta:
        app_label = "htac"
        indexes = [
            models.Index(fields=["condition", "domain"]),
            models.Index(fields=["concept_id", "vocabulary_id"]),
        ]

    def __str__(self):
        excluded = " [EXCLUDED]" if self.is_excluded else ""
        return f"{self.concept_id} ({self.vocabulary_id}) {self.concept_name}{excluded}"


# ─── Layer 3: PPRL and Enrichment ────────────────────────────────────────────

class HashToken(models.Model):
    """
    SHA-256 hex digest derived from 6 PII fields at token-generation time.
    The six source fields (first_name, last_name, dob, sex, phone, zip) are
    passed in transiently via CSV/stdin and are NEVER persisted to this model.
    """
    person = models.ForeignKey(
        Person, on_delete=models.CASCADE, related_name="hash_tokens"
    )
    health_system = models.ForeignKey(
        HealthSystem, on_delete=models.CASCADE, related_name="hash_tokens"
    )
    token = models.CharField(max_length=64, db_index=True)
    generated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = "htac"
        unique_together = [("health_system", "token")]

    def __str__(self):
        return f"{self.token[:8]}… @ {self.health_system.short_code}"


class DeduplicatedRoster(models.Model):
    """
    One record per unique patient across the network.  canonical_token is the
    SHA-256 token selected as the canonical identifier; canonical_site is the
    site with the most recent visit for patients appearing at multiple sites.
    Enrichment flags are populated by enrich_roster management command.
    """
    canonical_token = models.CharField(max_length=64, unique=True, db_index=True)
    canonical_site = models.ForeignKey(
        HealthSystem,
        on_delete=models.PROTECT,
        related_name="canonical_roster_entries",
    )
    site_count = models.IntegerField(default=1)

    # ── Medicaid enrollment (staging) ────────────────────────────────────────
    medicaid_flag = models.BooleanField(default=False)
    medicaid_effective_date = models.DateField(null=True, blank=True)

    # ── HMIS (homelessness) ──────────────────────────────────────────────────
    homeless_flag = models.BooleanField(default=False)
    homeless_first_service_date = models.DateField(null=True, blank=True)

    # ── DOC — jail ──────────────────────────────────────────────────────────
    jail_flag = models.BooleanField(default=False)
    jail_admission_date = models.DateField(null=True, blank=True)

    # ── DOC — prison ─────────────────────────────────────────────────────────
    prison_flag = models.BooleanField(default=False)
    prison_admission_date = models.DateField(null=True, blank=True)

    # ── MIIC immunization ────────────────────────────────────────────────────
    covid_vaccinated_flag = models.BooleanField(default=False)
    covid_vaccine_date = models.DateField(null=True, blank=True)
    influenza_vaccinated_flag = models.BooleanField(default=False)

    # ── Vital statistics (staging) ───────────────────────────────────────────
    deceased_flag = models.BooleanField(default=False)
    death_date = models.DateField(null=True, blank=True)

    roster_version = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = "htac"
        indexes = [
            models.Index(fields=["canonical_site"]),
            models.Index(fields=["medicaid_flag"]),
            models.Index(fields=["homeless_flag"]),
            models.Index(fields=["jail_flag"]),
            models.Index(fields=["prison_flag"]),
            models.Index(fields=["deceased_flag"]),
            models.Index(fields=["roster_version"]),
        ]

    def __str__(self):
        plural = "s" if self.site_count != 1 else ""
        return f"{self.canonical_token[:8]}… ({self.site_count} site{plural})"


# ─── Layer 4: Enrichment Source Staging ──────────────────────────────────────

class MedicaidEnrollment(models.Model):
    """Raw Medicaid enrollment rows from a state eligibility file before linkage to the roster."""
    token_hash = models.CharField(max_length=64, db_index=True)
    effective_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    coverage_type = models.CharField(max_length=100)
    source_file = models.CharField(max_length=500)
    loaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = "htac"
        indexes = [
            models.Index(fields=["token_hash", "effective_date"]),
        ]

    def __str__(self):
        return f"Medicaid {self.token_hash[:8]}… eff {self.effective_date}"


class HMISRecord(models.Model):
    """HMIS homelessness service records from a HUD-aligned HMIS feed before roster linkage."""
    SERVICE_TYPE_CHOICES = [
        ("street_outreach", "Street Outreach"),
        ("emergency_shelter", "Emergency Shelter"),
        ("transitional_housing", "Transitional Housing"),
        ("supportive_housing", "Supportive Housing"),
    ]

    token_hash = models.CharField(max_length=64, db_index=True)
    service_type = models.CharField(max_length=30, choices=SERVICE_TYPE_CHOICES)
    entry_date = models.DateField()
    exit_date = models.DateField(null=True, blank=True)
    source_file = models.CharField(max_length=500)
    loaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = "htac"
        indexes = [
            models.Index(fields=["token_hash", "entry_date"]),
        ]

    def __str__(self):
        return f"HMIS {self.service_type} {self.token_hash[:8]}…"


class DOCRecord(models.Model):
    """Corrections custody records (jail and prison) before roster linkage."""
    RECORD_TYPE_CHOICES = [
        ("jail", "Jail"),
        ("prison", "Prison"),
    ]

    token_hash = models.CharField(max_length=64, db_index=True)
    record_type = models.CharField(
        max_length=10, choices=RECORD_TYPE_CHOICES, db_index=True
    )
    admission_date = models.DateField()
    discharge_date = models.DateField(null=True, blank=True)
    facility_name = models.CharField(max_length=200)
    source_file = models.CharField(max_length=500)
    loaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = "htac"
        indexes = [
            models.Index(fields=["token_hash", "record_type"]),
        ]

    def __str__(self):
        return f"DOC {self.record_type} {self.token_hash[:8]}… adm {self.admission_date}"


class MIICRecord(models.Model):
    """Immunization information system (IIS) records before roster linkage."""
    VACCINE_TYPE_CHOICES = [
        ("covid", "COVID-19"),
        ("influenza", "Influenza"),
        ("other", "Other"),
    ]

    token_hash = models.CharField(max_length=64, db_index=True)
    vaccine_type = models.CharField(
        max_length=20, choices=VACCINE_TYPE_CHOICES, db_index=True
    )
    vaccination_date = models.DateField()
    cvx_code = models.CharField(max_length=10)
    source_file = models.CharField(max_length=500)
    loaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = "htac"
        indexes = [
            models.Index(fields=["token_hash", "vaccine_type"]),
        ]

    def __str__(self):
        return f"MIIC {self.vaccine_type} {self.token_hash[:8]}… {self.vaccination_date}"


class VitalStatisticsRecord(models.Model):
    """Civil vital statistics death records from an authorized vital records feed before roster linkage."""
    token_hash = models.CharField(max_length=64, db_index=True)
    death_date = models.DateField()
    cause_of_death_icd10 = models.CharField(max_length=10, null=True, blank=True)
    source_file = models.CharField(max_length=500)
    loaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = "htac"

    def __str__(self):
        return f"Death {self.token_hash[:8]}… {self.death_date}"


# ─── Layer 5: Analytic Output ────────────────────────────────────────────────

class StudyRun(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("running", "Running"),
        ("complete", "Complete"),
        ("failed", "Failed"),
    ]

    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    run_date = models.DateField()
    roster_version = models.DateField()
    conditions = models.ManyToManyField(
        Condition, related_name="study_runs", blank=True
    )
    run_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="study_runs",
    )
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="pending", db_index=True
    )
    notes = models.TextField(blank=True)

    class Meta:
        app_label = "htac"
        ordering = ["-run_date"]

    def __str__(self):
        return f"{self.name} ({self.run_date}) [{self.status}]"


class PrevalenceEstimate(models.Model):
    """
    One row per (study_run, condition, health_system, geo_level, geo_value,
    stratifier, stratifier_value) cell.  When is_suppressed is True the
    numerator, denominator, and prevalence_rate are set to None to prevent
    disclosure of small counts (n < 11).
    """
    GEO_LEVEL_CHOICES = [
        ("state", "State"),
        ("county", "County"),
        ("zip", "ZIP Code"),
        ("census_tract", "Census Tract"),
    ]
    STRATIFIER_CHOICES = [
        ("race", "Race"),
        ("ethnicity", "Ethnicity"),
        ("language", "Language"),
        ("sex", "Sex"),
        ("age_group", "Age Group"),
        ("homeless", "Homeless Status"),
        ("incarceration", "Incarceration Status"),
        ("medicaid", "Medicaid Status"),
        ("total", "Total"),
    ]

    study_run = models.ForeignKey(
        StudyRun, on_delete=models.CASCADE, related_name="estimates"
    )
    condition = models.ForeignKey(
        Condition, on_delete=models.CASCADE, related_name="estimates"
    )
    health_system = models.ForeignKey(
        HealthSystem,
        on_delete=models.CASCADE,
        related_name="estimates",
        null=True,
        blank=True,
        help_text="Null indicates a statewide (network-wide) aggregate.",
    )
    geo_level = models.CharField(max_length=20, choices=GEO_LEVEL_CHOICES, db_index=True)
    geo_value = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        db_index=True,
        help_text="FIPS code, ZIP, or census tract string; null for state-level rows.",
    )
    stratifier = models.CharField(
        max_length=20, choices=STRATIFIER_CHOICES, db_index=True
    )
    stratifier_value = models.CharField(max_length=100)
    numerator = models.IntegerField(
        null=True, blank=True, help_text="Null when is_suppressed is True."
    )
    denominator = models.IntegerField(
        null=True, blank=True, help_text="Null when is_suppressed is True."
    )
    prevalence_rate = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        null=True,
        blank=True,
        help_text="Cases per 10,000 persons. Null when is_suppressed is True.",
    )
    is_suppressed = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = "htac"
        indexes = [
            models.Index(fields=["study_run", "condition", "stratifier"]),
            models.Index(fields=["geo_level", "geo_value"]),
            models.Index(fields=["condition", "health_system"]),
            models.Index(fields=["study_run", "is_suppressed"]),
        ]

    def __str__(self):
        site = self.health_system.short_code if self.health_system else "statewide"
        return (
            f"{self.condition.slug} | {self.geo_level} | "
            f"{self.stratifier}={self.stratifier_value} | {site}"
        )


class DataQualityReport(models.Model):
    """
    Per-site data quality metrics written by the run_data_quality management command.
    Each row is one metric for one site on one run date.
    """
    FLAG_CHOICES = [
        ("pass", "Pass"),
        ("warn", "Warn"),
        ("fail", "Fail"),
    ]

    health_system = models.ForeignKey(
        HealthSystem, on_delete=models.CASCADE, related_name="dq_reports"
    )
    run_date = models.DateField(db_index=True)
    metric_name = models.CharField(max_length=100)
    metric_value = models.DecimalField(max_digits=12, decimal_places=4)
    flag = models.CharField(max_length=10, choices=FLAG_CHOICES, db_index=True)
    threshold = models.DecimalField(
        max_digits=12, decimal_places=4, null=True, blank=True
    )

    class Meta:
        app_label = "htac"
        ordering = ["-run_date", "health_system", "metric_name"]
        indexes = [
            models.Index(fields=["health_system", "run_date"]),
        ]

    def __str__(self):
        return (
            f"{self.health_system.short_code} | {self.metric_name} "
            f"= {self.metric_value} [{self.flag}]"
        )


from htac.models_pipeline_run import PipelineRun, PipelineStep  # noqa: E402,F401
