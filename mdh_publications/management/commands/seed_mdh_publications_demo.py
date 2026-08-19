"""Populate the library with realistic demo content.

    python manage.py seed_mdh_publications_demo
    python manage.py seed_mdh_publications_demo --reset

Differs from seed_mdh_publications_samples, which exists for development:
that command writes placeholder descriptions and assigns tags at random, so
filtering by a tag returns an arbitrary set and the pages read as noise.
This one carries hand-written descriptions, and each publication is tagged
with terms that actually describe it, so facet and tag filtering
demonstrates something true.

The content is illustrative, written for demonstration. It does not
reproduce real Minnesota Department of Health publications, and the figures
in the descriptions are invented.
"""

from datetime import date

from django.core.management.base import BaseCommand, CommandError

from mdh_publications.models import DocumentType, LandingImage, Publication, Tag

# (title, document type, ISO date, status, featured, description, tag slugs)
DEMO_PUBLICATIONS = [
    (
        "Cancer Screening Participation in Greater Minnesota",
        "Data Brief", "2025-09-15", "published", True,
        "Screening participation for breast, cervical, and colorectal cancer "
        "outside the Twin Cities metro, by county and age group. Screening "
        "completion outside the metro trails statewide rates across all three "
        "cancers examined, with the widest gap among adults aged 50 to 64 in "
        "counties without a local screening program. Travel distance to the "
        "nearest facility is the strongest single correlate.",
        ["cancer", "screening-programs", "greater-minnesota", "rural-communities",
         "adults", "barriers-to-care"],
    ),
    (
        "Opioid Overdose Deaths: Annual Surveillance Summary",
        "Data Brief", "2025-06-30", "published", True,
        "Statewide overdose mortality, including drug type, county, and "
        "demographic breakdowns, with naloxone distribution figures. Overdose "
        "deaths involving synthetic opioids continued to account for the majority "
        "of drug deaths. Rates remained highest among American Indian residents. "
        "Counties with saturated naloxone distribution recorded lower "
        "fatality-to-encounter ratios.",
        ["opioids", "substance-use", "american-indian", "statewide",
         "disease-surveillance", "health-disparities"],
    ),
    (
        "Maternal Mortality Review Committee Findings",
        "Legislation or Policy", "2025-03-01", "published", True,
        "Case review of pregnancy-associated deaths, contributing factors, "
        "and prevention recommendations submitted to the legislature. The "
        "committee reviewed pregnancy-associated deaths and judged a majority "
        "preventable. Mental health conditions and hemorrhage were the leading "
        "underlying causes. Disparities by race persisted after adjusting for "
        "age and insurance status.",
        ["maternal-mortality", "pregnant-people", "mental-health",
         "health-disparities", "legislative-reporting", "black-populations"],
    ),
    (
        "Health Insurance Coverage and the Uninsured",
        "Report", "2025-02-10", "published", False,
        "Coverage rates by source, income, and region, with characteristics "
        "of Minnesotans who remain uninsured. The uninsured rate held roughly "
        "steady statewide, masking increases among young adults and self-employed "
        "workers. Cost remains the most commonly cited reason for going without "
        "coverage.",
        ["insurance-coverage", "uninsured-rate", "uninsured-populations",
         "affordability", "young-adults", "statewide"],
    ),
    (
        "Rural Primary Care Workforce Capacity",
        "Report", "2024-11-20", "published", True,
        "Supply, distribution, and projected retirement of primary care "
        "clinicians practicing outside metropolitan areas. More than a third of "
        "rural primary care physicians are within ten years of expected "
        "retirement, concentrated in counties already designated as shortage "
        "areas. Advanced practice clinicians have absorbed much of the growth "
        "in visit volume.",
        ["primary-care-workforce", "rural-workforce", "provider-shortage",
         "rural-communities", "workforce-training", "greater-minnesota"],
    ),
    (
        "Childhood Lead Exposure Testing and Follow-Up",
        "Data Brief", "2024-10-05", "published", False,
        "Blood lead testing rates among children under six and follow-up "
        "after an elevated result, by housing age and region. Testing coverage "
        "varies substantially by county. Elevated results cluster in census "
        "tracts with the oldest housing stock. Follow-up testing within the "
        "recommended window occurred in fewer than half of elevated cases.",
        ["lead-exposure", "children", "housing", "built-environment",
         "environmental-contaminants", "county-level"],
    ),
    (
        "Adolescent Mental Health and School Connectedness",
        "Report", "2024-09-12", "published", True,
        "Student survey findings on anxiety, depression, and the protective "
        "role of connection to school and trusted adults. Students reporting a "
        "trusted adult at school were substantially less likely to report "
        "persistent sadness or suicidal ideation. The association held across "
        "grade, region, and family income.",
        ["mental-health", "adolescents", "education", "suicide-prevention",
         "social-connectedness", "survey-data"],
    ),
    (
        "Nursing Facility Capacity and Staffing",
        "Report", "2024-08-01", "published", False,
        "Licensed bed capacity, occupancy, and direct care staffing across "
        "long-term care facilities. Occupancy recovered unevenly, with rural "
        "facilities reporting the greatest difficulty filling direct care roles. "
        "Several facilities reduced licensed capacity rather than operate "
        "understaffed.",
        ["long-term-care", "nursing-workforce", "older-adults",
         "rural-communities", "licensing-regulation", "care-quality"],
    ),
    (
        "Drinking Water Contaminants of Emerging Concern",
        "Guidance Document", "2024-06-18", "published", False,
        "Sampling results for per- and polyfluoroalkyl substances in public "
        "water systems, with guidance for operators. Detections were concentrated "
        "near known industrial and firefighting foam use. Guidance covers sampling "
        "frequency, treatment options, and public notification thresholds for "
        "affected systems.",
        ["water-quality", "environmental-contaminants", "public-health-policy",
         "local-public-health", "statewide"],
    ),
    (
        "Telehealth Use After the Public Health Emergency",
        "Data Brief", "2024-05-22", "published", False,
        "Telehealth visit volume by service type, region, and broadband "
        "availability following the end of emergency flexibilities. Telehealth "
        "use settled well above pre-2020 levels but far below its peak, with "
        "behavioral health retaining the highest share. Counties with weaker "
        "broadband saw the sharpest decline.",
        ["telehealth", "broadband-access", "behavioral-health-workforce",
         "rural-communities", "health-care-spending"],
    ),
    (
        "Immunization Coverage Among Kindergarten Students",
        "Data Brief", "2024-04-10", "published", False,
        "School-reported immunization and exemption rates by district and "
        "vaccine series. Statewide coverage declined modestly for the second "
        "consecutive year. Conscientious exemptions rose in a small number of "
        "districts, several of which fall below the threshold for measles herd "
        "immunity.",
        ["immunization-programs", "vaccine-preventable-disease", "children",
         "education", "registries", "county-level"],
    ),
    (
        "Food Insecurity and Health Outcomes",
        "Report", "2024-02-28", "published", False,
        "The relationship between household food insecurity and chronic "
        "disease management, drawing on survey and clinical data. Food-insecure "
        "households reported worse diabetes and hypertension control. Participation "
        "in nutrition assistance was associated with narrowed but not eliminated "
        "differences.",
        ["food-security", "diabetes", "cardiovascular-disease",
         "low-income", "health-disparities", "survey-data"],
    ),
    (
        "Tribal Public Health Partnership Evaluation",
        "Program Evaluation", "2023-12-15", "published", False,
        "Evaluation of joint public health initiatives with tribal nations, "
        "covering governance, data sharing, and program reach. Data sharing "
        "agreements that recognized tribal data sovereignty were associated with "
        "sustained participation. Programs designed with tribal health directors "
        "from the outset reached more households.",
        ["tribal-nations", "tribal-health-partnerships", "american-indian",
         "program-evaluation", "cultural-responsiveness"],
    ),
    (
        "Firearm Injury Surveillance",
        "Data Brief", "2023-11-02", "published", False,
        "Fatal and non-fatal firearm injuries by intent, age, and county. "
        "Suicide accounted for the majority of firearm deaths, concentrated among "
        "older men in rural counties. Non-fatal assault injuries were concentrated "
        "among young men in urban counties.",
        ["firearm-injury", "suicide-prevention", "older-adults",
         "community-safety", "disease-surveillance"],
    ),
    (
        "Prescription Drug Price Transparency",
        "Report", "2023-09-25", "published", False,
        "Reported price increases and new high-cost drug launches under the "
        "state transparency statute. Manufacturers reported price increases "
        "exceeding the statutory threshold on a substantial number of products. "
        "Specialty drugs accounted for a disproportionate share of total reported "
        "spending.",
        ["prescription-drug-costs", "health-care-spending", "affordability",
         "statute-rule", "public-health-policy"],
    ),
    (
        "Extreme Heat and Emergency Department Visits",
        "Data Brief", "2023-08-14", "published", False,
        "Heat-related emergency visits during summer heat events, by age and "
        "neighborhood tree canopy. Visit rates rose sharply above a heat index "
        "threshold, with the steepest increases among adults over 65 and outdoor "
        "workers. Neighborhoods with less tree canopy recorded higher rates.",
        ["climate-health", "emergency-services", "older-adults",
         "occupational-injury", "built-environment", "twin-cities-metro"],
    ),
    (
        "Community Health Center Performance",
        "Report", "2023-06-07", "published", False,
        "Patient volume, payer mix, and quality measures across federally "
        "qualified health centers. Centers served a growing share of uninsured "
        "and publicly insured patients while maintaining quality measure "
        "performance at or above statewide averages for several chronic disease "
        "indicators.",
        ["community-health-centers", "uninsured-populations", "care-quality",
         "public-program-financing", "language-access"],
    ),
    (
        "Foodborne Illness Outbreak Investigations",
        "Report", "2023-04-19", "published", False,
        "Outbreaks investigated during the year, by pathogen, setting, and "
        "implicated food. Investigations spanned restaurant, institutional, and "
        "private event settings. Whole genome sequencing linked several "
        "geographically dispersed clusters that traditional interviews had not "
        "connected.",
        ["foodborne-illness", "outbreak-investigation", "disease-surveillance",
         "local-public-health", "emergency-response"],
    ),
    (
        "Language Access in Clinical Settings",
        "Guidance Document", "2023-02-21", "published", False,
        "Practical guidance for health systems on interpreter services, "
        "translated materials, and measuring language access. The toolkit covers "
        "assessing patient language needs, contracting qualified interpreters, "
        "and avoiding reliance on family members. Includes sample policies and a "
        "self-assessment checklist.",
        ["language-access", "immigrants-refugees", "cultural-responsiveness",
         "patient-experience", "health-disparities"],
    ),
    (
        "Respiratory Illness Season Dashboard",
        "Data Brief", "2025-11-10", "published", False,
        "Weekly influenza, COVID-19, and RSV activity with hospitalization "
        "and test positivity trends. The dashboard reports weekly activity by "
        "region and age group, drawing on sentinel provider reporting, laboratory "
        "results, and hospital admissions.",
        ["influenza", "covid-19", "disease-surveillance", "hospitals",
         "statewide", "data-quality"],
    ),
    (
        "Home Visiting Program Outcomes",
        "Program Evaluation", "2024-07-30", "in_review", False,
        "Outcomes for families enrolled in evidence-based family home "
        "visiting, including birth outcomes and developmental screening. Enrolled "
        "families completed developmental screening at higher rates than comparison "
        "families. Preterm birth differences were not statistically significant at "
        "current sample sizes.",
        ["home-visiting", "birth-outcomes", "child-development", "infants",
         "program-evaluation", "prenatal-care"],
    ),
    (
        "Dental Care Access for Publicly Insured Adults",
        "Data Brief", "2025-01-16", "draft", False,
        "Availability of dental providers accepting public insurance, and "
        "unmet dental need by region. A minority of practicing dentists accept "
        "new publicly insured adult patients. Unmet need is highest in counties "
        "without a community dental clinic.",
        ["dental-access", "public-program-financing", "provider-shortage",
         "greater-minnesota", "adults"],
    ),
]



