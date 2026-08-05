"""Single source of truth for the starter publications taxonomy.

Run this to regenerate the four CSVs in this directory, which
``manage.py seed_mdh_publications_taxonomy`` reads:

    python mdh_publications/data/build_taxonomy.py

NOTE ON PROVENANCE: this is a *starter* vocabulary covering standard public
health domains. It is not an official Minnesota Department of Health
taxonomy. Replace TAXONOMY / DOCUMENT_TYPES below with the real vocabulary
when it is available, re-run this script, and re-run the seed command --
the importer uses update_or_create keyed on slug, so re-seeding revises
existing rows rather than duplicating them.

Structure: facet code -> (facet name, facet description, topic groups),
where each topic group maps to a list of (tag slug, tag description).
Tag slugs must be unique across the whole taxonomy: Tag.slug is unique.
"""

import csv
from pathlib import Path

TAXONOMY = {
    "A": (
        "Demographics & Populations",
        "Who a publication is about: age, race and ethnicity, geography, and "
        "populations that experience distinct health needs or barriers.",
        {
            "Age Groups": [
                ("infants", "Children under one year of age."),
                ("children", "Pediatric populations, roughly ages 1 to 12."),
                ("adolescents", "Youth and teenagers, roughly ages 13 to 19."),
                ("young-adults", "Adults roughly ages 20 to 34."),
                ("adults", "Working-age adults, roughly ages 35 to 64."),
                ("older-adults", "Adults age 65 and older."),
            ],
            "Race & Ethnicity": [
                ("american-indian", "American Indian and Alaska Native populations."),
                ("asian-populations", "Asian and Asian American populations."),
                ("black-populations", "Black and African American populations."),
                ("hispanic-latino", "Hispanic and Latino populations."),
                ("pacific-islander", "Native Hawaiian and Pacific Islander populations."),
                ("white-populations", "White populations."),
                ("multiracial", "People identifying with two or more races."),
            ],
            "Geography": [
                ("statewide", "Statewide figures covering all of Minnesota."),
                ("twin-cities-metro", "The seven-county Twin Cities metropolitan area."),
                ("greater-minnesota", "Minnesota outside the Twin Cities metro."),
                ("rural-communities", "Rural and small-town communities."),
                ("tribal-nations", "Tribal nations and reservation communities."),
                ("county-level", "Data reported at the county level."),
            ],
            "Priority Populations": [
                ("immigrants-refugees", "Immigrant, refugee, and newcomer communities."),
                ("veterans", "Military veterans and their families."),
                ("lgbtq-populations", "Lesbian, gay, bisexual, transgender, and queer people."),
                ("people-with-disabilities", "People living with physical or cognitive disabilities."),
                ("pregnant-people", "People who are pregnant or postpartum."),
                ("uninsured-populations", "People without health insurance coverage."),
                ("people-experiencing-homelessness", "People experiencing housing instability or homelessness."),
            ],
        },
    ),
    "B": (
        "Health Conditions & Topics",
        "The health condition, disease, or clinical subject a publication "
        "addresses.",
        {
            "Chronic Disease": [
                ("cancer", "Cancer incidence, screening, treatment, and survivorship."),
                ("cardiovascular-disease", "Heart disease, stroke, and hypertension."),
                ("diabetes", "Type 1 and type 2 diabetes and prediabetes."),
                ("asthma", "Asthma and chronic respiratory conditions."),
                ("obesity", "Obesity, nutrition, and physical activity."),
                ("kidney-disease", "Chronic kidney disease and dialysis care."),
            ],
            "Infectious Disease": [
                ("covid-19", "COVID-19 surveillance, response, and long-term effects."),
                ("influenza", "Seasonal and pandemic influenza."),
                ("hiv-aids", "HIV and AIDS prevention, testing, and care."),
                ("sexually-transmitted-infections", "Sexually transmitted infections and reporting."),
                ("tuberculosis", "Tuberculosis screening, treatment, and contact tracing."),
                ("vaccine-preventable-disease", "Measles, pertussis, and other vaccine-preventable illness."),
                ("antimicrobial-resistance", "Antibiotic resistance and stewardship."),
            ],
            "Behavioral Health": [
                ("mental-health", "Mental health conditions, treatment, and access."),
                ("substance-use", "Substance use disorders and treatment services."),
                ("opioids", "Opioid use, overdose, and harm reduction."),
                ("tobacco", "Tobacco, vaping, and cessation programs."),
                ("alcohol", "Alcohol use and related harms."),
                ("suicide-prevention", "Suicide surveillance and prevention efforts."),
            ],
            "Maternal & Child Health": [
                ("prenatal-care", "Access to and quality of prenatal care."),
                ("birth-outcomes", "Preterm birth, low birth weight, and delivery outcomes."),
                ("infant-mortality", "Infant and perinatal mortality."),
                ("maternal-mortality", "Maternal deaths and severe maternal morbidity."),
                ("breastfeeding", "Breastfeeding initiation, duration, and support."),
                ("child-development", "Early childhood development and screening."),
            ],
            "Injury & Violence": [
                ("unintentional-injury", "Falls, poisonings, and other unintentional injuries."),
                ("motor-vehicle-crashes", "Traffic-related injuries and deaths."),
                ("firearm-injury", "Firearm-related injuries and deaths."),
                ("domestic-violence", "Intimate partner and family violence."),
                ("child-maltreatment", "Child abuse and neglect."),
                ("occupational-injury", "Workplace injuries and illnesses."),
            ],
            "Environmental Health": [
                ("air-quality", "Outdoor and indoor air quality."),
                ("water-quality", "Drinking water, wells, and recreational water."),
                ("lead-exposure", "Childhood and occupational lead exposure."),
                ("climate-health", "Health effects of extreme heat, flooding, and climate change."),
                ("foodborne-illness", "Food safety and foodborne outbreaks."),
                ("environmental-contaminants", "Chemical contaminants and hazardous exposures."),
            ],
        },
    ),
    "C": (
        "Health System & Access",
        "How care is organized, staffed, financed, and reached, including "
        "coverage, cost, workforce, and facilities.",
        {
            "Access to Care": [
                ("insurance-coverage", "Health insurance coverage and enrollment."),
                ("uninsured-rate", "Rates and characteristics of the uninsured."),
                ("provider-shortage", "Health professional shortage areas and unmet need."),
                ("telehealth", "Telehealth and remote care delivery."),
                ("transportation-barriers", "Transportation as a barrier to receiving care."),
                ("dental-access", "Access to oral and dental health services."),
            ],
            "Cost & Financing": [
                ("health-care-spending", "Total and per capita health care spending."),
                ("prescription-drug-costs", "Prescription drug pricing and spending."),
                ("affordability", "Affordability of premiums, deductibles, and care."),
                ("medical-debt", "Medical debt and financial hardship."),
                ("public-program-financing", "Medicaid, MinnesotaCare, and public program financing."),
            ],
            "Health Care Workforce": [
                ("primary-care-workforce", "Primary care physicians, NPs, and PAs."),
                ("nursing-workforce", "Registered nurses and licensed practical nurses."),
                ("behavioral-health-workforce", "Mental health and substance use treatment providers."),
                ("rural-workforce", "Workforce supply and retention outside metro areas."),
                ("workforce-training", "Education, residency, and pipeline programs."),
                ("workforce-diversity", "Diversity and cultural representation in the workforce."),
            ],
            "Facilities & Services": [
                ("hospitals", "Hospital capacity, utilization, and finances."),
                ("community-health-centers", "Federally qualified and community health centers."),
                ("long-term-care", "Nursing facilities and home and community-based services."),
                ("emergency-services", "Emergency departments and ambulance services."),
                ("rural-health-clinics", "Rural clinics and critical access hospitals."),
            ],
            "Quality & Outcomes": [
                ("patient-safety", "Adverse events and patient safety reporting."),
                ("readmissions", "Hospital readmissions and care transitions."),
                ("care-quality", "Clinical quality measurement and performance."),
                ("health-outcomes", "Population-level health outcome measures."),
                ("patient-experience", "Patient-reported experience and satisfaction."),
            ],
        },
    ),
    "D": (
        "Determinants & Equity",
        "Social, economic, and community conditions that shape health, and "
        "the disparities that result from them.",
        {
            "Social Determinants": [
                ("housing", "Housing quality, cost, and stability."),
                ("food-security", "Food access, insecurity, and nutrition programs."),
                ("education", "Educational attainment and school-based health."),
                ("employment", "Employment, working conditions, and job quality."),
                ("income-poverty", "Income, poverty, and economic stability."),
                ("child-care-access", "Availability and affordability of child care."),
            ],
            "Health Equity": [
                ("health-disparities", "Differences in health outcomes between populations."),
                ("structural-racism", "Structural and institutional drivers of inequity."),
                ("language-access", "Interpretation, translation, and language services."),
                ("cultural-responsiveness", "Culturally responsive and community-informed care."),
                ("disability-equity", "Equitable access for people with disabilities."),
            ],
            "Community Conditions": [
                ("built-environment", "Housing stock, transit, parks, and neighborhood design."),
                ("community-safety", "Neighborhood safety and violence prevention."),
                ("social-connectedness", "Social support, isolation, and belonging."),
                ("broadband-access", "Internet access as a determinant of health care access."),
            ],
        },
    ),
    "E": (
        "Public Health Practice",
        "How public health work itself is carried out: surveillance, "
        "programs, policy, preparedness, and partnerships.",
        {
            "Surveillance & Data": [
                ("vital-statistics", "Births, deaths, and vital records."),
                ("disease-surveillance", "Reportable disease and syndromic surveillance."),
                ("survey-data", "Population surveys such as BRFSS and student surveys."),
                ("data-quality", "Data completeness, accuracy, and methods."),
                ("registries", "Disease and immunization registries."),
            ],
            "Programs & Interventions": [
                ("health-promotion", "Health promotion and education campaigns."),
                ("screening-programs", "Population screening and early detection programs."),
                ("immunization-programs", "Vaccination delivery and coverage programs."),
                ("home-visiting", "Family home visiting and early intervention."),
                ("program-evaluation", "Evaluation of program implementation and impact."),
            ],
            "Policy & Regulation": [
                ("public-health-policy", "Policy analysis and recommendations."),
                ("licensing-regulation", "Facility and professional licensing and oversight."),
                ("statute-rule", "Statutory and rulemaking requirements."),
                ("legislative-reporting", "Reports prepared for the legislature."),
            ],
            "Emergency Preparedness": [
                ("emergency-response", "Public health emergency response operations."),
                ("outbreak-investigation", "Outbreak detection and investigation."),
                ("preparedness-planning", "Preparedness planning and exercises."),
                ("medical-countermeasures", "Stockpiles and countermeasure distribution."),
            ],
            "Partnerships": [
                ("local-public-health", "Local public health departments and CHBs."),
                ("tribal-health-partnerships", "Partnerships with tribal health systems."),
                ("community-partnerships", "Community-based organizations and coalitions."),
                ("academic-partnerships", "Research and academic collaborations."),
            ],
        },
    ),
}

