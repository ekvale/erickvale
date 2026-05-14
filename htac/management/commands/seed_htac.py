"""
htac/management/commands/seed_htac.py

Load all reference data and synthetic patient records needed to run the
full HTAC pipeline end-to-end.

What is created
---------------
1. 11 MNEHRC HealthSystem records (active)
2. Data-gap institutions: 11 MN tribal nations + 8 FQHCs (is_active=False)
3. 22 HTAC Condition records, each with ≥ 3 real OMOP concept codes
   (SNOMED / ICD-10-CM / RxNorm / LOINC — verified against OHDSI Athena)
4. 500 synthetic Person records distributed across the 11 sites with
   realistic Minnesota demographic distributions
5. VisitOccurrence records (1–4 per person)
6. ConditionOccurrence records at prevalence rates that produce
   non-suppressed statewide cells for ≥ 18 of the 22 conditions
7. A default pending StudyRun covering the 2022 calendar year

With --tokens:
8. Synthetic HashToken records derived from Minnesota-realistic fictitious PII
   (names drawn from Scandinavian/German, Somali/East African, Hmong, Latino,
   and American Indian pools matching MN demographic composition)
9. Cross-site patient linkages (~10% of patients appear at 2 sites,
   mirroring realistic specialist referral and care-transition patterns)
10. DeduplicatedRoster rows produced by running deduplicate_tokens()

DATA GAP NOTE
-------------
Federally Qualified Health Centers (FQHCs) and Tribal health programs are
registered as is_active=False HealthSystem records to make the data gap
visible in the admin and API.  No patient data is generated for these sites.
This reflects the real-world situation: as of 2024, MN FQHCs and the 11
federally recognized Tribal Nations have not been integrated into MNEHRC
infrastructure.  Outreach efforts are ongoing.

Idempotency
-----------
Health systems and conditions use get_or_create on their unique slugs /
short_codes, so re-running is safe.  For persons and clinical events, the
command skips creation if any Person records already exist for the site
(use --force to clear and recreate synthetic patient data).

USAGE
-----
  python manage.py seed_htac
  python manage.py seed_htac --tokens       # also generate HashTokens + dedup
  python manage.py seed_htac --force        # clear existing persons and re-seed
  python manage.py seed_htac --verbosity 2  # show per-site counts
"""

import datetime
import random
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from htac.models import (
    Condition,
    ConditionOccurrence,
    ConceptCode,
    DeduplicatedRoster,
    DrugExposure,
    HashToken,
    HealthSystem,
    Measurement,
    Observation,
    Person,
    StudyRun,
    VisitOccurrence,
)
from htac.services.pprl import compute_token, deduplicate_tokens

User = get_user_model()

# ── Fixed seed for reproducible synthetic data ─────────────────────────────────
_RNG = random.Random(42)

# ── Synthetic name pools (Minnesota-realistic, obviously fictitious) ───────────
# Stratified by OMOP race_concept_id and sex.  Names reflect MN's actual
# demographic composition: heavy Scandinavian/German heritage among white
# population; large Somali/East African community in Twin Cities; largest
# urban Hmong population in the US; growing Latino community; 11 Tribal Nations.

_FIRST_M = {
    # White — Scandinavian/German heritage heavy
    8527: ["Erik", "Lars", "Bjorn", "Gunnar", "Leif", "Karl", "Sven", "Magnus",
           "Heinrich", "Friedrich", "Hans", "Gustav", "James", "John", "Robert",
           "William", "David", "Richard", "Thomas", "Kenneth", "Steven", "Mark",
           "Gregory", "Timothy", "Scott", "Brian", "Kevin", "Douglas", "Gary",
           "Dennis", "Roger", "Craig", "Randy", "Dale", "Troy", "Chad", "Brett"],
    # Black / African American — includes Somali and East African names
    8516: ["Mohamed", "Ahmed", "Omar", "Hassan", "Abdi", "Ibrahim", "Yusuf",
           "Khalid", "Abdullahi", "Sadiq", "Mahad", "Faisal", "Daud", "Hodan",
           "Marcus", "DeShawn", "Jerome", "Tyrone", "Darnell", "Jamal", "Kendrick",
           "Andre", "Terrence", "Malik", "Brandon", "Jalen", "Isaiah", "Elijah",
           "Darius", "Marquis", "DeAndre", "Lamar", "Quincy", "Reginald"],
    # Asian — Hmong names (MN has the largest urban Hmong community in the US)
    8515: ["Ka", "Pao", "Vue", "Yer", "Xai", "Neng", "Toua", "Dang", "Blong",
           "Thai", "Chong", "Lue", "Chue", "Gao", "Sia", "Kou", "Shoua", "Nhia",
           "Keng", "Ger", "Txooj", "Huab", "Zong", "Ntxhais", "Hlub", "Tshiab"],
    # American Indian / Alaska Native — MN tribal nations
    8657: ["Joseph", "Thomas", "James", "William", "Michael", "Robert", "John",
           "Raymond", "Gerald", "Leonard", "Harold", "Eugene", "Alfred", "Vernon",
           "Leroy", "Russell", "Wayne", "Roy", "Norman", "Clifford", "Marvin",
           "Dennis", "Darrell", "Floyd", "Glen", "Lyle", "Orville", "Wilbur"],
    # Hispanic / Latino
    "hispanic": ["Jose", "Juan", "Miguel", "Carlos", "Luis", "Antonio", "Jorge",
                 "Ricardo", "Manuel", "Francisco", "Eduardo", "Alejandro", "Sergio",
                 "Hector", "Roberto", "Diego", "Pablo", "Ernesto", "Gabriel",
                 "Oscar", "Raul", "Cesar", "Marco", "Felix", "Victor", "Andres"],
    # Fallback
    "default": ["James", "John", "Robert", "Michael", "William", "David",
                "Richard", "Joseph", "Thomas", "Charles", "Christopher"],
}