class Command(BaseCommand):
    help = "Populate the library with realistic demo publications."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help=(
                "Delete existing publications and landing images first. Use this "
                "to clear landing images an earlier seeding created."
            ),
        )

    def handle(self, *args, **options):
        if not Tag.objects.exists() or not DocumentType.objects.exists():
            raise CommandError(
                "No taxonomy found. Run seed_mdh_publications_taxonomy first."
            )

        if options["reset"]:
            pub_count, _ = Publication.objects.all().delete()
            # Landing images too: an earlier version of this command created
            # rows pointing at bundled images that are no longer shipped.
            img_count, _ = LandingImage.objects.all().delete()
            self.stdout.write(
                self.style.WARNING(
                    f"Deleted {pub_count} publication rows and {img_count} landing images."
                )
            )

        created, updated, missing_tags = 0, 0, set()

        for (
            title, type_name, iso_date, status, featured, description, tag_slugs
        ) in DEMO_PUBLICATIONS:
            document_type, _ = DocumentType.objects.get_or_create(
                name=type_name,
                defaults={"slug": type_name.lower().replace(" ", "-")},
            )

            publication, was_created = Publication.objects.update_or_create(
                title=title,
                defaults={
                    "description": description,
                    "document_type": document_type,
                    "publication_date": date.fromisoformat(iso_date),
                    "status": status,
                    "is_featured": featured,
                    "language": "en",
                    "source_url": "https://www.health.state.mn.us/",
                },
            )

            tags = list(Tag.objects.filter(slug__in=tag_slugs))
            missing_tags.update(set(tag_slugs) - {tag.slug for tag in tags})
            publication.tags.set(tags)
            # Facets drive the facet filter, and are derived from the tags so
            # the two can never disagree.
            publication.facets.set({tag.facet for tag in tags})

            created += was_created
            updated += not was_created

        if missing_tags:
            self.stdout.write(
                self.style.WARNING(
                    "Tag slugs not found in the loaded taxonomy (publications were "
                    "created without them): " + ", ".join(sorted(missing_tags))
                )
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"Demo content ready. Created {created}, updated {updated}, "
                f"{Publication.objects.count()} publications total "
                f"({Publication.objects.filter(status='published').count()} published, "
                f"{Publication.objects.filter(is_featured=True).count()} featured)."
            )
        )

