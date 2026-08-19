"""Single source of truth for the starter publications taxonomy.

Run this to regenerate the four CSVs in this directory, which
``manage.py seed_mdh_publications_taxonomy`` reads:

    python mdh_publications/data/build_taxonomy.py

NOTE ON PROVENANCE: vocabulary is aligned to MDH / CHS wording where we have
it, NIH/NLM publication types for document format, and Nan's steward list.
Tag slugs must be unique across the whole taxonomy: Tag.slug is unique.

Structure: facet code -> (facet name, facet description, topic groups),
where each topic group maps to a list of (slug, name, description).
"""

import csv
from pathlib import Path

# Old starter slugs -> current slugs. Applied before import so existing
# publication tag links survive a re-seed.
TAG_SLUG_RENAMES = {
    "income-poverty": "low-income",
    "transportation-barriers": "barriers-to-care",
    "child-maltreatment": "child-abuse-and-neglect",
}

# Obsolete slug -> tag to receive those publications, then delete the old tag.
OBSOLETE_TAG_REASSIGN = {
    "readmissions": "care-quality",
}

# Retired document types -> Nan/NLM-aligned type that should remain active.
DOCUMENT_TYPE_REMAP = {
    "Surveillance Summary": "Data Brief",
    "Dashboard": "Data Brief",
    "Statistical Table": "Data Brief",
    "Legislative Report": "Legislation or Policy",
    "Toolkit": "Guidance Document",
    "Annual Report": "Report",
    "White Paper": "Report",
    "Presentation": "Report",
    "Newsletter": "Fact Sheet",
    "Chartbook": "Data Brief",
}


def _humanize(slug):
    return slug.replace("-", " ").replace("_", " ").title()


_ACRONYM_NAMES = {
    "covid-19": "COVID-19",
    "hiv-aids": "HIV/AIDS",
    "lgbtq-populations": "LGBTQ+ Populations",
}


def T(slug, description, name=None):
    """(slug, display name, description) for a tag row."""
    return (slug, name or _ACRONYM_NAMES.get(slug) or _humanize(slug), description)