_FIRST_F = {
    8527: ["Ingrid", "Astrid", "Sigrid", "Helga", "Kirsten", "Britta", "Signe",
           "Solveig", "Gertrude", "Margaret", "Dorothy", "Betty", "Helen",
           "Sandra", "Donna", "Carol", "Ruth", "Sharon", "Karen", "Lisa",
           "Nancy", "Michelle", "Patricia", "Mary", "Barbara", "Linda", "Susan",
           "Deborah", "Cynthia", "Cheryl", "Kathleen", "Amy", "Angela", "Melissa"],
    8516: ["Fatima", "Amina", "Khadija", "Safia", "Hodan", "Asha", "Ifrah",
           "Yasmin", "Ubah", "Maryam", "Hawo", "Sagal", "Faadumo", "Nimco",
           "Shaniqua", "LaShonda", "Tamara", "Keisha", "Monique", "Latoya",
           "Angela", "Tiffany", "Aaliyah", "Destiny", "Jasmine", "Imani",
           "Shanice", "Latasha", "Yolanda", "Tanesha", "Rochelle", "Lakisha"],
    8515: ["Pa", "Zoua", "Chia", "Maiv", "Nhia", "Kia", "Youa", "Hli", "Chai",
           "Yer", "Nkauj", "Paj", "Tswb", "Nou", "Suab", "Hnub", "Hlub",
           "Ntxhais", "Txhiab", "Siab", "Dawb", "Npliag", "Pog", "Ntxhi"],
    8657: ["Mary", "Patricia", "Sandra", "Barbara", "Donna", "Linda", "Carol",
           "Betty", "Ruth", "Alice", "Dorothy", "Gloria", "Shirley", "Lorraine",
           "Irene", "Vivian", "Frances", "Edna", "Agnes", "Beatrice", "Lucille",
           "Gladys", "Mildred", "Ethel", "Hazel", "Bertha", "Lillian", "Viola"],
    "hispanic": ["Maria", "Ana", "Rosa", "Carmen", "Elena", "Luisa", "Isabel",
                 "Valentina", "Sofia", "Guadalupe", "Adriana", "Veronica",
                 "Esperanza", "Cecilia", "Alicia", "Monica", "Diana", "Norma",
                 "Yolanda", "Leticia", "Blanca", "Silvia", "Marisol", "Rocio"],
    "default": ["Mary", "Patricia", "Jennifer", "Linda", "Barbara", "Elizabeth",
                "Susan", "Jessica", "Karen", "Sarah", "Lisa", "Nancy", "Betty"],
}

_LAST = {
    8527: ["Anderson", "Johnson", "Nelson", "Peterson", "Olson", "Hansen",
           "Larson", "Berg", "Carlson", "Lindberg", "Gustafson", "Erikson",
           "Lundgren", "Bergstrom", "Swenson", "Thorsen", "Halvorsen",
           "Magnusson", "Schmidt", "Mueller", "Fischer", "Wagner", "Bauer",
           "Weber", "Koch", "Hoffman", "Meyer", "Klein", "Wolf", "Braun",
           "Schultz", "Zimmermann", "Schroeder", "Thompson", "Williams"],
    8516: ["Hassan", "Mohamed", "Omar", "Hussein", "Ali", "Ahmed", "Abdi",
           "Warsame", "Farah", "Osman", "Diriye", "Shire", "Duale", "Hersi",
           "Jackson", "Williams", "Johnson", "Brown", "Davis", "Robinson",
           "Wilson", "Anderson", "Thomas", "Taylor", "Harris", "Washington",
           "Martin", "Thompson", "Moore", "White", "Walker", "Lewis"],
    8515: ["Vang", "Yang", "Lee", "Xiong", "Thao", "Kong", "Her", "Moua",
           "Cha", "Vue", "Lo", "Pha", "Hang", "Khang", "Chang", "Ly",
           "Lor", "Kue", "Fang", "Pao", " Vue", "Kang", "Muas", "Lis"],
    8657: ["Bressette", "Wadena", "Vizenor", "DeCoteau", "LaFave", "BigEagle",
           "Treuer", "Bellecourt", "Cloud", "Houle", "Gourneau", "LaDuke",
           "Northbird", "Morriseau", "Sharlow", "Henry", "Wind", "Auginaush",
           "StandingCloud", "Graves", "Lyons", "Swifthawk", "Beaulieu",
           "Fairbanks", "Downwind", "Broker", "Erdrich", "Jourdain"],
    "hispanic": ["Garcia", "Martinez", "Rodriguez", "Hernandez", "Lopez",
                 "Gonzalez", "Perez", "Sanchez", "Ramirez", "Torres", "Flores",
                 "Rivera", "Gomez", "Diaz", "Reyes", "Cruz", "Morales", "Ortiz",
                 "Gutierrez", "Chavez", "Vargas", "Castillo", "Jimenez", "Romero"],
    "default": ["Smith", "Jones", "Miller", "Davis", "Wilson", "Moore",
                "Taylor", "Anderson", "Thomas", "Jackson", "White", "Harris"],
}

# Phone area codes by site service region
_SITE_AREA_CODES = {
    "ALLINA":         ["612", "651", "763", "952"],
    "CENTRACARE":     ["320", "651"],
    "CHILDRENS":      ["612", "651", "763", "952"],
    "ESSENTIA":       ["218"],
    "HEALTHPARTNERS": ["651", "612", "763", "952"],
    "HENNEPIN":       ["612", "763"],
    "MHFAIRVIEW":     ["612", "651", "763", "952"],
    "MAYO":           ["507"],
    "NORTHMEMORIAL":  ["763", "612"],
    "SANFORD":        ["507", "320"],
    "VA":             ["612", "651", "952"],
}

# Cross-site patient linkages — (from_site, to_site, fraction_of_from_site)
# Based on realistic MN care-transition patterns:
#   VA → ALLINA: veterans transitioning to community care
#   ALLINA ↔ MAYO: specialty referrals (Rochester)
#   HENNEPIN → NORTHMEMORIAL: north Minneapolis corridor
#   MHFAIRVIEW ↔ HEALTHPARTNERS: Twin Cities market overlap
#   ESSENTIA → MAYO: rural-to-specialty pipeline (NE MN to Rochester)
#   CENTRACARE → MHFAIRVIEW: St. Cloud patients seeking sub-specialty
#   SANFORD → MAYO: SW MN to Rochester specialty
CROSS_SITE_PAIRS = [
    ("VA",            "ALLINA",         0.10),
    ("ALLINA",        "MAYO",           0.07),
    ("MHFAIRVIEW",    "HEALTHPARTNERS", 0.06),
    ("HENNEPIN",      "NORTHMEMORIAL",  0.08),
    ("ESSENTIA",      "MAYO",           0.07),
    ("CENTRACARE",    "MHFAIRVIEW",     0.05),
    ("SANFORD",       "MAYO",           0.08),
]

# ── Data-gap institutions (is_active=False) ────────────────────────────────────
# These appear in admin/API to make the structural data gap visible.
# No patient data is generated for these sites.

