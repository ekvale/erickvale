"""AAPI metadata constellation seed data (steward example).

Asian or Asian American and Native Hawaiian or Pacific Islander stay separate
CHS-aligned tags. Shared AAPI materials are linked to *both* tags; community-
specific items attach to one. Language landing pages are constellation links
and cataloged publications (language metadata + Language Access tag), not
race/ethnicity tags by themselves.
"""

from datetime import date

# (title, url) — MDH spaces / products
MDH_SPACES = [
    ("HESI Division webpage", "https://www.health.state.mn.us/communities/equity/"),
    ("Office of DEIB webpage", "https://www.health.state.mn.us/about/equalopp/"),
    (
        "MDH Center for Health Statistics",
        "https://www.health.state.mn.us/data/mchs/",
    ),
    (
        "Demographic data webpage",
        "https://www.health.state.mn.us/data/mchs/demodatastandards.html",
    ),
    (
        "Minnesota Public Health Data Access Health Equity Landing Page",
        "https://data.web.health.state.mn.us/health_equity",
    ),
]

# (title, note, url)
STATUTES_POLICY = [
    (
        "Minnesota Statutes Section 4A.02",
        "Establishes Minnesota demographic data and the role of the State Demographer.",
        "https://www.revisor.mn.gov/statutes/cite/4A.02",
    ),
    (
        "Minnesota Statutes Chapter 13 — Minnesota Government Data Practices Act",
        "Governs government data practices.",
        "https://www.revisor.mn.gov/statutes/cite/13",
    ),
    (
        "Minn. Stat. § 15.0145 — Ethnic councils",
        "Structure and duties of the state's ethnic councils.",
        "https://www.revisor.mn.gov/statutes/cite/15.0145",
    ),
    (
        "Council on Asian Pacific Minnesotans (CAPM) 2025-26 Legislative Agenda",
        "CAPM legislative priorities.",
        "https://mn.gov/capm/",
    ),
    (
        "Minnesota Statutes § 145.987 — HEAL Council",
        "HEAL Council statute.",
        "https://www.revisor.mn.gov/statutes/cite/145.987",
    ),
    (
        "Minnesota Statutes § 145.928 — Health disparities and ethnic councils",
        "Coordinated plans to reduce health disparities in collaboration with ethnic councils including CAPM.",
        "https://www.revisor.mn.gov/statutes/cite/145.928",
    ),
    (
        "Minnesota Statutes Section 299A.2994 — Asian-American Juvenile Crime Prevention Grants (2025)",
        "Asian-American juvenile crime prevention grants.",
        "https://www.revisor.mn.gov/statutes/cite/299A.2994",
    ),
    (
        "2026 Minn. Laws Chapter 115 §§ 148.636–148.6373 — Massage Therapy and Asian Bodywork Therapy Act",
        "Minnesota Massage Therapy and Asian Bodywork Therapy Act.",
        "https://www.revisor.mn.gov/laws/",
    ),
    (
        "Federal OMB Statistical Policy Directive No. 15 (SPD 15)",
        "Federal race and ethnicity data standards, including Asian and Native Hawaiian or Other Pacific Islander categories.",
        "https://spd15revision.gov/",
    ),
]

# (title, url, apply_to) where apply_to is "both", "asian", or "nhpi"
RESOURCE_GROUPS = [
    ("Council on Asian Pacific Minnesotans (CAPM)", "https://mn.gov/capm/", "both"),
    (
        "CAPI (formerly Center for Asian and Pacific Islanders)",
        "https://www.capiusa.org/",
        "both",
    ),
    ("Wilder Center for Social Healing", "https://www.wilder.org/", "both"),
    (
        "Coalition of Asian-American Leaders (CAAL)",
        "https://caalmn.org/",
        "asian",
    ),
    ("Hmong American Partnership", "https://www.hmong.org/", "asian"),
    ("Hmong Medical Association", "", "asian"),
    ("Advocates for Human Rights", "https://www.theadvocatesforhumanrights.org/", "both"),
    (
        "International Institute of Minnesota",
        "https://iimn.org/",
        "both",
    ),
    ("Vietnamese Social Services", "", "asian"),
    ("Sewa-Aifw (Asian Indian Family Wellness)", "https://www.sewa-aifw.org/", "asian"),
    ("Afghan Cultural Society of Minnesota", "", "asian"),
    (
        "U of M Asian Pacific American Research Center (APARC)",
        "https://cla.umn.edu/",
        "both",
    ),
    (
        "Asian and Pacific Islander Health Forum (National)",
        "https://www.apiahf.org/",
        "both",
    ),
    (
        "Association of Asian Pacific Community Health Organizations (National)",
        "https://www.aapcho.org/",
        "both",
    ),
    (
        "Asian Americans/Pacific Islanders in Philanthropy (National)",
        "https://aapip.org/",
        "both",
    ),
]

