"""
Constants for the HTAC federated pipeline demonstration (synthetic run).

SIMULATED_SITES uses real MNEHRC member names; patient_share values are
approximate and normalized at runtime so quotas sum to TARGET_PATIENTS.
"""

from __future__ import annotations

# Maps demo site id → HealthSystem.short_code used in the OMOP database (seed_htac).
SITE_ID_TO_SHORT_CODE: dict[str, str] = {
    "allina": "ALLINA",
    "healthpartners": "HEALTHPARTNERS",
    "mhealthfairview": "MHFAIRVIEW",
    "mayoclinic": "MAYO",
    "essentiahealth": "ESSENTIA",
    "hennepinhealthcare": "HENNEPIN",
    "sanfordhealth": "SANFORD",
    "centrecare": "CENTRACARE",
    "childrensminnesota": "CHILDRENS",
    "northmemorial": "NORTHMEMORIAL",
    "minneapolisva": "VA",
}

SIMULATED_SITES = [
    {
        "id": "allina",
        "name": "Allina Health",
        "hospitals": 13,
        "clinics": 200,
        "region": "Twin Cities metro",
        "patient_share": 0.18,
    },
    {
        "id": "healthpartners",
        "name": "HealthPartners",
        "hospitals": 9,
        "clinics": 73,
        "region": "Twin Cities metro",
        "patient_share": 0.16,
    },
    {
        "id": "mhealthfairview",
        "name": "M Health Fairview",
        "hospitals": 11,
        "clinics": 91,
        "region": "Twin Cities metro and greater MN",
        "patient_share": 0.17,
    },
    {
        "id": "mayoclinic",
        "name": "Mayo Clinic",
        "hospitals": 20,
        "clinics": 56,
        "region": "Southeast Minnesota (Rochester)",
        "patient_share": 0.14,
    },
    {
        "id": "essentiahealth",
        "name": "Essentia Health",
        "hospitals": 14,
        "clinics": 80,
        "region": "Northern Minnesota and Duluth",
        "patient_share": 0.12,
    },
    {
        "id": "hennepinhealthcare",
        "name": "Hennepin Healthcare",
        "hospitals": 1,
        "clinics": 8,
        "region": "Hennepin County safety net",
        "patient_share": 0.08,
    },
    {
        "id": "sanfordhealth",
        "name": "Sanford Health",
        "hospitals": 22,
        "clinics": 172,
        "region": "Western Minnesota and Dakotas",
        "patient_share": 0.10,
    },
    {
        "id": "centrecare",
        "name": "CentraCare",
        "hospitals": 9,
        "clinics": 30,
        "region": "Central Minnesota (St. Cloud)",
        "patient_share": 0.07,
    },
    {
        "id": "childrensminnesota",
        "name": "Children's Minnesota",
        "hospitals": 2,
        "clinics": 29,
        "region": "Twin Cities pediatric",
        "patient_share": 0.04,
    },
    {
        "id": "northmemorial",
        "name": "North Memorial Health",
        "hospitals": 2,
        "clinics": 12,
        "region": "North Twin Cities metro",
        "patient_share": 0.05,
    },
    {
        "id": "minneapolisva",
        "name": "Minneapolis VA Health Care System",
        "hospitals": 2,
        "clinics": 22,
        "region": "Veterans — statewide",
        "patient_share": 0.06,
    },
]

TARGET_PATIENTS = 2500

CROSS_SITE_OVERLAP_RATE = 0.32

HOMELESS_FLAG_RATE = 0.004
INCARCERATION_FLAG_RATE = 0.012
MEDICAID_FLAG_RATE = 0.21

SUPPRESSION_THRESHOLD = 11

DEMO_CONDITIONS = [
    {"name": "Depression", "prevalence": 0.172},
    {"name": "Opioid Use Disorder", "prevalence": 0.014},
    {"name": "Hypertension", "prevalence": 0.334},
    {"name": "Asthma", "prevalence": 0.071},
    {"name": "Type 2 Diabetes", "prevalence": 0.097},
]

# Maps demo display name → Condition.slug in the database
DEMO_CONDITION_NAME_TO_SLUG: dict[str, str] = {
    "Depression": "depression",
    "Opioid Use Disorder": "opioid-use-disorder",
    "Hypertension": "hypertension",
    "Asthma": "asthma",
    "Type 2 Diabetes": "diabetes",
}

DEMO_STRATIFIERS = ["race", "homeless_status", "incarceration_status", "age_group", "total"]

GEO_LEVELS = ["state", "county"]

# PrevalenceEstimate.stratifier field codes (model uses "homeless" not "homeless_status")
STRATIFIER_MODEL_KEYS: dict[str, str] = {
    "race": "race",
    "homeless_status": "homeless",
    "incarceration_status": "incarceration",
    "age_group": "age_group",
    "total": "total",
}

PIPELINE_STEP_DEFINITIONS = [
    (1, "Clinical Data in OMOP CDM"),
    (2, "PPRL Token Generation"),
    (3, "Deduplication"),
    (4, "Administrative Data Enrichment"),
    (5, "Federated Cohort Queries"),
    (6, "Stratification and Suppression"),
    (7, "Results Published"),
]

DEMO_STUDY_NOTES_MARKER = "__DEMO_PIPELINE__"