TRIBAL_NATIONS = [
    ("Bois Forte Band Health Program",                   "BOIS_FORTE_TRIBAL"),
    ("Fond du Lac Band Health Division",                 "FOND_DU_LAC_TRIBAL"),
    ("Grand Portage Band Health Program",                "GRAND_PORTAGE_TRIBAL"),
    ("Leech Lake Band Health & Human Services",          "LEECH_LAKE_TRIBAL"),
    ("Lower Sioux Indian Community Health",              "LOWER_SIOUX_TRIBAL"),
    ("Mille Lacs Band Health & Human Services",          "MILLE_LACS_TRIBAL"),
    ("Prairie Island Indian Community Health",           "PRAIRIE_ISLAND_TRIBAL"),
    ("Red Lake Nation Health Services",                  "RED_LAKE_TRIBAL"),
    ("Shakopee Mdewakanton Sioux Health Program",        "SHAKOPEE_TRIBAL"),
    ("Upper Sioux Community Health (Pezihutazizi Oyate)","UPPER_SIOUX_TRIBAL"),
    ("White Earth Nation Health Services",               "WHITE_EARTH_TRIBAL"),
]

FQHC_INSTITUTIONS = [
    ("NorthPoint Health & Wellness Center",              "NORTHPOINT_FQHC"),
    ("Minnesota Community Care",                         "MN_COMMUNITY_CARE_FQHC"),
    ("Open Door Health Center",                          "OPEN_DOOR_FQHC"),
    ("Virginia Community Health Center",                 "VIRGINIA_CHC_FQHC"),
    ("Native American Community Clinic",                 "NACC_FQHC"),
    ("Comunidades Latinas Unidas En Servicio (CLUES)",   "CLUES_FQHC"),
    ("WellShare International",                          "WELLSHARE_FQHC"),
    ("Central MN Community Empowerment Org",             "CMCEO_FQHC"),
]

# ── 1. Health systems ──────────────────────────────────────────────────────────

HEALTH_SYSTEMS = [
    ("Allina Health",         "ALLINA"),
    ("CentraCare",            "CENTRACARE"),
    ("Children's Minnesota",  "CHILDRENS"),
    ("Essentia Health",       "ESSENTIA"),
    ("HealthPartners",        "HEALTHPARTNERS"),
    ("Hennepin Healthcare",   "HENNEPIN"),
    ("M Health Fairview",     "MHFAIRVIEW"),
    ("Mayo Clinic",           "MAYO"),
    ("North Memorial Health", "NORTHMEMORIAL"),
    ("Sanford Health",        "SANFORD"),
    ("Minneapolis VA",        "VA"),
]

# Persons per site — total = 500
SITE_SIZES = {
    "ALLINA":         65,
    "CENTRACARE":     35,
    "CHILDRENS":      25,
    "ESSENTIA":       40,
    "HEALTHPARTNERS": 65,
    "HENNEPIN":       60,
    "MHFAIRVIEW":     55,
    "MAYO":           50,
    "NORTHMEMORIAL":  25,
    "SANFORD":        30,
    "VA":             50,
}

# ── 2. Conditions + OMOP concept codes ────────────────────────────────────────
# Concept IDs sourced from OHDSI Athena (athena.ohdsi.org).
# domain choices: condition / drug / measurement / observation
# vocabulary_id choices: SNOMED / ICD10CM / RxNorm / LOINC