TAXONOMY = {
    "A": (
        "Demographics & Populations",
        "Who a publication is about: age, race and ethnicity, geography, and "
        "populations that experience distinct health needs or barriers.",
        {
            "Age Groups": [
                T("infants", "Children under one year of age."),
                T("children", "Pediatric populations, roughly ages 1 to 12."),
                T("adolescents", "Youth and teenagers, roughly ages 13 to 19."),
                T("young-adults", "Adults roughly ages 20 to 34."),
                T("adults", "Working-age adults, roughly ages 35 to 64."),
                T("older-adults", "Adults age 65 and older."),
            ],
            "Race & Ethnicity": [
                T(
                    "american-indian",
                    "People with origins in the original peoples of North, Central, "
                    "and South America who maintain tribal affiliation or community "
                    "attachment, including Alaska Native peoples. Aligns with CHS "
                    "and OMB American Indian or Alaska Native reporting.",
                    "American Indian and Alaska Native",
                ),
                T(
                    "asian-populations",
                    "People with origins in East Asia, Southeast Asia, or South Asia, "
                    "including Asian American communities. Aligns with CHS Asian reporting.",
                    "Asian",
                ),
                T(
                    "black-populations",
                    "Black and African populations, including African American people "
                    "and people with origins in any of the Black racial groups of Africa. "
                    "Use when a publication is about these communities, not merely "
                    "translated into a language they speak.",
                    "Black and African Populations",
                ),
                T(
                    "hispanic-latino",
                    "Hispanic, Latino/Latina/Latinx, and Spanish-speaking populations, "
                    "including people of Cuban, Mexican, Puerto Rican, South or Central "
                    "American, or other Spanish culture or origin, regardless of race. "
                    "If a document is only translated into Spanish and is not about "
                    "these communities, set Publication Language to Spanish instead of "
                    "this tag.",
                    "Hispanic, Latino, and Spanish-speaking Populations",
                ),
                T(
                    "mena",
                    "People with origins in the Middle East or North Africa. Distinct "
                    "from White in CHS and 2024 OMB (SPD 15) standards.",
                    "Middle Eastern and North African (MENA)",
                ),
                T(
                    "pacific-islander",
                    "People with origins in Hawaii, Guam, Samoa, or other Pacific Islands. "
                    "Aligns with CHS Native Hawaiian or Other Pacific Islander reporting.",
                    "Native Hawaiian and Pacific Islander",
                ),
                T(
                    "white-populations",
                    "White populations, including people with origins in Europe. "
                    "Does not include Middle Eastern or North African communities, "
                    "which have their own tag.",
                    "White",
                ),
                T(
                    "multiracial",
                    "People identifying with two or more races, matching CHS "
                    "more-than-one-race reporting.",
                    "Two or More Races",
                ),
            ],
            "Geography": [
                T("statewide", "Statewide figures covering all of Minnesota."),
                T("twin-cities-metro", "The seven-county Twin Cities metropolitan area."),
                T("greater-minnesota", "Minnesota outside the Twin Cities metro."),
                T("rural-communities", "Rural and small-town communities."),
                T("tribal-nations", "Tribal nations and reservation communities."),
                T("county-level", "Data reported at the county level."),
            ],
            "Priority Populations": [
                T(
                    "immigrants-refugees",
                    "Immigrant, refugee, and newcomer communities.",
                ),
                T("veterans", "Military veterans and their families."),
                T(
                    "lgbtq-populations",
                    "Lesbian, gay, bisexual, transgender, and queer people.",
                ),
                T(
                    "people-with-disabilities",
                    "People living with physical or cognitive disabilities.",
                ),
                T("pregnant-people", "People who are pregnant or postpartum."),
                T(
                    "uninsured-populations",
                    "People without health insurance coverage.",
                ),
                T(
                    "people-experiencing-homelessness",
                    "People experiencing housing instability or homelessness.",
                ),
            ],
            "Audience": [
                T(
                    "healthcare-provider",
                    "Materials written for clinicians, nurses, and other health care "
                    "providers rather than the general public.",
                    "Healthcare Provider",
                ),
            ],
        },
    ),
    "B": (
        "Health Conditions & Topics",
        "The health condition, disease, or clinical subject a publication "
        "addresses.",
        {
            "Chronic Disease": [
                T("cancer", "Cancer incidence, screening, treatment, and survivorship."),
                T("cardiovascular-disease", "Heart disease, stroke, and hypertension."),
                T("diabetes", "Type 1 and type 2 diabetes and prediabetes."),
                T("asthma", "Asthma and chronic respiratory conditions."),
                T("obesity", "Obesity, nutrition, and physical activity."),
                T("kidney-disease", "Chronic kidney disease and dialysis care."),
            ],
            "Infectious Disease": [
                T(
                    "covid-19",
                    "COVID-19 surveillance, response, and long-term effects.",
                ),
                T("influenza", "Seasonal and pandemic influenza."),
                T("hiv-aids", "HIV and AIDS prevention, testing, and care."),
                T(
                    "sexually-transmitted-infections",
                    "Sexually transmitted infections and reporting.",
                ),
                T(
                    "tuberculosis",
                    "Tuberculosis screening, treatment, and contact tracing.",
                ),
                T(
                    "vaccine-preventable-disease",
                    "Measles, pertussis, and other vaccine-preventable illness.",
                ),
                T(
                    "antimicrobial-resistance",
                    "Antibiotic resistance and stewardship.",
                ),
            ],
            "Behavioral Health": [
                T("mental-health", "Mental health conditions, treatment, and access."),
                T("substance-use", "Substance use disorders and treatment services."),
                T("opioids", "Opioid use, overdose, and harm reduction."),
                T("tobacco", "Tobacco, vaping, and cessation programs."),
                T("alcohol", "Alcohol use and related harms."),
                T("suicide-prevention", "Suicide surveillance and prevention efforts."),
            ],
            "Maternal & Child Health": [
                T("prenatal-care", "Access to and quality of prenatal care."),
                T(
                    "birth-outcomes",
                    "Preterm birth, low birth weight, and delivery outcomes.",
                ),
                T("infant-mortality", "Infant and perinatal mortality."),
                T("maternal-mortality", "Maternal deaths and severe maternal morbidity."),
                T("breastfeeding", "Breastfeeding initiation, duration, and support."),
                T("child-development", "Early childhood development and screening."),
            ],
            "Injury & Violence": [
                T(
                    "unintentional-injury",
                    "Falls, poisonings, and other unintentional injuries.",
                ),
                T("motor-vehicle-crashes", "Traffic-related injuries and deaths."),
                T("firearm-injury", "Firearm-related injuries and deaths."),
                T("domestic-violence", "Intimate partner and family violence."),
                T(
                    "child-abuse-and-neglect",
                    "Child abuse and neglect, including physical, sexual, and "
                    "emotional abuse and neglect.",
                    "Child Abuse and Neglect",
                ),
                T("occupational-injury", "Workplace injuries and illnesses."),
            ],
            "Environmental Health": [
                T("air-quality", "Outdoor and indoor air quality."),
                T("water-quality", "Drinking water, wells, and recreational water."),
                T("lead-exposure", "Childhood and occupational lead exposure."),
                T(
                    "climate-health",
                    "Health effects of extreme heat, flooding, and climate change.",
                ),
                T("foodborne-illness", "Food safety and foodborne outbreaks."),
                T(
                    "environmental-contaminants",
                    "Chemical contaminants and hazardous exposures.",
                ),
            ],
        },
    ),
    "C": (
        "Health System & Access",
        "How care is organized, staffed, financed, and reached, including "
        "coverage, cost, workforce, and facilities.",
        {
            "Access to Care": [
                T("insurance-coverage", "Health insurance coverage and enrollment."),
                T("uninsured-rate", "Rates and characteristics of the uninsured."),
                T(
                    "provider-shortage",
                    "Health professional shortage areas and unmet need.",
                ),
                T("telehealth", "Telehealth and remote care delivery."),
                T(
                    "barriers-to-care",
                    "Barriers to receiving care, including cost, coverage, distance, "
                    "transportation, wait times, discrimination, and related obstacles.",
                    "Barriers to Care",
                ),
                T("dental-access", "Access to oral and dental health services."),
            ],
            "Cost & Financing": [
                T("health-care-spending", "Total and per capita health care spending."),
                T("prescription-drug-costs", "Prescription drug pricing and spending."),
                T(
                    "affordability",
                    "Affordability of premiums, deductibles, and care.",
                ),
                T("medical-debt", "Medical debt and financial hardship."),
                T(
                    "public-program-financing",
                    "Medicaid, MinnesotaCare, and public program financing.",
                ),
            ],
            "Health Care Workforce": [
                T("primary-care-workforce", "Primary care physicians, NPs, and PAs."),
                T("nursing-workforce", "Registered nurses and licensed practical nurses."),
                T(
                    "behavioral-health-workforce",
                    "Mental health and substance use treatment providers.",
                ),
                T(
                    "rural-workforce",
                    "Workforce supply and retention outside metro areas.",
                ),
                T(
                    "workforce-training",
                    "Education, residency, and pipeline programs.",
                ),
                T(
                    "workforce-diversity",
                    "Diversity and cultural representation in the workforce.",
                ),
            ],
            "Facilities & Services": [
                T("hospitals", "Hospital capacity, utilization, and finances."),
                T(
                    "community-health-centers",
                    "Federally qualified and community health centers.",
                ),
                T(
                    "long-term-care",
                    "Nursing facilities and home and community-based services.",
                ),
                T("emergency-services", "Emergency departments and ambulance services."),
                T(
                    "rural-health-clinics",
                    "Rural clinics and critical access hospitals.",
                ),
            ],
            "Quality & Outcomes": [
                T("patient-safety", "Adverse events and patient safety reporting."),
                T("care-quality", "Clinical quality measurement and performance."),
                T("health-outcomes", "Population-level health outcome measures."),
                T(
                    "patient-experience",
                    "Patient-reported experience and satisfaction.",
                ),
            ],
        },
    ),
    "D": (
        "Determinants & Equity",
        "Social, economic, and community conditions that shape health, and "
        "the disparities that result from them.",
        {
            "Social Determinants": [
                T("housing", "Housing quality, cost, and stability."),
                T(
                    "food-security",
                    "Food access, insecurity, and nutrition programs.",
                ),
                T("education", "Educational attainment and school-based health."),
                T(
                    "employment",
                    "Employment, working conditions, and job quality.",
                ),
                T(
                    "low-income",
                    "Low-income households, poverty, and economic stability.",
                    "Low Income",
                ),
                T("child-care-access", "Availability and affordability of child care."),
            ],
            "Health Equity": [
                T(
                    "health-disparities",
                    "Differences in health outcomes between populations.",
                ),
                T(
                    "structural-racism",
                    "Structural and institutional drivers of inequity.",
                ),
                T(
                    "language-access",
                    "Interpretation, translation, and language services as a topic. "
                    "Do not use this tag only because a file is translated; set "
                    "Publication Language instead.",
                ),
                T(
                    "cultural-responsiveness",
                    "Culturally responsive and community-informed care.",
                ),
                T(
                    "disability-equity",
                    "Equitable access for people with disabilities.",
                ),
            ],
            "Community Conditions": [
                T(
                    "built-environment",
                    "Housing stock, transit, parks, and neighborhood design.",
                ),
                T("community-safety", "Neighborhood safety and violence prevention."),
                T(
                    "social-connectedness",
                    "Social support, isolation, belonging, and connection to others "
                    "as a determinant of health.",
                ),
                T(
                    "broadband-access",
                    "Internet and broadband access as a determinant of health and "
                    "telehealth access.",
                ),
            ],
        },
    ),
    "E": (
        "Public Health Practice",
        "How public health work itself is carried out: surveillance, "
        "programs, policy, preparedness, and partnerships.",
        {
            "Surveillance & Data": [
                T("vital-statistics", "Births, deaths, and vital records."),
                T(
                    "disease-surveillance",
                    "Reportable disease and syndromic surveillance.",
                ),
                T(
                    "survey-data",
                    "Population surveys such as BRFSS and student surveys.",
                ),
                T("data-quality", "Data completeness, accuracy, and methods."),
                T("registries", "Disease and immunization registries."),
            ],
            "Programs & Interventions": [
                T("health-promotion", "Health promotion and education campaigns."),
                T(
                    "screening-programs",
                    "Population screening and early detection programs.",
                ),
                T(
                    "immunization-programs",
                    "Vaccination delivery and coverage programs.",
                ),
                T("home-visiting", "Family home visiting and early intervention."),
                T(
                    "program-evaluation",
                    "Evaluation of program implementation and impact.",
                ),
            ],
            "Policy & Regulation": [
                T("public-health-policy", "Policy analysis and recommendations."),
                T(
                    "licensing-regulation",
                    "Facility and professional licensing and oversight.",
                ),
                T("statute-rule", "Statutory and rulemaking requirements."),
                T("legislative-reporting", "Reports prepared for the legislature."),
            ],
            "Emergency Preparedness": [
                T(
                    "emergency-response",
                    "Public health emergency response operations.",
                ),
                T(
                    "outbreak-investigation",
                    "Outbreak detection and investigation.",
                ),
                T(
                    "preparedness-planning",
                    "Preparedness planning and exercises.",
                ),
                T(
                    "medical-countermeasures",
                    "Stockpiles and distribution of vaccines, antivirals, PPE, and "
                    "other medical countermeasures.",
                ),
            ],
            "Partnerships": [
                T("local-public-health", "Local public health departments and CHBs."),
                T(
                    "tribal-health-partnerships",
                    "Partnerships with tribal health systems.",
                ),
                T(
                    "community-partnerships",
                    "Community-based organizations and coalitions.",
                ),
                T(
                    "academic-partnerships",
                    "Research and academic collaborations.",
                ),
            ],
        },
    ),
}