# Language landing pages: (language_code, title, url)
LANGUAGE_LANDING_PAGES = [
    ("zh", "Chinese (简体中文) translated materials", "https://www.health.state.mn.us/"),
    ("prs", "Dari (دری) translated materials", "https://www.health.state.mn.us/"),
    ("gu", "Gujarati (ગુજરાતી) translated materials", "https://www.health.state.mn.us/"),
    ("hi", "Hindi (हिन्दी) translated materials", "https://www.health.state.mn.us/"),
    ("hmn", "Hmong (Lus Hmoob) translated materials", "https://www.health.state.mn.us/"),
    ("ksw", "Karen (S’gaw Karen) translated materials", "https://www.health.state.mn.us/"),
    ("km", "Khmer (ភាសាខ្មែរ) translated materials", "https://www.health.state.mn.us/"),
    ("ko", "Korean (한국어) translated materials", "https://www.health.state.mn.us/"),
    ("lo", "Lao (ພາສາລາວ) translated materials", "https://www.health.state.mn.us/"),
    ("ne", "Nepali (नेपाली) translated materials", "https://www.health.state.mn.us/"),
    ("vi", "Vietnamese (Tiếng Việt) translated materials", "https://www.health.state.mn.us/"),
    ("ur", "Urdu (اردو) translated materials", "https://www.health.state.mn.us/"),
]