CONDITIONS_DATA = [
    {
        "name": "Diabetes",
        "slug": "diabetes",
        "category": "endocrine",
        "description": "Type 2 diabetes mellitus and insulin-related conditions.",
        "codes": [
            (201826,  "Type 2 diabetes mellitus",                       "condition",   "SNOMED"),
            (442793,  "Type 2 diabetes mellitus with complications",     "condition",   "SNOMED"),
            (1503297, "Metformin",                                       "drug",        "RxNorm"),
            (3004410, "Hemoglobin A1c/Hemoglobin.total in Blood",        "measurement", "LOINC"),
        ],
    },
    {
        "name": "Hypertension",
        "slug": "hypertension",
        "category": "cardiometabolic",
        "description": "Essential and secondary hypertension.",
        "codes": [
            (320128,  "Essential hypertension",                          "condition",   "SNOMED"),
            (316866,  "Hypertensive disorder, systemic arterial",        "condition",   "SNOMED"),
            (1308216, "Lisinopril",                                      "drug",        "RxNorm"),
            (3004249, "Systolic blood pressure",                         "measurement", "LOINC"),
        ],
    },
    {
        "name": "Asthma",
        "slug": "asthma",
        "category": "respiratory",
        "description": "Asthma of any severity or type.",
        "codes": [
            (317009,  "Asthma",                                          "condition",   "SNOMED"),
            (4283893, "Mild persistent asthma",                          "condition",   "SNOMED"),
            (4116495, "Moderate persistent asthma",                      "condition",   "SNOMED"),
            (1154343, "Albuterol",                                       "drug",        "RxNorm"),
        ],
    },
    {
        "name": "COPD",
        "slug": "copd",
        "category": "respiratory",
        "description": "Chronic obstructive pulmonary disease.",
        "codes": [
            (255573,  "Chronic obstructive lung disease",                "condition",   "SNOMED"),
            (4275260, "Chronic obstructive pulmonary disease with acute lower respiratory infection", "condition", "SNOMED"),
            (1137529, "Tiotropium",                                      "drug",        "RxNorm"),
        ],
    },
    {
        "name": "Depression",
        "slug": "depression",
        "category": "mental_health",
        "description": "Major depressive disorder and depressive episodes.",
        "codes": [
            (440383,  "Depressive disorder",                             "condition",   "SNOMED"),
            (4152280, "Major depression, single episode",                "condition",   "SNOMED"),
            (4152981, "Recurrent major depressive disorder",             "condition",   "SNOMED"),
            (738156,  "Sertraline",                                      "drug",        "RxNorm"),
        ],
    },
    {
        "name": "Anxiety",
        "slug": "anxiety",
        "category": "mental_health",
        "description": "Generalized anxiety disorder and related anxiety conditions.",
        "codes": [
            (441542,  "Anxiety disorder",                                "condition",   "SNOMED"),
            (4022511, "Generalized anxiety disorder",                    "condition",   "SNOMED"),
            (441822,  "Panic disorder",                                  "condition",   "SNOMED"),
        ],
    },
    {
        "name": "Substance Use Disorder",
        "slug": "substance-use-disorder",
        "category": "substance_use",
        "description": "Alcohol and drug use disorders excluding opioids (captured separately).",
        "codes": [
            (433753,  "Alcohol dependence",                              "condition",   "SNOMED"),
            (440069,  "Alcohol abuse",                                   "condition",   "SNOMED"),
            (4029381, "Drug dependence",                                 "condition",   "SNOMED"),
        ],
    },
    {
        "name": "Obesity",
        "slug": "obesity",
        "category": "cardiometabolic",
        "description": "Obesity (BMI ≥ 30) and morbid obesity.",
        "codes": [
            (433736,  "Obesity",                                         "condition",   "SNOMED"),
            (4215968, "Morbid obesity",                                  "condition",   "SNOMED"),
            (3038553, "Body mass index",                                 "measurement", "LOINC"),
        ],
    },
    {
        "name": "Heart Failure",
        "slug": "heart-failure",
        "category": "cardiometabolic",
        "description": "Systolic and diastolic heart failure, any stage.",
        "codes": [
            (316139,  "Heart failure",                                   "condition",   "SNOMED"),
            (4229440, "Chronic heart failure",                           "condition",   "SNOMED"),
            (40226742,"Heart failure with reduced ejection fraction",    "condition",   "SNOMED"),
            (1308216, "Lisinopril",                                      "drug",        "RxNorm"),
        ],
    },
    {
        "name": "CKD",
        "slug": "ckd",
        "category": "renal",
        "description": "Chronic kidney disease, stages 1–5.",
        "codes": [
            (443601,  "Chronic kidney disease",                          "condition",   "SNOMED"),
            (46271022,"Chronic kidney disease stage 3",                  "condition",   "SNOMED"),
            (3020891, "Creatinine [Mass/volume] in Serum or Plasma",     "measurement", "LOINC"),
            (3048741, "Glomerular filtration rate/1.73 sq M.predicted",  "measurement", "LOINC"),
        ],
    },
    {
        "name": "CAD",
        "slug": "cad",
        "category": "cardiometabolic",
        "description": "Coronary artery disease and coronary arteriosclerosis.",
        "codes": [
            (317576,  "Coronary arteriosclerosis",                       "condition",   "SNOMED"),
            (4043731, "Acute myocardial infarction",                     "condition",   "SNOMED"),
            (312327,  "Acute myocardial infarction of anterior wall",    "condition",   "SNOMED"),
        ],
    },
    {
        "name": "Hyperlipidemia",
        "slug": "hyperlipidemia",
        "category": "cardiometabolic",
        "description": "Hyperlipidemia and hypercholesterolemia.",
        "codes": [
            (432867,  "Hyperlipidemia",                                  "condition",   "SNOMED"),
            (4311768, "Hypercholesterolemia",                            "condition",   "SNOMED"),
            (1545958, "Atorvastatin",                                    "drug",        "RxNorm"),
            (3027114, "Cholesterol [Mass/volume] in Serum or Plasma",    "measurement", "LOINC"),
        ],
    },
    {
        "name": "Hypothyroidism",
        "slug": "hypothyroidism",
        "category": "endocrine",
        "description": "Primary and secondary hypothyroidism.",
        "codes": [
            (140673,  "Hypothyroidism",                                  "condition",   "SNOMED"),
            (4218106, "Primary hypothyroidism",                          "condition",   "SNOMED"),
            (1592744, "Levothyroxine",                                   "drug",        "RxNorm"),
        ],
    },
    {
        "name": "Atrial Fibrillation",
        "slug": "atrial-fibrillation",
        "category": "cardiometabolic",
        "description": "Atrial fibrillation and flutter.",
        "codes": [
            (313217,  "Atrial fibrillation",                             "condition",   "SNOMED"),
            (4068155, "Paroxysmal atrial fibrillation",                  "condition",   "SNOMED"),
            (4195694, "Persistent atrial fibrillation",                  "condition",   "SNOMED"),
        ],
    },
    {
        "name": "PTSD",
        "slug": "ptsd",
        "category": "mental_health",
        "description": "Post-traumatic stress disorder.",
        "codes": [
            (436676,  "Post-traumatic stress disorder",                  "condition",   "SNOMED"),
            (4153263, "Post-traumatic stress disorder, chronic",         "condition",   "SNOMED"),
            (4153264, "Post-traumatic stress disorder, acute",           "condition",   "SNOMED"),
        ],
    },
    {
        "name": "Schizophrenia",
        "slug": "schizophrenia",
        "category": "mental_health",
        "description": "Schizophrenia spectrum disorders.",
        "codes": [
            (435783,  "Schizophrenia",                                   "condition",   "SNOMED"),
            (4327541, "Paranoid schizophrenia",                          "condition",   "SNOMED"),
            (4085936, "Residual schizophrenia",                          "condition",   "SNOMED"),
        ],
    },
    {
        "name": "Bipolar Disorder",
        "slug": "bipolar-disorder",
        "category": "mental_health",
        "description": "Bipolar I and II disorder.",
        "codes": [
            (436665,  "Bipolar disorder",                                "condition",   "SNOMED"),
            (4048379, "Bipolar I disorder",                              "condition",   "SNOMED"),
            (4048380, "Bipolar II disorder",                             "condition",   "SNOMED"),
        ],
    },
    {
        "name": "Opioid Use Disorder",
        "slug": "opioid-use-disorder",
        "category": "substance_use",
        "description": "Opioid use disorder, dependence, and abuse.",
        "codes": [
            (440607,  "Opioid abuse",                                    "condition",   "SNOMED"),
            (4145085, "Opioid dependence",                               "condition",   "SNOMED"),
            (1049648, "Buprenorphine",                                   "drug",        "RxNorm"),
        ],
    },
    {
        "name": "HIV",
        "slug": "hiv",
        "category": "infectious",
        "description": "HIV infection and AIDS.",
        "codes": [
            (439727,  "Human immunodeficiency virus infection",          "condition",   "SNOMED"),
            (4151534, "HIV disease",                                     "condition",   "SNOMED"),
            (4134325, "AIDS",                                            "condition",   "SNOMED"),
        ],
    },
    {
        "name": "Hepatitis C",
        "slug": "hepatitis-c",
        "category": "infectious",
        "description": "Chronic hepatitis C infection.",
        "codes": [
            (193253,  "Hepatitis C",                                     "condition",   "SNOMED"),
            (4029283, "Chronic hepatitis C",                             "condition",   "SNOMED"),
            (45757474,"Chronic hepatitis C without mention of hepatic coma", "condition", "SNOMED"),
        ],
    },
    {
        "name": "Dementia",
        "slug": "dementia",
        "category": "neurological",
        "description": "Alzheimer's disease and other dementias.",
        "codes": [
            (372610,  "Alzheimer's disease",                             "condition",   "SNOMED"),
            (4182210, "Dementia",                                        "condition",   "SNOMED"),
            (4028965, "Vascular dementia",                               "condition",   "SNOMED"),
        ],
    },
    {
        "name": "Stroke",
        "slug": "stroke",
        "category": "neurological",
        "description": "Ischemic stroke and cerebral infarction.",
        "codes": [
            (443454,  "Cerebral infarction",                             "condition",   "SNOMED"),
            (381591,  "Stroke",                                          "condition",   "SNOMED"),
            (4148906, "Ischemic stroke",                                 "condition",   "SNOMED"),
        ],
    },
]