# Nan's controlled list, with Data Brief as the short statistical product
# (more applicable than Chartbook for typical MDH CHS briefs). Scope notes
# follow NIH/NLM publication-type practice at a library scale.
DOCUMENT_TYPES = [
    (
        "Data Brief",
        "Compact statistical product: figures and tables with limited narrative. "
        "Use for short CHS briefs and similar chart-forward products.",
    ),
    (
        "Dictionary or Glossary",
        "Work consisting of definitions of terms in a subject field.",
    ),
    (
        "Fact Sheet",
        "Short, single-topic briefing for the public or professionals "
        "(NLM Fact Sheets).",
    ),
    (
        "Guidance Document",
        "Statements, directions, or principles presenting recommended practice "
        "or policy. Corresponds to NLM Guideline, not statute itself.",
    ),
    (
        "Infographic",
        "Visual one-pager or pictorial work whose primary content is graphic.",
    ),
    (
        "Journal Article",
        "Article published in a journal, including peer-reviewed literature.",
    ),
    (
        "Legislation or Policy",
        "Statute, adopted rule, or official policy text, including reports "
        "whose primary purpose is legislative or policy (NLM Legislation).",
    ),
    (
        "Map",
        "Cartographic work as the primary content (NLM Maps).",
    ),
    (
        "Press Release",
        "News announcement issued for media or public distribution.",
    ),
    (
        "Program Evaluation",
        "Assessment of program implementation, reach, or impact.",
    ),
    (
        "Report",
        "Substantial narrative with findings or recommendations "
        "(NLM Report / Technical Report). Default when no more specific type fits.",
    ),
]