# Publications: (title, year_or_None, url, apply_to, doc_type_name, extra_tag_slugs)
# apply_to: both | asian | nhpi
# Descriptions are generated in the seeder to meet the 150-character minimum.
PUBLICATIONS = [
    (
        "A Report on Violence Against Asian Women and Children in Minnesota",
        2016,
        "https://www.health.state.mn.us/",
        "asian",
        "Report",
        ["domestic-violence", "children"],
    ),
    (
        "Health Status Among Minnesota Adults, 2023",
        2023,
        "https://www.health.state.mn.us/",
        "both",
        "Report",
        ["adults", "health-outcomes", "survey-data"],
    ),
    (
        "Asthma by Race and Ethnicity (2022 MSS)",
        2022,
        "https://www.health.state.mn.us/",
        "both",
        "Data Brief",
        ["asthma", "adolescents", "survey-data"],
    ),
    (
        "Asthma among Middle and High School Students (2022 MSS)",
        2022,
        "https://www.health.state.mn.us/",
        "both",
        "Data Brief",
        ["asthma", "adolescents", "survey-data"],
    ),
    (
        "2025 MSS — Asian or Asian-American only",
        2025,
        "https://www.health.state.mn.us/data/mchs/surveys/mss/datatables.html",
        "asian",
        "Data Brief",
        ["survey-data", "adolescents"],
    ),
    (
        "2025 MSS — Asian or Asian-American alone or in combination with other groups",
        2025,
        "https://www.health.state.mn.us/data/mchs/surveys/mss/datatables.html",
        "asian",
        "Data Brief",
        ["survey-data", "adolescents", "multiracial"],
    ),
    (
        "2025 MSS — Native Hawaiian or Other Pacific Islander only",
        2025,
        "https://www.health.state.mn.us/data/mchs/surveys/mss/datatables.html",
        "nhpi",
        "Data Brief",
        ["survey-data", "adolescents"],
    ),
    (
        "2025 MSS — Native Hawaiian or Other Pacific Islander alone or in combination with other groups",
        2025,
        "https://www.health.state.mn.us/data/mchs/surveys/mss/datatables.html",
        "nhpi",
        "Data Brief",
        ["survey-data", "adolescents", "multiracial"],
    ),
    (
        "Suicides among Korean Adoptees in Minnesota",
        2017,
        "https://www.health.state.mn.us/",
        "asian",
        "Report",
        ["suicide-prevention", "mental-health"],
    ),
    (
        "Advancing Health Equity at the Minnesota Department of Health 2014-2024",
        2024,
        "https://www.health.state.mn.us/",
        "both",
        "Report",
        ["health-disparities", "structural-racism"],
    ),
    (
        "Eliminating Health Disparities Initiative - Infant Mortality Report 2023",
        2023,
        "https://www.health.state.mn.us/",
        "both",
        "Report",
        ["infant-mortality", "health-disparities"],
    ),
    (
        "Eliminating Health Disparities Initiative - Infant Mortality Report 2022",
        2022,
        "https://www.health.state.mn.us/",
        "both",
        "Report",
        ["infant-mortality", "health-disparities"],
    ),
    (
        "Eliminating Health Disparities Initiative - Report to the Legislature 2021",
        2021,
        "https://www.health.state.mn.us/",
        "both",
        "Legislation or Policy",
        ["health-disparities", "legislative-reporting"],
    ),
    (
        "Eliminating Health Disparities Initiative - Infant Mortality Report 2021",
        2021,
        "https://www.health.state.mn.us/",
        "both",
        "Report",
        ["infant-mortality", "health-disparities"],
    ),
    (
        "Eliminating Health Disparities Initiative - Report to the Legislature 2020",
        2020,
        "https://www.health.state.mn.us/",
        "both",
        "Legislation or Policy",
        ["health-disparities", "legislative-reporting"],
    ),
    (
        "Eliminating Health Disparities Initiative - Infant Mortality Report 2020",
        2020,
        "https://www.health.state.mn.us/",
        "both",
        "Report",
        ["infant-mortality", "health-disparities"],
    ),
    (
        "Eliminating Health Disparities Initiative - Report to the Legislature 2019",
        2019,
        "https://www.health.state.mn.us/",
        "both",
        "Legislation or Policy",
        ["health-disparities", "legislative-reporting"],
    ),
    (
        "Eliminating Health Disparities Initiative - Infant Mortality Report 2019",
        2019,
        "https://www.health.state.mn.us/",
        "both",
        "Report",
        ["infant-mortality", "health-disparities"],
    ),
    (
        "Eliminating Health Disparities Initiative - Infant Mortality Report 2018",
        2018,
        "https://www.health.state.mn.us/",
        "both",
        "Report",
        ["infant-mortality", "health-disparities"],
    ),
    (
        "Eliminating Health Disparities Initiative - Report to the Legislature 2016",
        2016,
        "https://www.health.state.mn.us/",
        "both",
        "Legislation or Policy",
        ["health-disparities", "legislative-reporting"],
    ),
    (
        "Prostate Cancer Disparities in Minnesota",
        2024,
        "https://www.health.state.mn.us/",
        "both",
        "Report",
        ["cancer", "health-disparities"],
    ),
    (
        "Statewide Multi Year Anemia in Minnesota WIC Infants and Children by Race/Ethnicity 2019",
        2019,
        "https://www.health.state.mn.us/",
        "both",
        "Data Brief",
        ["children", "infants", "food-security"],
    ),
    (
        "Multi Year Overweight and Obesity Status in Minnesota WIC Children Ages 2 to 5 by Race/Ethnicity AOIC (2023)",
        2023,
        "https://www.health.state.mn.us/",
        "both",
        "Data Brief",
        ["obesity", "children"],
    ),
    (
        "Multi Year Pre Pregnancy Weight Status in Minnesota WIC by Race/Ethnicity (2022)",
        2022,
        "https://www.health.state.mn.us/",
        "both",
        "Data Brief",
        ["obesity", "pregnant-people"],
    ),
    (
        "Multi Year Anemia in Minnesota WIC Infants and Children by Race/Ethnicity AOIC 2022",
        2022,
        "https://www.health.state.mn.us/",
        "both",
        "Data Brief",
        ["children", "infants"],
    ),
    (
        "Anemia in Pregnant and Postpartum Women MN WIC Fact Sheet 2019",
        2019,
        "https://www.health.state.mn.us/",
        "both",
        "Fact Sheet",
        ["pregnant-people"],
    ),
    (
        "Anemia in pregnant and postpartum women Minnesota WIC fact sheet, 2025",
        2025,
        "https://www.health.state.mn.us/",
        "both",
        "Fact Sheet",
        ["pregnant-people"],
    ),
    (
        "WIC PROGRAM 2025 Methodology and Interpretation: Location and Race and Ethnicity",
        2025,
        "https://www.health.state.mn.us/",
        "both",
        "Guidance Document",
        ["data-quality"],
    ),
    (
        "Child Anemia in the Minnesota WIC Program, 2025",
        2025,
        "https://www.health.state.mn.us/",
        "both",
        "Data Brief",
        ["children"],
    ),
    (
        "Minnesota WIC Facts 2026",
        2026,
        "https://www.health.state.mn.us/",
        "both",
        "Fact Sheet",
        ["food-security", "children"],
    ),
    (
        "2025 Anemia in Minnesota WIC Children Talking Points",
        2025,
        "https://www.health.state.mn.us/",
        "both",
        "Fact Sheet",
        ["children"],
    ),
    (
        "WIC High Birth Weight data by Race and Ethnicity",
        None,
        "https://www.health.state.mn.us/",
        "both",
        "Data Brief",
        ["birth-outcomes"],
    ),
    (
        "MN FEET Community Report (English)",
        None,
        "https://www.health.state.mn.us/",
        "both",
        "Report",
        ["community-partnerships"],
    ),
    (
        "MN FEET Community Report (Hmong)",
        None,
        "https://www.health.state.mn.us/",
        "asian",
        "Report",
        ["community-partnerships", "language-access"],
    ),
    (
        "Cervical Cancer in Minnesota (2025)",
        2025,
        "https://www.health.state.mn.us/",
        "both",
        "Fact Sheet",
        ["cancer"],
    ),
    (
        "Ovarian Cancer in Minnesota (2024)",
        2024,
        "https://www.health.state.mn.us/",
        "both",
        "Fact Sheet",
        ["cancer"],
    ),
    (
        "Uterine Cancer in Minnesota (2024)",
        2024,
        "https://www.health.state.mn.us/",
        "both",
        "Fact Sheet",
        ["cancer"],
    ),
    (
        "Multiple Myeloma Fact Sheet - Minnesota Department of Health (2024)",
        2024,
        "https://www.health.state.mn.us/",
        "both",
        "Fact Sheet",
        ["cancer"],
    ),
    (
        "Breastfeeding Initiation for all Infants born in Minnesota by Race/Ethnicity and Cultural Identity and Region, CY 2017 to 2021",
        2021,
        "https://www.health.state.mn.us/",
        "both",
        "Data Brief",
        ["breastfeeding", "infants"],
    ),
    (
        "BIG BROTHERS BIG SISTERS TWIN CITIES profile",
        None,
        "https://www.health.state.mn.us/",
        "both",
        "Fact Sheet",
        ["community-partnerships", "children"],
    ),
    (
        "Hmong American Partnership profile",
        None,
        "https://www.health.state.mn.us/",
        "asian",
        "Fact Sheet",
        ["community-partnerships", "immigrants-refugees"],
    ),
    (
        "Lung Cancer Survival in Minnesota, 2021",
        2021,
        "https://www.health.state.mn.us/",
        "both",
        "Data Brief",
        ["cancer"],
    ),
    (
        "Vaccinations, by Race and Ethnicity (CSV)",
        None,
        "https://www.health.state.mn.us/",
        "both",
        "Data Brief",
        ["immunization-programs"],
    ),
    (
        "STD, HIV and Hepatitis C 2017 Data Release",
        2017,
        "https://www.health.state.mn.us/",
        "both",
        "Report",
        ["sexually-transmitted-infections", "hiv-aids"],
    ),
    (
        "Suicides in the Laotian Community of Minnesota 2016",
        2016,
        "https://www.health.state.mn.us/",
        "asian",
        "Report",
        ["suicide-prevention", "mental-health"],
    ),
    (
        "Sexually Transmitted Disease (STD) Surveillance Report, 2016",
        2016,
        "https://www.health.state.mn.us/",
        "both",
        "Report",
        ["sexually-transmitted-infections", "disease-surveillance"],
    ),
    (
        "Hmong Culture & Foods (WIC 2025)",
        2025,
        "https://www.health.state.mn.us/",
        "asian",
        "Fact Sheet",
        ["food-security", "cultural-responsiveness"],
    ),
    (
        "Excessive Alcohol Use Data Brief 2017",
        2017,
        "https://www.health.state.mn.us/",
        "both",
        "Data Brief",
        ["alcohol"],
    ),
    (
        "Birth Outcomes and Breastfeeding in Minnesota Hmong Women",
        None,
        "https://www.health.state.mn.us/",
        "asian",
        "Report",
        ["birth-outcomes", "breastfeeding", "pregnant-people"],
    ),
    (
        "Only 4 in 10 Minnesota Adults have Ideal Cardiovascular Health",
        None,
        "https://www.health.state.mn.us/",
        "both",
        "Fact Sheet",
        ["cardiovascular-disease", "adults"],
    ),
    (
        "2023 Minnesota Adult Commercial Tobacco Data",
        2023,
        "https://www.health.state.mn.us/",
        "both",
        "Data Brief",
        ["tobacco", "adults"],
    ),
    (
        "Minnesota 2017 Statewide Health Assessment",
        2017,
        "https://www.health.state.mn.us/",
        "both",
        "Report",
        ["health-outcomes", "statewide"],
    ),
    (
        "Cannabis Use Among Youth in Minnesota",
        None,
        "https://www.health.state.mn.us/",
        "both",
        "Data Brief",
        ["substance-use", "adolescents"],
    ),
    (
        "Hospitalization Rate by Race and Ethnicity (CSV)",
        None,
        "https://www.health.state.mn.us/",
        "both",
        "Data Brief",
        ["hospitals", "health-disparities"],
    ),
    (
        "Minnesota Department of Health, PREP Infographic",
        None,
        "https://www.health.state.mn.us/",
        "both",
        "Infographic",
        ["adolescents"],
    ),
    (
        "HIV/AIDS Prevalence and Mortality Report, 2017",
        2017,
        "https://www.health.state.mn.us/",
        "both",
        "Report",
        ["hiv-aids"],
    ),
    (
        "Wabasha County Community Testing Demographics",
        None,
        "https://www.health.state.mn.us/",
        "both",
        "Data Brief",
        ["county-level", "disease-surveillance"],
    ),
    (
        "Mental Health in Minnesota data brief 2017",
        2017,
        "https://www.health.state.mn.us/",
        "both",
        "Data Brief",
        ["mental-health"],
    ),
    (
        "Tuberculosis Semi-Annual Surveillance Report",
        None,
        "https://www.health.state.mn.us/",
        "both",
        "Report",
        ["tuberculosis", "disease-surveillance"],
    ),
    (
        "Family Planning Special Projects Statistical Report for FY2024",
        2024,
        "https://www.health.state.mn.us/",
        "both",
        "Report",
        ["prenatal-care"],
    ),
]


def publication_date(year):
    if year is None:
        return None
    return date(year, 1, 1)


def describe(title, year):
    year_bit = f" ({year})" if year else ""
    body = (
        f"{title}{year_bit}. Cataloged from the MDH AAPI metadata constellation example "
        "for Asian or Asian American and/or Native Hawaiian or Pacific Islander "
        "populations. Replace this description and confirm the canonical health.mn.gov "
        "URL when stewards verify the live source."
    )
    if len(body) < 150:
        body += " Additional context will be added during steward review."
    return body