# ── 3. Demographic distributions (Minnesota population-based) ─────────────────

# OMOP standard concept IDs
GENDER_WEIGHTS   = [(8507, "Male", 0.49), (8532, "Female", 0.51)]
RACE_WEIGHTS     = [
    (8527, "White",                                      0.79),
    (8516, "Black or African American",                  0.07),
    (8515, "Asian",                                      0.05),
    (8657, "American Indian or Alaska Native",           0.02),
    (8557, "Native Hawaiian or Other Pacific Islander",  0.01),
    (8522, "Other Race",                                 0.03),
    (0,    "Unknown",                                    0.03),
]
ETHNICITY_WEIGHTS = [
    (38003564, "Not Hispanic or Latino", 0.92),
    (38003563, "Hispanic or Latino",     0.06),
    (0,        "Unknown",                0.02),
]
LANGUAGES = [
    ("English", 0.82), ("Spanish", 0.06), ("Somali", 0.04),
    ("Hmong", 0.03), ("Vietnamese", 0.02), ("Other", 0.03),
]

# MN county FIPS codes (site-appropriate)
SITE_COUNTIES = {
    "ALLINA":         ["27053", "27123", "27003", "27037"],   # Metro
    "CENTRACARE":     ["27145", "27009", "27067"],             # Stearns area
    "CHILDRENS":      ["27053", "27123", "27037"],             # Metro
    "ESSENTIA":       ["27137", "27061", "27075"],             # St. Louis / N MN
    "HEALTHPARTNERS": ["27053", "27123", "27163", "27037"],    # Metro
    "HENNEPIN":       ["27053"],                               # Hennepin only
    "MHFAIRVIEW":     ["27053", "27123", "27163"],             # Metro
    "MAYO":           ["27109", "27045", "27157"],             # SE MN
    "NORTHMEMORIAL":  ["27053", "27003"],                      # Hennepin / Anoka
    "SANFORD":        ["27051", "27167", "27169"],             # SW MN
    "VA":             ["27053", "27123"],                      # Metro
}

# One representative ZIP per county FIPS (simplified)
COUNTY_ZIP = {
    "27053": "55401", "27123": "55101", "27003": "55303", "27037": "55122",
    "27163": "55082", "27139": "55378", "27019": "55318", "27145": "56301",
    "27009": "56303", "27067": "56258", "27137": "55802", "27061": "55744",
    "27075": "56431", "27109": "55901", "27045": "55024", "27157": "55944",
    "27051": "56232", "27167": "56187", "27169": "56001",
}

# Census tract placeholder (11 chars) — one per county for simulation
COUNTY_TRACT = {fips: f"{fips}000100" for fips in COUNTY_ZIP}

# ── 4. Condition prevalence rates ─────────────────────────────────────────────
# Site-adjusted multipliers for realism (VA = older/more-male, etc.)
BASE_PREVALENCE = {
    "diabetes":             0.12,
    "hypertension":         0.33,
    "asthma":               0.09,
    "copd":                 0.06,
    "depression":           0.18,
    "anxiety":              0.20,
    "substance-use-disorder": 0.06,
    "obesity":              0.30,
    "heart-failure":        0.05,
    "ckd":                  0.06,
    "cad":                  0.07,
    "hyperlipidemia":       0.25,
    "hypothyroidism":       0.09,
    "atrial-fibrillation":  0.05,
    "ptsd":                 0.05,
    "schizophrenia":        0.01,
    "bipolar-disorder":     0.03,
    "opioid-use-disorder":  0.03,
    "hiv":                  0.01,
    "hepatitis-c":          0.02,
    "dementia":             0.04,
    "stroke":               0.03,
}

# Drug concept IDs per condition slug (from CONDITIONS_DATA, drug domain only)
COND_DRUG_CONCEPTS: dict[str, list[int]] = {
    "diabetes":             [1503297],           # Metformin
    "hypertension":         [1308216],           # Lisinopril
    "asthma":               [1154343],           # Albuterol
    "copd":                 [1137529],           # Tiotropium
    "depression":           [738156],            # Sertraline
    "heart-failure":        [1308216],           # Lisinopril
    "hyperlipidemia":       [1545958],           # Atorvastatin
    "hypothyroidism":       [1592744],           # Levothyroxine
    "opioid-use-disorder":  [1049648],           # Buprenorphine
}

# Measurement concept IDs per condition slug + realistic (lo, hi) value ranges
COND_MEAS_CONCEPTS: dict[str, list[tuple[int, float, float]]] = {
    "diabetes":         [(3004410, 5.5, 12.0)],     # HbA1c %
    "hypertension":     [(3004249, 100.0, 180.0)],  # Systolic BP mmHg
    "obesity":          [(3038553, 25.0, 50.0)],    # BMI kg/m²
    "ckd":              [(3020891, 0.5, 6.0),        # Creatinine mg/dL
                         (3048741, 10.0, 120.0)],   # GFR mL/min/1.73m²
    "hyperlipidemia":   [(3027114, 120.0, 320.0)],  # Cholesterol mg/dL
}

# OMOP standard type concept IDs used in seeded records
_DRUG_TYPE_EHR       = 32817    # EHR encounter record
_MEAS_TYPE_LAB       = 44818702 # Lab result

SITE_MULTIPLIERS = {
    # VA: higher PTSD, SUD, CAD, COPD; older male population
    "VA": {
        "ptsd": 4.0, "substance-use-disorder": 2.0, "opioid-use-disorder": 1.5,
        "cad": 1.8, "copd": 1.5, "hypertension": 1.4, "depression": 1.6,
        "heart-failure": 1.5, "atrial-fibrillation": 1.4,
    },
    # Children's: lower adult chronic conditions, higher asthma
    "CHILDRENS": {
        "asthma": 2.0, "diabetes": 0.3, "hypertension": 0.1, "cad": 0.05,
        "heart-failure": 0.05, "copd": 0.05, "dementia": 0.0,
        "atrial-fibrillation": 0.1, "stroke": 0.1,
    },
    # Hennepin: higher homelessness-associated conditions
    "HENNEPIN": {
        "substance-use-disorder": 2.0, "opioid-use-disorder": 2.0,
        "hiv": 3.0, "hepatitis-c": 2.5, "schizophrenia": 2.0,
        "ptsd": 1.5, "depression": 1.3,
    },
}

# ── OMOP visit type concept ────────────────────────────────────────────────────
VISIT_TYPE_CONCEPT = 9202    # Outpatient visit
VISIT_CONCEPT_AMB  = 9202    # Outpatient
VISIT_CONCEPT_IP   = 9201    # Inpatient