def build(out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)

    with (out_dir / "facets.csv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["facet_code", "facet_name", "description"])
        for code, (name, description, _groups) in TAXONOMY.items():
            writer.writerow([code, name, description])

    tag_rows = []
    for code, (name, _description, groups) in TAXONOMY.items():
        for group_name, tags in groups.items():
            for slug, tag_name, tag_description in tags:
                tag_rows.append(
                    {
                        "tag": slug,
                        "name": tag_name,
                        "facet_code": code,
                        "facet_name": name,
                        "description": tag_description,
                        "parent": group_name,
                    }
                )

    seen = {}
    for row in tag_rows:
        if row["tag"] in seen:
            raise SystemExit(
                f"Duplicate tag slug {row['tag']!r} in facets "
                f"{seen[row['tag']]} and {row['facet_code']}; Tag.slug is unique."
            )
        seen[row["tag"]] = row["facet_code"]

    with (out_dir / "tags.csv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(
            ["tag", "name", "facet_code", "facet_name", "description", "parent", "examples"]
        )
        for row in tag_rows:
            writer.writerow(
                [
                    row["tag"],
                    row["name"],
                    row["facet_code"],
                    row["facet_name"],
                    row["description"],
                    row["parent"],
                    "[]",
                ]
            )

    with (out_dir / "tags_by_facet.csv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(
            ["facet_code", "facet_name", "tag", "parent_category", "description"]
        )
        for row in tag_rows:
            writer.writerow(
                [
                    row["facet_code"],
                    row["facet_name"],
                    row["tag"],
                    row["parent"],
                    row["description"],
                ]
            )

    with (out_dir / "document_types.csv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["document_type", "scope_note"])
        for name, scope_note in DOCUMENT_TYPES:
            writer.writerow([name, scope_note])

    groups = sum(len(g) for _n, _d, g in TAXONOMY.values())
    print(
        f"Wrote {len(TAXONOMY)} facets, {groups} topic groups, "
        f"{len(tag_rows)} tags, {len(DOCUMENT_TYPES)} document types to {out_dir}"
    )


if __name__ == "__main__":
    build(Path(__file__).resolve().parent)