DOCUMENT_TYPES = [
    "Report",
    "Data Brief",
    "Fact Sheet",
    "Surveillance Summary",
    "Dashboard",
    "Infographic",
    "Statistical Table",
    "Program Evaluation",
    "Legislative Report",
    "Guidance Document",
    "Toolkit",
    "Annual Report",
    "White Paper",
    "Presentation",
    "Newsletter",
]


def build(out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)

    with (out_dir / "facets.csv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["facet_code", "facet_name", "description"])
        for code, (name, description, _groups) in TAXONOMY.items():
            writer.writerow([code, name, description])

    # tags.csv is authoritative for tags. tags_by_facet.csv exists because the
    # importer requires all four files present to take the CSV path; it carries
    # the same facet/topic-group pairing, so both are generated together here
    # rather than hand-edited out of sync.
    tag_rows = []
    for code, (name, _description, groups) in TAXONOMY.items():
        for group_name, tags in groups.items():
            for slug, tag_description in tags:
                tag_rows.append(
                    {
                        "tag": slug,
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
            ["tag", "facet_code", "facet_name", "description", "parent", "examples"]
        )
        for row in tag_rows:
            writer.writerow(
                [
                    row["tag"],
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
        writer.writerow(["document_type"])
        for name in DOCUMENT_TYPES:
            writer.writerow([name])

    groups = sum(len(g) for _n, _d, g in TAXONOMY.values())
    print(
        f"Wrote {len(TAXONOMY)} facets, {groups} topic groups, "
        f"{len(tag_rows)} tags, {len(DOCUMENT_TYPES)} document types to {out_dir}"
    )


if __name__ == "__main__":
    build(Path(__file__).resolve().parent)