# Study period for condition occurrence dates
STUDY_START = datetime.date(2020, 1, 1)
STUDY_END   = datetime.date(2022, 12, 31)


class Command(BaseCommand):
    help = "Seed all reference data and synthetic patient records for the HTAC app."

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Delete existing Person / clinical event records and re-seed.",
        )
        parser.add_argument(
            "--tokens",
            action="store_true",
            help=(
                "Generate synthetic HashToken records and run PPRL deduplication. "
                "Uses Minnesota-realistic fictitious PII; no real data is used or stored."
            ),
        )

    def handle(self, *args, **options):
        force: bool    = options["force"]
        gen_tokens: bool = options["tokens"]
        verbosity: int = options["verbosity"]

        with transaction.atomic():
            sites       = self._seed_health_systems(verbosity)
            self._seed_data_gap_institutions(verbosity)
            conditions  = self._seed_conditions(verbosity)
            self._seed_persons(sites, conditions, force, verbosity)
            self._seed_study_run(conditions, verbosity)

        if gen_tokens:
            self._seed_tokens(sites, force, verbosity)

        self.stdout.write(self.style.SUCCESS("Seed complete."))

    # ── Health systems ────────────────────────────────────────────────────────

    def _seed_health_systems(self, verbosity):
        sites = {}
        for name, code in HEALTH_SYSTEMS:
            hs, created = HealthSystem.objects.get_or_create(
                short_code=code,
                defaults={"name": name, "is_active": True},
            )
            sites[code] = hs
            if verbosity >= 2:
                tag = "created" if created else "exists"
                self.stdout.write(f"  HealthSystem {code}: {tag}")
        self.stdout.write(f"Health systems: {len(sites)}")
        return sites

    # ── Conditions ────────────────────────────────────────────────────────────

    def _seed_conditions(self, verbosity):
        conditions = {}
        for cdata in CONDITIONS_DATA:
            cond, created = Condition.objects.get_or_create(
                slug=cdata["slug"],
                defaults={
                    "name":         cdata["name"],
                    "description":  cdata["description"],
                    "htac_category": cdata["category"],
                    "is_active":    True,
                },
            )
            conditions[cdata["slug"]] = cond

            for concept_id, concept_name, domain, vocab in cdata["codes"]:
                ConceptCode.objects.get_or_create(
                    condition=cond,
                    concept_id=concept_id,
                    defaults={
                        "concept_name": concept_name,
                        "domain":       domain,
                        "vocabulary_id": vocab,
                        "is_excluded":  False,
                    },
                )

            if verbosity >= 2:
                tag = "created" if created else "exists"
                self.stdout.write(
                    f"  Condition '{cond.name}': {tag}  "
                    f"({cond.concept_codes.count()} codes)"
                )

        self.stdout.write(f"Conditions: {len(conditions)}")
        return conditions

    # ── Persons + clinical events ─────────────────────────────────────────────

    def _seed_persons(self, sites, conditions, force, verbosity):
        total_existing = Person.objects.filter(
            health_system__in=sites.values()
        ).count()

        if total_existing and not force:
            self.stdout.write(
                self.style.WARNING(
                    f"Found {total_existing} existing Person records — skipping person seed. "
                    "Use --force to clear and recreate."
                )
            )
            return

        if force and total_existing:
            n, _ = Person.objects.filter(health_system__in=sites.values()).delete()
            self.stdout.write(f"Cleared {n} existing records (cascades visits, conditions, drugs, measurements).")

        # Pre-build weighted choice helpers
        gender_pop    = [(cid, w) for cid, _, w in GENDER_WEIGHTS]
        race_pop      = [(cid, w) for cid, _, w in RACE_WEIGHTS]
        ethnicity_pop = [(cid, w) for cid, _, w in ETHNICITY_WEIGHTS]
        lang_pop      = [(lang, w) for lang, w in LANGUAGES]

        def wchoice(population):
            items, weights = zip(*population)
            return _RNG.choices(items, weights=weights, k=1)[0]

        # Build primary concept_id per condition (first non-excluded condition-domain code)
        cond_concept = {}
        for slug, cond in conditions.items():
            cc = cond.concept_codes.filter(
                domain="condition", is_excluded=False
            ).first()
            if cc:
                cond_concept[slug] = cc.concept_id

        total_persons = 0
        total_visits  = 0
        total_co      = 0
        total_drugs   = 0
        total_meas    = 0

        person_bulk   = []
        visit_bulk    = []
        co_bulk       = []
        drug_bulk     = []
        meas_bulk     = []

        # We build Person objects first to get DB IDs before creating FKs
        for code, hs in sites.items():
            n_persons   = SITE_SIZES.get(code, 40)
            mults       = SITE_MULTIPLIERS.get(code, {})
            counties    = SITE_COUNTIES.get(code, ["27053"])

            # VA: skew older (born 1940–1975) and predominantly male
            is_va       = code == "VA"
            is_childrens = code == "CHILDRENS"

            site_persons = []
            for i in range(n_persons):
                if is_va:
                    yob = _RNG.randint(1940, 1975)
                    gender_cid = _RNG.choices([8507, 8532], weights=[0.92, 0.08])[0]
                elif is_childrens:
                    yob = _RNG.randint(2000, 2019)
                    gender_cid = wchoice(gender_pop)
                else:
                    yob = _RNG.randint(1940, 2004)
                    gender_cid = wchoice(gender_pop)

                county  = _RNG.choice(counties)
                zip5    = COUNTY_ZIP.get(county, "55401")
                tract   = COUNTY_TRACT.get(county, f"{county}000100")

                p = Person(
                    health_system=hs,
                    person_source_value=f"{code}-{i+1:04d}",
                    gender_concept_id=gender_cid,
                    year_of_birth=yob,
                    race_concept_id=wchoice(race_pop),
                    ethnicity_concept_id=wchoice(ethnicity_pop),
                    preferred_language=wchoice(lang_pop),
                    county_fips=county,
                    zip_code=zip5,
                    census_tract=tract,
                )
                site_persons.append(p)

            # Bulk-create persons and retrieve with PKs
            created_persons = Person.objects.bulk_create(site_persons)
            total_persons  += len(created_persons)

            for person in created_persons:
                # ── Visits (1–4 per person) ───────────────────────────────────
                n_visits = _RNG.randint(1, 4)
                for _ in range(n_visits):
                    vstart = _random_date(STUDY_START, STUDY_END)
                    vend   = vstart + datetime.timedelta(days=_RNG.randint(0, 3))
                    visit_bulk.append(VisitOccurrence(
                        person=person,
                        health_system=hs,
                        visit_concept_id=_RNG.choice([VISIT_CONCEPT_AMB, VISIT_CONCEPT_IP]),
                        visit_start_date=vstart,
                        visit_end_date=vend,
                        visit_type_concept_id=44818518,  # EHR encounter record
                    ))
                    total_visits += 1

                # ── Condition occurrences + linked drug/measurement records ───
                for slug, base_prev in BASE_PREVALENCE.items():
                    prev = base_prev * mults.get(slug, 1.0)
                    if _RNG.random() < prev and slug in cond_concept:
                        dx_date = _random_date(STUDY_START, STUDY_END)
                        co_bulk.append(ConditionOccurrence(
                            person=person,
                            health_system=hs,
                            condition_concept_id=cond_concept[slug],
                            condition_start_date=dx_date,
                            condition_end_date=dx_date + datetime.timedelta(days=_RNG.randint(0, 365)),
                            condition_type_concept_id=32817,  # EHR encounter diagnosis
                        ))
                        total_co += 1

                        # Drug exposures (75% of conditioned persons have a prescription)
                        if slug in COND_DRUG_CONCEPTS and _RNG.random() < 0.75:
                            for drug_cid in COND_DRUG_CONCEPTS[slug]:
                                supply = _RNG.choice([30, 60, 90])
                                rx_start = _random_date(STUDY_START, STUDY_END)
                                drug_bulk.append(DrugExposure(
                                    person=person,
                                    health_system=hs,
                                    drug_concept_id=drug_cid,
                                    drug_exposure_start_date=rx_start,
                                    drug_exposure_end_date=rx_start + datetime.timedelta(days=supply),
                                    drug_type_concept_id=_DRUG_TYPE_EHR,
                                    quantity=Decimal(_RNG.randint(1, 4) * 30),
                                    days_supply=supply,
                                ))
                                total_drugs += 1

                        # Measurements (85% of conditioned persons have a lab/vital)
                        if slug in COND_MEAS_CONCEPTS and _RNG.random() < 0.85:
                            for meas_cid, lo, hi in COND_MEAS_CONCEPTS[slug]:
                                value = Decimal(str(round(_RNG.uniform(lo, hi), 2)))
                                meas_bulk.append(Measurement(
                                    person=person,
                                    health_system=hs,
                                    measurement_concept_id=meas_cid,
                                    measurement_date=_random_date(STUDY_START, STUDY_END),
                                    measurement_type_concept_id=_MEAS_TYPE_LAB,
                                    value_as_number=value,
                                ))
                                total_meas += 1

            if verbosity >= 2:
                self.stdout.write(
                    f"  {code:<20} {len(created_persons):>3} persons"
                )

        # Bulk write all clinical records
        VisitOccurrence.objects.bulk_create(visit_bulk, batch_size=500)
        ConditionOccurrence.objects.bulk_create(co_bulk, batch_size=500)
        DrugExposure.objects.bulk_create(drug_bulk, batch_size=500)
        Measurement.objects.bulk_create(meas_bulk, batch_size=500)

        self.stdout.write(
            f"Persons: {total_persons}  "
            f"Visits: {total_visits}  "
            f"ConditionOccurrences: {total_co}  "
            f"DrugExposures: {total_drugs}  "
            f"Measurements: {total_meas}"
        )

    # ── Data-gap institutions ─────────────────────────────────────────────────

    def _seed_data_gap_institutions(self, verbosity):
        created_count = 0
        for name, code in TRIBAL_NATIONS + FQHC_INSTITUTIONS:
            _, created = HealthSystem.objects.get_or_create(
                short_code=code,
                defaults={"name": name, "is_active": False},
            )
            if created:
                created_count += 1
        total = len(TRIBAL_NATIONS) + len(FQHC_INSTITUTIONS)
        self.stdout.write(
            self.style.WARNING(
                f"Data-gap institutions registered (is_active=False): "
                f"{len(TRIBAL_NATIONS)} Tribal Nations + {len(FQHC_INSTITUTIONS)} FQHCs "
                f"({created_count} new).  No patient data generated for these sites."
            )
        )

    # ── HashTokens + PPRL deduplication ──────────────────────────────────────

    def _seed_tokens(self, sites, force, verbosity):
        """
        Generate synthetic HashToken records for all seeded persons.

        PII is derived from the person's stored attributes (race, sex,
        year_of_birth, zip_code) using a per-person seeded RNG so the
        result is deterministic across runs.  The generated names, DOBs,
        and phone numbers are obviously fictitious — they are never stored;
        only the SHA-256 digest (token) is persisted.

        Cross-site linkages are created for a realistic fraction of each
        site's population, mirroring known MN care-transition patterns.
        """
        if force:
            deleted, _ = HashToken.objects.filter(
                health_system__in=sites.values()
            ).delete()
            DeduplicatedRoster.objects.filter(
                canonical_site__in=sites.values()
            ).delete()
            if verbosity >= 1:
                self.stdout.write(f"Cleared {deleted} existing HashToken rows.")

        existing = HashToken.objects.filter(
            health_system__in=sites.values()
        ).count()
        if existing and not force:
            self.stdout.write(
                self.style.WARNING(
                    f"Found {existing} existing HashToken rows — skipping token seed. "
                    "Use --force to regenerate."
                )
            )
            return

        # ── Step 1: generate PII + tokens for all primary persons ────────────
        all_persons = list(
            Person.objects.filter(health_system__in=sites.values())
            .select_related("health_system")
            .order_by("id")
        )

        pii_by_pid: dict[int, dict] = {}   # person.pk → {first, last, dob, sex, phone, zip}
        token_bulk: list[HashToken] = []

        for person in all_persons:
            pii = _make_pii(person)
            pii_by_pid[person.pk] = pii
            tok = compute_token(**pii)
            token_bulk.append(HashToken(
                person=person,
                health_system=person.health_system,
                token=tok,
            ))

        HashToken.objects.bulk_create(token_bulk, ignore_conflicts=True, batch_size=500)
        primary_count = len(token_bulk)

        if verbosity >= 2:
            self.stdout.write(f"  Primary tokens generated: {primary_count}")

        # ── Step 2: cross-site linkages ───────────────────────────────────────
        persons_by_site: dict[str, list[Person]] = {}
        for p in all_persons:
            persons_by_site.setdefault(p.health_system.short_code, []).append(p)

        cross_persons_bulk: list[Person] = []
        cross_token_data: list[tuple[dict, HealthSystem]] = []  # (pii, target_site)

        for src_code, dst_code, fraction in CROSS_SITE_PAIRS:
            src_persons = persons_by_site.get(src_code, [])
            dst_site = sites.get(dst_code)
            if not src_persons or not dst_site:
                continue

            n_link = max(1, round(len(src_persons) * fraction))
            # Deterministic selection via seeded sample
            pair_rng = random.Random(hash((src_code, dst_code)) & 0xFFFFFFFF)
            selected = pair_rng.sample(src_persons, min(n_link, len(src_persons)))

            for src_person in selected:
                pii = pii_by_pid[src_person.pk]
                # Mirror person record at destination site (same demographics,
                # site-appropriate geography)
                dst_counties = SITE_COUNTIES.get(dst_code, ["27053"])
                dst_county = pair_rng.choice(dst_counties)
                dst_zip = COUNTY_ZIP.get(dst_county, "55401")
                dst_tract = COUNTY_TRACT.get(dst_county, f"{dst_county}000100")

                mirror = Person(
                    health_system=dst_site,
                    person_source_value=f"{dst_code}-LINK-{src_person.person_source_value}",
                    gender_concept_id=src_person.gender_concept_id,
                    year_of_birth=src_person.year_of_birth,
                    race_concept_id=src_person.race_concept_id,
                    ethnicity_concept_id=src_person.ethnicity_concept_id,
                    preferred_language=src_person.preferred_language,
                    county_fips=dst_county,
                    zip_code=dst_zip,
                    census_tract=dst_tract,
                )
                cross_persons_bulk.append(mirror)
                cross_token_data.append((pii, dst_site))

        # Bulk-create cross-site persons to get PKs
        created_mirrors = Person.objects.bulk_create(
            cross_persons_bulk, batch_size=500
        )

        # Add a single visit per cross-site person so canonical-site selection works
        mirror_visits = []
        visit_rng = random.Random(99)
        for mirror in created_mirrors:
            vdate = _random_date(datetime.date(2021, 1, 1), datetime.date(2022, 12, 31))
            mirror_visits.append(VisitOccurrence(
                person=mirror,
                health_system=mirror.health_system,
                visit_concept_id=9202,
                visit_start_date=vdate,
                visit_end_date=vdate,
                visit_type_concept_id=44818518,
            ))
        VisitOccurrence.objects.bulk_create(mirror_visits, batch_size=500)

        cross_tokens = []
        for mirror, (pii, dst_site) in zip(created_mirrors, cross_token_data):
            tok = compute_token(**pii)
            cross_tokens.append(HashToken(
                person=mirror,
                health_system=dst_site,
                token=tok,
            ))
        HashToken.objects.bulk_create(cross_tokens, ignore_conflicts=True, batch_size=500)

        if verbosity >= 1:
            self.stdout.write(
                f"Cross-site persons: {len(created_mirrors)}  "
                f"(tokens linking {len(CROSS_SITE_PAIRS)} site pairs)"
            )

        # ── Step 3: PPRL deduplication ────────────────────────────────────────
        self.stdout.write("Running PPRL deduplication…")
        roster_count = deduplicate_tokens(HashToken.objects.filter(
            health_system__in=sites.values()
        ))
        multi_site = DeduplicatedRoster.objects.filter(site_count__gt=1).count()
        self.stdout.write(
            f"DeduplicatedRoster rows: {roster_count}  "
            f"({multi_site} with site_count > 1)"
        )

        # ── Step 4: data-gap reminder ─────────────────────────────────────────
        self.stdout.write(
            self.style.WARNING(
                "\n  DATA GAP: Tokens generated for MNEHRC sites only.\n"
                f"  {len(TRIBAL_NATIONS)} MN Tribal Nation health programs and "
                f"{len(FQHC_INSTITUTIONS)} FQHCs are NOT represented.\n"
                "  These populations — disproportionately affected by chronic conditions —\n"
                "  are systematically undercounted in current prevalence estimates.\n"
                "  Tribal data sovereignty agreements and FQHC data-sharing MOUs\n"
                "  are prerequisites before these sites can be onboarded.\n"
            )
        )

    # ── Default StudyRun ──────────────────────────────────────────────────────

    def _seed_study_run(self, conditions, verbosity):
        run, created = StudyRun.objects.get_or_create(
            name="HTAC 2022 Baseline",
            defaults={
                "description":    "Baseline prevalence study covering the 2022 calendar year.",
                "run_date":       datetime.date(2023, 3, 1),
                "roster_version": datetime.date(2023, 1, 15),
                "status":         "pending",
            },
        )
        if created:
            run.conditions.set(conditions.values())
            run.save()
        tag = "created" if created else "exists"
        self.stdout.write(f"StudyRun 'HTAC 2022 Baseline': {tag}")


