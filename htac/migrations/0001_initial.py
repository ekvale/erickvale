import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [

        # ── Layer 1a: HealthSystem (no htac deps) ────────────────────────────
        migrations.CreateModel(
            name="HealthSystem",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=200)),
                ("short_code", models.CharField(max_length=20, unique=True)),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "ordering": ["name"],
                "app_label": "htac",
            },
        ),

        # ── Layer 2a: Condition (no htac deps) ───────────────────────────────
        migrations.CreateModel(
            name="Condition",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=200)),
                ("slug", models.SlugField(max_length=100, unique=True)),
                ("description", models.TextField(blank=True)),
                ("is_active", models.BooleanField(default=True)),
                ("htac_category", models.CharField(
                    max_length=30,
                    choices=[
                        ("cardiometabolic", "Cardiometabolic"),
                        ("respiratory", "Respiratory"),
                        ("mental_health", "Mental Health"),
                        ("substance_use", "Substance Use"),
                        ("infectious", "Infectious Disease"),
                        ("neurological", "Neurological"),
                        ("endocrine", "Endocrine"),
                        ("renal", "Renal"),
                        ("other", "Other"),
                    ],
                )),
            ],
            options={
                "ordering": ["name"],
                "app_label": "htac",
            },
        ),

        # ── Layer 1b: Person (depends on HealthSystem) ───────────────────────
        migrations.CreateModel(
            name="Person",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("health_system", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="persons",
                    to="htac.healthsystem",
                )),
                ("person_source_value", models.CharField(
                    max_length=100,
                    help_text="Site-internal patient identifier — never shared across sites.",
                )),
                ("gender_concept_id", models.IntegerField(db_index=True)),
                ("year_of_birth", models.IntegerField()),
                ("race_concept_id", models.IntegerField(db_index=True)),
                ("ethnicity_concept_id", models.IntegerField(db_index=True)),
                ("preferred_language", models.CharField(max_length=50, blank=True)),
                ("county_fips", models.CharField(max_length=5, blank=True, db_index=True)),
                ("zip_code", models.CharField(max_length=10, blank=True, db_index=True)),
                ("census_tract", models.CharField(max_length=11, blank=True, db_index=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "app_label": "htac",
            },
        ),

        # ── Layer 1c: VisitOccurrence (depends on Person, HealthSystem) ──────
        migrations.CreateModel(
            name="VisitOccurrence",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("person", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="visits",
                    to="htac.person",
                )),
                ("health_system", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="visits",
                    to="htac.healthsystem",
                )),
                ("visit_concept_id", models.IntegerField(db_index=True)),
                ("visit_start_date", models.DateField(db_index=True)),
                ("visit_end_date", models.DateField(null=True, blank=True)),
                ("visit_type_concept_id", models.IntegerField()),
                ("care_site_id", models.IntegerField(null=True, blank=True)),
            ],
            options={
                "app_label": "htac",
            },
        ),

        # ── Layer 1d: ConditionOccurrence (depends on Person, HealthSystem, VisitOccurrence) ──
        migrations.CreateModel(
            name="ConditionOccurrence",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("person", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="condition_occurrences",
                    to="htac.person",
                )),
                ("health_system", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="condition_occurrences",
                    to="htac.healthsystem",
                )),
                ("condition_concept_id", models.IntegerField(db_index=True)),
                ("condition_start_date", models.DateField(db_index=True)),
                ("condition_end_date", models.DateField(null=True, blank=True)),
                ("condition_type_concept_id", models.IntegerField()),
                ("visit_occurrence", models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name="condition_occurrences",
                    to="htac.visitoccurrence",
                )),
            ],
            options={
                "app_label": "htac",
            },
        ),

        # ── Layer 1e: DrugExposure (depends on Person, HealthSystem) ─────────
        migrations.CreateModel(
            name="DrugExposure",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("person", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="drug_exposures",
                    to="htac.person",
                )),
                ("health_system", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="drug_exposures",
                    to="htac.healthsystem",
                )),
                ("drug_concept_id", models.IntegerField(db_index=True)),
                ("drug_exposure_start_date", models.DateField(db_index=True)),
                ("drug_exposure_end_date", models.DateField(null=True, blank=True)),
                ("quantity", models.DecimalField(decimal_places=4, max_digits=12, null=True, blank=True)),
                ("days_supply", models.IntegerField(null=True, blank=True)),
            ],
            options={
                "app_label": "htac",
            },
        ),

        # ── Layer 1f: Measurement (depends on Person, HealthSystem) ──────────
        migrations.CreateModel(
            name="Measurement",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("person", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="measurements",
                    to="htac.person",
                )),
                ("health_system", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="measurements",
                    to="htac.healthsystem",
                )),
                ("measurement_concept_id", models.IntegerField(db_index=True)),
                ("measurement_date", models.DateField(db_index=True)),
                ("value_as_number", models.DecimalField(decimal_places=6, max_digits=20, null=True, blank=True)),
                ("value_as_concept_id", models.IntegerField(null=True, blank=True)),
                ("unit_concept_id", models.IntegerField(null=True, blank=True)),
            ],
            options={
                "app_label": "htac",
            },
        ),

        # ── Layer 1g: Observation (depends on Person, HealthSystem) ──────────
        migrations.CreateModel(
            name="Observation",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("person", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="observations",
                    to="htac.person",
                )),
                ("health_system", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="observations",
                    to="htac.healthsystem",
                )),
                ("observation_concept_id", models.IntegerField(db_index=True)),
                ("observation_date", models.DateField(db_index=True)),
                ("value_as_string", models.CharField(max_length=500, null=True, blank=True)),
                ("value_as_concept_id", models.IntegerField(null=True, blank=True)),
            ],
            options={
                "app_label": "htac",
            },
        ),

        # ── Layer 2b: ConceptCode (depends on Condition, AUTH_USER_MODEL) ────
        migrations.CreateModel(
            name="ConceptCode",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("condition", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="concept_codes",
                    to="htac.condition",
                )),
                ("domain", models.CharField(
                    db_index=True,
                    max_length=20,
                    choices=[
                        ("condition", "Condition"),
                        ("drug", "Drug"),
                        ("measurement", "Measurement"),
                        ("observation", "Observation"),
                    ],
                )),
                ("concept_id", models.IntegerField(db_index=True)),
                ("concept_name", models.CharField(max_length=500)),
                ("vocabulary_id", models.CharField(
                    max_length=20,
                    choices=[
                        ("ICD10CM", "ICD-10-CM"),
                        ("SNOMED", "SNOMED CT"),
                        ("RxNorm", "RxNorm"),
                        ("LOINC", "LOINC"),
                    ],
                )),
                ("is_excluded", models.BooleanField(default=False)),
                ("added_by", models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name="added_concept_codes",
                    to=settings.AUTH_USER_MODEL,
                )),
                ("added_date", models.DateField(auto_now_add=True)),
                ("notes", models.TextField(blank=True)),
            ],
            options={
                "app_label": "htac",
            },
        ),

        # ── Layer 3a: HashToken (depends on Person, HealthSystem) ─────────────
        migrations.CreateModel(
            name="HashToken",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("person", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="hash_tokens",
                    to="htac.person",
                )),
                ("health_system", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="hash_tokens",
                    to="htac.healthsystem",
                )),
                ("token", models.CharField(max_length=64, db_index=True)),
                ("generated_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "app_label": "htac",
                "unique_together": {("health_system", "token")},
            },
        ),

        # ── Layer 3b: DeduplicatedRoster (depends on HealthSystem) ────────────
        migrations.CreateModel(
            name="DeduplicatedRoster",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("canonical_token", models.CharField(max_length=64, unique=True, db_index=True)),
                ("canonical_site", models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name="canonical_roster_entries",
                    to="htac.healthsystem",
                )),
                ("site_count", models.IntegerField(default=1)),
                ("medicaid_flag", models.BooleanField(default=False)),
                ("medicaid_effective_date", models.DateField(null=True, blank=True)),
                ("homeless_flag", models.BooleanField(default=False)),
                ("homeless_first_service_date", models.DateField(null=True, blank=True)),
                ("jail_flag", models.BooleanField(default=False)),
                ("jail_admission_date", models.DateField(null=True, blank=True)),
                ("prison_flag", models.BooleanField(default=False)),
                ("prison_admission_date", models.DateField(null=True, blank=True)),
                ("covid_vaccinated_flag", models.BooleanField(default=False)),
                ("covid_vaccine_date", models.DateField(null=True, blank=True)),
                ("influenza_vaccinated_flag", models.BooleanField(default=False)),
                ("deceased_flag", models.BooleanField(default=False)),
                ("death_date", models.DateField(null=True, blank=True)),
                ("roster_version", models.DateField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "app_label": "htac",
            },
        ),

        # ── Layer 4: Enrichment staging tables (no htac FK deps) ─────────────
        migrations.CreateModel(
            name="MedicaidEnrollment",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("token_hash", models.CharField(max_length=64, db_index=True)),
                ("effective_date", models.DateField()),
                ("end_date", models.DateField(null=True, blank=True)),
                ("coverage_type", models.CharField(max_length=100)),
                ("source_file", models.CharField(max_length=500)),
                ("loaded_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "app_label": "htac",
            },
        ),

        migrations.CreateModel(
            name="HMISRecord",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("token_hash", models.CharField(max_length=64, db_index=True)),
                ("service_type", models.CharField(
                    max_length=30,
                    choices=[
                        ("street_outreach", "Street Outreach"),
                        ("emergency_shelter", "Emergency Shelter"),
                        ("transitional_housing", "Transitional Housing"),
                        ("supportive_housing", "Supportive Housing"),
                    ],
                )),
                ("entry_date", models.DateField()),
                ("exit_date", models.DateField(null=True, blank=True)),
                ("source_file", models.CharField(max_length=500)),
                ("loaded_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "app_label": "htac",
            },
        ),

        migrations.CreateModel(
            name="DOCRecord",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("token_hash", models.CharField(max_length=64, db_index=True)),
                ("record_type", models.CharField(
                    db_index=True,
                    max_length=10,
                    choices=[
                        ("jail", "Jail"),
                        ("prison", "Prison"),
                    ],
                )),
                ("admission_date", models.DateField()),
                ("discharge_date", models.DateField(null=True, blank=True)),
                ("facility_name", models.CharField(max_length=200)),
                ("source_file", models.CharField(max_length=500)),
                ("loaded_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "app_label": "htac",
            },
        ),

        migrations.CreateModel(
            name="MIICRecord",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("token_hash", models.CharField(max_length=64, db_index=True)),
                ("vaccine_type", models.CharField(
                    db_index=True,
                    max_length=20,
                    choices=[
                        ("covid", "COVID-19"),
                        ("influenza", "Influenza"),
                        ("other", "Other"),
                    ],
                )),
                ("vaccination_date", models.DateField()),
                ("cvx_code", models.CharField(max_length=10)),
                ("source_file", models.CharField(max_length=500)),
                ("loaded_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "app_label": "htac",
            },
        ),

        migrations.CreateModel(
            name="VitalStatisticsRecord",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("token_hash", models.CharField(max_length=64, db_index=True)),
                ("death_date", models.DateField()),
                ("cause_of_death_icd10", models.CharField(max_length=10, null=True, blank=True)),
                ("source_file", models.CharField(max_length=500)),
                ("loaded_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "app_label": "htac",
            },
        ),

        # ── Layer 5a: StudyRun (depends on Condition, AUTH_USER_MODEL) ────────
        migrations.CreateModel(
            name="StudyRun",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=200)),
                ("description", models.TextField(blank=True)),
                ("run_date", models.DateField()),
                ("roster_version", models.DateField()),
                ("conditions", models.ManyToManyField(
                    blank=True,
                    related_name="study_runs",
                    to="htac.condition",
                )),
                ("run_by", models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name="study_runs",
                    to=settings.AUTH_USER_MODEL,
                )),
                ("status", models.CharField(
                    db_index=True,
                    default="pending",
                    max_length=20,
                    choices=[
                        ("pending", "Pending"),
                        ("running", "Running"),
                        ("complete", "Complete"),
                        ("failed", "Failed"),
                    ],
                )),
                ("notes", models.TextField(blank=True)),
            ],
            options={
                "ordering": ["-run_date"],
                "app_label": "htac",
            },
        ),

        # ── Layer 5b: PrevalenceEstimate (depends on StudyRun, Condition, HealthSystem) ──
        migrations.CreateModel(
            name="PrevalenceEstimate",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("study_run", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="estimates",
                    to="htac.studyrun",
                )),
                ("condition", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="estimates",
                    to="htac.condition",
                )),
                ("health_system", models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="estimates",
                    to="htac.healthsystem",
                    help_text="Null indicates a statewide (network-wide) aggregate.",
                )),
                ("geo_level", models.CharField(
                    db_index=True,
                    max_length=20,
                    choices=[
                        ("state", "State"),
                        ("county", "County"),
                        ("zip", "ZIP Code"),
                        ("census_tract", "Census Tract"),
                    ],
                )),
                ("geo_value", models.CharField(
                    blank=True,
                    db_index=True,
                    max_length=20,
                    null=True,
                    help_text="FIPS code, ZIP, or census tract string; null for state-level rows.",
                )),
                ("stratifier", models.CharField(
                    db_index=True,
                    max_length=20,
                    choices=[
                        ("race", "Race"),
                        ("ethnicity", "Ethnicity"),
                        ("language", "Language"),
                        ("sex", "Sex"),
                        ("age_group", "Age Group"),
                        ("homeless", "Homeless Status"),
                        ("incarceration", "Incarceration Status"),
                        ("medicaid", "Medicaid Status"),
                        ("total", "Total"),
                    ],
                )),
                ("stratifier_value", models.CharField(max_length=100)),
                ("numerator", models.IntegerField(
                    blank=True,
                    null=True,
                    help_text="Null when is_suppressed is True.",
                )),
                ("denominator", models.IntegerField(
                    blank=True,
                    null=True,
                    help_text="Null when is_suppressed is True.",
                )),
                ("prevalence_rate", models.DecimalField(
                    blank=True,
                    decimal_places=4,
                    max_digits=8,
                    null=True,
                    help_text="Null when is_suppressed is True.",
                )),
                ("is_suppressed", models.BooleanField(default=False, db_index=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "app_label": "htac",
            },
        ),

        # ── Layer 5c: DataQualityReport (depends on HealthSystem) ─────────────
        migrations.CreateModel(
            name="DataQualityReport",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("health_system", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="dq_reports",
                    to="htac.healthsystem",
                )),
                ("run_date", models.DateField(db_index=True)),
                ("metric_name", models.CharField(max_length=100)),
                ("metric_value", models.DecimalField(decimal_places=4, max_digits=12)),
                ("flag", models.CharField(
                    db_index=True,
                    max_length=10,
                    choices=[
                        ("pass", "Pass"),
                        ("warn", "Warn"),
                        ("fail", "Fail"),
                    ],
                )),
                ("threshold", models.DecimalField(
                    blank=True, decimal_places=4, max_digits=12, null=True
                )),
            ],
            options={
                "ordering": ["-run_date", "health_system", "metric_name"],
                "app_label": "htac",
            },
        ),

        # ── Composite indexes (Meta.indexes) ─────────────────────────────────

        # Person
        migrations.AddIndex(
            model_name="person",
            index=models.Index(fields=["health_system", "person_source_value"], name="htac_person_site_val_idx"),
        ),

        # VisitOccurrence
        migrations.AddIndex(
            model_name="visitoccurrence",
            index=models.Index(fields=["person", "visit_start_date"], name="htac_visit_person_date_idx"),
        ),
        migrations.AddIndex(
            model_name="visitoccurrence",
            index=models.Index(fields=["health_system", "visit_start_date"], name="htac_visit_site_date_idx"),
        ),

        # ConditionOccurrence
        migrations.AddIndex(
            model_name="conditionoccurrence",
            index=models.Index(fields=["person", "condition_concept_id"], name="htac_cond_person_concept_idx"),
        ),
        migrations.AddIndex(
            model_name="conditionoccurrence",
            index=models.Index(fields=["health_system", "condition_concept_id"], name="htac_cond_site_concept_idx"),
        ),
        migrations.AddIndex(
            model_name="conditionoccurrence",
            index=models.Index(fields=["condition_concept_id", "condition_start_date"], name="htac_cond_concept_date_idx"),
        ),

        # DrugExposure
        migrations.AddIndex(
            model_name="drugexposure",
            index=models.Index(fields=["person", "drug_concept_id"], name="htac_drug_person_concept_idx"),
        ),
        migrations.AddIndex(
            model_name="drugexposure",
            index=models.Index(fields=["health_system", "drug_concept_id"], name="htac_drug_site_concept_idx"),
        ),
        migrations.AddIndex(
            model_name="drugexposure",
            index=models.Index(fields=["drug_concept_id", "drug_exposure_start_date"], name="htac_drug_concept_date_idx"),
        ),

        # Measurement
        migrations.AddIndex(
            model_name="measurement",
            index=models.Index(fields=["person", "measurement_concept_id"], name="htac_meas_person_concept_idx"),
        ),
        migrations.AddIndex(
            model_name="measurement",
            index=models.Index(fields=["health_system", "measurement_concept_id"], name="htac_meas_site_concept_idx"),
        ),
        migrations.AddIndex(
            model_name="measurement",
            index=models.Index(fields=["measurement_concept_id", "measurement_date"], name="htac_meas_concept_date_idx"),
        ),

        # Observation
        migrations.AddIndex(
            model_name="observation",
            index=models.Index(fields=["person", "observation_concept_id"], name="htac_obs_person_concept_idx"),
        ),
        migrations.AddIndex(
            model_name="observation",
            index=models.Index(fields=["health_system", "observation_concept_id"], name="htac_obs_site_concept_idx"),
        ),
        migrations.AddIndex(
            model_name="observation",
            index=models.Index(fields=["observation_concept_id", "observation_date"], name="htac_obs_concept_date_idx"),
        ),

        # ConceptCode
        migrations.AddIndex(
            model_name="conceptcode",
            index=models.Index(fields=["condition", "domain"], name="htac_cc_condition_domain_idx"),
        ),
        migrations.AddIndex(
            model_name="conceptcode",
            index=models.Index(fields=["concept_id", "vocabulary_id"], name="htac_cc_concept_vocab_idx"),
        ),

        # DeduplicatedRoster
        migrations.AddIndex(
            model_name="deduplicatedroster",
            index=models.Index(fields=["canonical_site"], name="htac_roster_site_idx"),
        ),
        migrations.AddIndex(
            model_name="deduplicatedroster",
            index=models.Index(fields=["medicaid_flag"], name="htac_roster_medicaid_idx"),
        ),
        migrations.AddIndex(
            model_name="deduplicatedroster",
            index=models.Index(fields=["homeless_flag"], name="htac_roster_homeless_idx"),
        ),
        migrations.AddIndex(
            model_name="deduplicatedroster",
            index=models.Index(fields=["jail_flag"], name="htac_roster_jail_idx"),
        ),
        migrations.AddIndex(
            model_name="deduplicatedroster",
            index=models.Index(fields=["prison_flag"], name="htac_roster_prison_idx"),
        ),
        migrations.AddIndex(
            model_name="deduplicatedroster",
            index=models.Index(fields=["deceased_flag"], name="htac_roster_deceased_idx"),
        ),
        migrations.AddIndex(
            model_name="deduplicatedroster",
            index=models.Index(fields=["roster_version"], name="htac_roster_version_idx"),
        ),

        # MedicaidEnrollment
        migrations.AddIndex(
            model_name="medicaidenrollment",
            index=models.Index(fields=["token_hash", "effective_date"], name="htac_medicaid_token_date_idx"),
        ),

        # HMISRecord
        migrations.AddIndex(
            model_name="hmisrecord",
            index=models.Index(fields=["token_hash", "entry_date"], name="htac_hmis_token_date_idx"),
        ),

        # DOCRecord
        migrations.AddIndex(
            model_name="docrecord",
            index=models.Index(fields=["token_hash", "record_type"], name="htac_doc_token_type_idx"),
        ),

        # MIICRecord
        migrations.AddIndex(
            model_name="miicrecord",
            index=models.Index(fields=["token_hash", "vaccine_type"], name="htac_miic_token_type_idx"),
        ),

        # PrevalenceEstimate
        migrations.AddIndex(
            model_name="prevalenceestimate",
            index=models.Index(fields=["study_run", "condition", "stratifier"], name="htac_prev_run_cond_strat_idx"),
        ),
        migrations.AddIndex(
            model_name="prevalenceestimate",
            index=models.Index(fields=["geo_level", "geo_value"], name="htac_prev_geo_idx"),
        ),
        migrations.AddIndex(
            model_name="prevalenceestimate",
            index=models.Index(fields=["condition", "health_system"], name="htac_prev_cond_site_idx"),
        ),
        migrations.AddIndex(
            model_name="prevalenceestimate",
            index=models.Index(fields=["study_run", "is_suppressed"], name="htac_prev_run_suppressed_idx"),
        ),

        # DataQualityReport
        migrations.AddIndex(
            model_name="dataqualityreport",
            index=models.Index(fields=["health_system", "run_date"], name="htac_dqr_site_date_idx"),
        ),
    ]