# ── Utilities ─────────────────────────────────────────────────────────────────

def _random_date(start: datetime.date, end: datetime.date) -> datetime.date:
    delta = (end - start).days
    return start + datetime.timedelta(days=_RNG.randint(0, delta))


def _name_key(person) -> str:
    """Return the name-pool key for a person based on race + ethnicity."""
    if person.ethnicity_concept_id == 38003563:   # Hispanic or Latino
        return "hispanic"
    return person.race_concept_id if person.race_concept_id in _FIRST_M else "default"


def _make_pii(person) -> dict:
    """
    Return a dict of synthetic PII fields for *person*.

    Uses a per-person seeded RNG (keyed to person.pk) so the result is
    deterministic regardless of iteration order.  The returned values are
    obviously fictitious and are NEVER persisted — only the SHA-256 token
    derived from them is stored.

    Returns keys: first_name, last_name, dob, sex, phone, zip_code
    """
    rng = random.Random(person.pk * 6271 + 1337)   # 6271 is prime

    key = _name_key(person)
    sex_char = "M" if person.gender_concept_id == 8507 else "F"

    first_pool = _FIRST_M.get(key, _FIRST_M["default"]) if sex_char == "M" \
        else _FIRST_F.get(key, _FIRST_F["default"])
    last_pool  = _LAST.get(key, _LAST["default"])

    first_name = rng.choice(first_pool)
    last_name  = rng.choice(last_pool)

    # DOB: year_of_birth + synthetic month/day
    month = rng.randint(1, 12)
    max_day = [0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month]
    day = rng.randint(1, max_day)
    dob = datetime.date(person.year_of_birth, month, day)

    # Phone: site area code + 7 random digits
    site_code = person.health_system.short_code
    area_codes = _SITE_AREA_CODES.get(site_code, ["612"])
    area = rng.choice(area_codes)
    number = f"{rng.randint(100, 999)}{rng.randint(1000, 9999)}"
    phone = f"{area}{number}"

    return {
        "first_name": first_name,
        "last_name":  last_name,
        "dob":        dob,
        "sex":        sex_char,
        "phone":      phone,
        "zip_code":   person.zip_code or "55401",
    }
