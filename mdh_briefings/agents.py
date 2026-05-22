"""MDH leadership roster and per-leader simulation context."""

from __future__ import annotations

LEADERS = [
    {
        'id': 'commissioner',
        'name': 'Dr. Brooke Cunningham, MD',
        'title': 'Commissioner of Health',
        'bureau': "Commissioner's Office",
        'initials': 'BC',
        'color': 'blue',
        'context': """
            Dr. Cunningham is a physician, sociologist, and the first Black woman to lead MDH.
            She was previously assistant commissioner for the Health Equity Bureau. Her priorities
            are health equity, public health system transformation, and navigating federal funding
            cuts (MDH lost $38M+ in CDC/PHIG grants in Feb 2026 and $226M in COVID-era grants in
            2025). MDH has ~2,075 staff and 7 regional offices. She chairs the Healthy Minnesota
            Partnership and represents MDH in legislative and intergovernmental settings.
        """,
    },
    {
        'id': 'deputy_commissioner',
        'name': 'Wendy Underwood',
        'title': 'Deputy Commissioner',
        'bureau': "Commissioner's Office",
        'initials': 'WU',
        'color': 'blue',
        'context': """
            Wendy Underwood serves as Deputy Commissioner, supporting the Commissioner on agency-wide
            strategy, operations, and legislative engagement. She helps coordinate across the six
            bureaus during PHIG termination fallout, workforce stabilization, and Healthy Minnesota
            Partnership implementation. She often steps in for bureau leadership gaps and cross-bureau
            initiatives.
        """,
    },
    {
        'id': 'chief_of_staff',
        'name': 'Imee Cambronero',
        'title': 'Chief of Staff',
        'bureau': "Commissioner's Office",
        'initials': 'IC',
        'color': 'blue',
        'context': """
            Imee Cambronero manages the Commissioner's Office daily operations: briefing materials,
            scheduling, priority tracking, and internal communications. She coordinates responses to
            urgent federal and legislative developments, including grant terminations and litigation
            updates affecting MDH programs.
        """,
    },
    {
        'id': 'ac_health_operations',
        'name': 'Mel Gresczyk',
        'title': 'Assistant Commissioner, Chief Operating Officer',
        'bureau': 'Health Operations Bureau',
        'initials': 'MG',
        'color': 'gray',
        'bureau_slug': 'health_operations',
        'context': """
            Mel Gresczyk leads the Health Operations Bureau as Assistant Commissioner and Chief
            Operating Officer: health regulation, emergency preparedness, HR, financial management,
            facilities, organizational wellbeing, and public health strategy partnerships.
            Current pressures include workforce retention, licensing modernization, and sustaining
            operations amid federal funding uncertainty.
        """,
    },
    {
        'id': 'ac_health_equity_acting',
        'name': 'Wendy Underwood',
        'title': 'Assistant Commissioner (Acting)',
        'bureau': 'Health Equity Bureau',
        'initials': 'WU',
        'color': 'teal',
        'bureau_slug': 'health_equity',
        'context': """
            Wendy Underwood is serving in an acting capacity as Assistant Commissioner for the Health
            Equity Bureau while maintaining Deputy Commissioner duties. The bureau advances health equity
            policy, community partnerships, and data-driven equity initiatives under Healthy Minnesota
            2025-2029 goals. Key pressures: sustaining equity programs after federal cuts, rural and
            tribal health access gaps, and embedding equity across all MDH bureaus.
        """,
    },
    {
        'id': 'ac_health_improvement',
        'name': 'Robsan (Halkeno) Tura',
        'title': 'Assistant Commissioner',
        'bureau': 'Health Improvement Bureau',
        'initials': 'RT',
        'color': 'green',
        'bureau_slug': 'health_improvement',
        'context': """
            Robsan Tura leads the Health Improvement Bureau: chronic disease prevention, maternal and
            child health, oral health, nutrition, and community health improvement. Oversees programs
            affected by CDC grant losses including injury prevention and tobacco control. Focuses on
            rural health gaps, behavioral health integration, and partnership with local public health.
        """,
    },
    {
        'id': 'ac_health_protection',
        'name': 'Myra Kunas',
        'title': 'Assistant Commissioner',
        'bureau': 'Health Protection Bureau',
        'initials': 'MK',
        'color': 'orange',
        'bureau_slug': 'health_protection',
        'context': """
            Myra Kunas leads the Health Protection Bureau encompassing infectious disease, environmental
            health, emergency preparedness coordination, and the State Public Health Laboratory. The bureau
            faces heightened scrutiny after PHIG cuts, ongoing H5N1 and respiratory disease surveillance,
            water quality concerns, and federal litigation affecting public health authority.
        """,
    },
    {
        'id': 'ac_health_systems',
        'name': 'Carol Backstrom',
        'title': 'Assistant Commissioner',
        'bureau': 'Health Systems Bureau',
        'initials': 'CB',
        'color': 'purple',
        'bureau_slug': 'health_systems',
        'context': """
            Carol Backstrom leads the Health Systems Bureau: health policy, Medicaid and state health
            program alignment, hospital and clinic systems, and health care workforce. Priorities include
            rural hospital sustainability, health care access in underserved areas, and navigating state
            budget constraints alongside federal Medicaid policy changes.
        """,
    },
    {
        'id': 'cfo',
        'name': 'Joshua Bunker',
        'title': 'Chief Financial Officer',
        'bureau': 'Financial Management Division',
        'initials': 'JB',
        'color': 'gray',
        'context': """
            Joshua Bunker oversees MDH financial management, budgeting, grants administration, and fiscal
            compliance. He is central to restructuring after $38M PHIG termination (Feb 2026) and
            $226M COVID-era grant reductions (2025), reprogramming state funds, and grant closeout
            obligations across bureaus.
        """,
    },
    {
        'id': 'director_data_strategy_interop',
        'name': 'Chris Brueske',
        'title': 'Director, Office of Data Strategy and Interoperability',
        'bureau': 'Office of Data and Analytics',
        'initials': 'CB',
        'color': 'gray',
        'context': """
            Chris Brueske directs the Office of Data Strategy and Interoperability within the
            Office of Data and Analytics: FHIR and interoperability programs, the Data Exchange Hub,
            and cross-bureau informatics alignment with MNIT Health and program areas.
        """,
    },
    {
        'id': 'facilities_manager',
        'name': 'Kevin Umidon',
        'title': 'Facilities Manager',
        'bureau': 'Facilities Management Division',
        'initials': 'KU',
        'color': 'gray',
        'context': """
            Kevin Umidon manages MDH facilities: Freeman and Public Health Lab building services,
            regional offices, facility services, and capital stewardship for agency locations.
        """,
    },
    {
        'id': 'director_legislative_relations',
        'name': 'Lisa Thimjon',
        'title': 'Director, Office of Legislative Relations',
        'bureau': "Commissioner's Office",
        'initials': 'LT',
        'color': 'blue',
        'context': """
            Lisa Thimjon leads legislative relations for MDH: bill tracking, committee testimony
            coordination, and agency positions on health policy at the Capitol.
        """,
    },
    {
        'id': 'director_public_health_strategy',
        'name': 'Chelsie Huntley',
        'title': 'Director, Public Health Strategy and Partnership',
        'bureau': 'Health Operations Bureau',
        'initials': 'CH',
        'color': 'gray',
        'context': """
            Chelsie Huntley directs public health strategy and partnership, aligning MDH bureaus
            with local public health and Healthy Minnesota Partnership implementation.
        """,
    },
    {
        'id': 'director_american_indian_health',
        'name': 'Kris Rhodes',
        'title': 'Director, Office of American Indian Health and Tribal Relations',
        'bureau': 'Health Equity Bureau',
        'initials': 'KR',
        'color': 'teal',
        'context': """
            Kris Rhodes leads tribal relations and American Indian health initiatives, government-to-
            government partnership, and culturally responsive public health programs.
        """,
    },
    {
        'id': 'director_african_american_health',
        'name': 'Aisha Ellis',
        'title': 'Director, Office of African American Health',
        'bureau': 'Health Equity Bureau',
        'initials': 'AE',
        'color': 'teal',
        'context': """
            Aisha Ellis directs the Office of African American Health, focused on disparities
            reduction and community-centered equity programs.
        """,
    },
    {
        'id': 'director_dibe',
        'name': 'Shalome Musigñac Jordán',
        'title': 'Director, Office of Diversity, Inclusion, Belonging, and Equity Strategy',
        'bureau': 'Health Equity Bureau',
        'initials': 'SM',
        'color': 'teal',
        'context': """
            Shalome Musigñac Jordán leads DIBE strategy: belonging, inclusion, and equity systems
            change across MDH workforce and programs.
        """,
    },
    {
        'id': 'deputy_coo_operations',
        'name': 'Mike Boettcher',
        'title': 'Director of Operations, Deputy Chief Operating Officer',
        'bureau': 'Office of Diversity, Inclusion, Belonging, and Equity Strategy',
        'initials': 'MB',
        'color': 'gray',
        'context': """
            Mike Boettcher serves as Deputy Chief Operating Officer and Director of Operations,
            supporting agency-wide operations planning and cross-bureau coordination.
        """,
    },
    {
        'id': 'mnit_health_cbto',
        'name': 'Brenda Gabriel',
        'title': 'Chief Business Technology Officer (Interim)',
        'bureau': 'MNIT Health',
        'initials': 'BG',
        'color': 'purple',
        'context': """
            Brenda Gabriel serves as interim Chief Business Technology Officer for MNIT Health,
            Minnesota IT Services' partnership with the Minnesota Department of Health. She has
            decades of state service (since 1991) including MDH since 1998, and recently led
            migration of many MDH applications to cloud infrastructure.

            Scope spans enterprise applications, hosting, service desk alignment, emergency
            preparedness systems (Medical PreCheck, POD Locator), and interoperable data exchange
            with external partners during outbreaks. Priorities: cloud cost and security governance,
            MEDSS and program system reliability amid grant cuts, FHIR-ready interfaces with MDH
            analytics teams, and surge capacity for epidemiology and operations during incidents.
        """,
    },
    {
        'id': 'general_counsel',
        'name': 'Robin C. Benson',
        'title': 'General Counsel',
        'bureau': "General Counsel's Office",
        'initials': 'RB',
        'color': 'gray',
        'context': """
            Robin C. Benson leads MDH legal affairs: rulemaking, contracts, employment law, intergovernmental
            agreements, and litigation strategy. Active issues include federal preemption questions,
            public health authority challenges, data sharing agreements, and legal review of emergency
            and infectious disease orders.
        """,
    },
    {
        'id': 'state_epidemiologist',
        'name': 'Ruth Lynfield',
        'title': 'State Epidemiologist',
        'bureau': 'Health Protection Bureau',
        'initials': 'RL',
        'color': 'orange',
        'context': """
            Dr. Ruth Lynfield serves as State Epidemiologist, directing disease surveillance, outbreak
            investigation, and epidemiologic consultation statewide. She leads response to respiratory
            viruses, foodborne outbreaks, healthcare-associated infections, and maintains CDC data
            sharing relationships strained by recent federal funding cuts.
        """,
    },
    {
        'id': 'cdao',
        'name': 'John Li',
        'title': 'Chief Data & Analytics Officer',
        'bureau': 'Office of Data and Analytics',
        'initials': 'JL',
        'color': 'gray',
        'context': """
            John Li leads MDH data strategy, analytics, interoperability, and public health informatics.
            Priorities include modernizing reporting systems, equity-focused data dashboards, supporting
            outbreak surveillance with reduced federal IT funding, and Minnesota Electronic Disease
            Surveillance System (MEDSS) enhancements.
        """,
    },
    {
        'id': 'director_center_health_statistics',
        'name': 'Daniel Fernandez-Baca',
        'title': 'Director, Minnesota Center for Health Statistics',
        'bureau': 'Minnesota Center for Health Statistics',
        'initials': 'DF',
        'color': 'gray',
        'context': """
            Daniel Fernandez-Baca directs the Minnesota Center for Health Statistics (MCHS) within
            MDH's Office of Data and Analytics. MCHS is the state's principal health statistics
            authority: vital records analytics, BRFSS and other population surveys, hospitalization
            and utilization data, small-area health indicators, and data products supporting Healthy
            Minnesota Partnership 2025-2029 reporting.

            The Center partners with CDC/NCHS, MDH epidemiology and bureaus, local public health, and
            tribal nations on standardized measures, privacy-protected release, and survey operations.
            Pressures include maintaining timeliness after federal grant cuts (PHIG $38M+ Feb 2026;
            $226M COVID-era reductions), modernizing public-facing data portals, workforce capacity
            for survey and registry coordination, and aligning statistics with new interoperability
            and equity reporting demands.
        """,
    },
    {
        'id': 'senior_data_scientist_interop',
        'name': 'Eric Kvale',
        'title': 'Senior Data Scientist, Data Strategy and Interoperability',
        'bureau': 'Office of Data and Analytics',
        'initials': 'EK',
        'color': 'gray',
        'extended_briefing': True,
        'context': """
            Eric Kvale serves as Senior Data Scientist for Data Strategy and Interoperability within
            MDH's Office of Data and Analytics, reporting through the Chief Data & Analytics Officer.
            Scope spans enterprise data strategy, public health informatics standards (FHIR R4, USCDI,
            TEFCA/QHIN), cross-bureau data governance, and hands-on analytics that turn fragmented
            program data into decision-ready products for leadership.

            Core systems and partners: Minnesota Electronic Disease Surveillance System (MEDSS), eLC,
            vital records and immunization interfaces, MDH data warehouse / analytics environments,
            interagency feeds (MN-ITS, DHS, MDE), and federal pipelines (CDC NSSP, NHSN) now stressed
            by PHIG termination ($38M+, Feb 2026) and prior COVID-era grant reductions ($226M, 2025).

            Highest-value problem spaces: (1) interoperability accelerators—FHIR APIs, bulk data export,
            consent-aware record linkage for outbreak response; (2) equity-by-design metrics and
            small-area estimation for rural/tribal gaps; (3) grant-impact dashboards that attribute
            funding cuts to program risk; (4) reusable ETL/quality frameworks so bureaus stop rebuilding
            pipelines; (5) responsible AI guardrails for internal summarization and coding assistance
            on sensitive public health data.

            Current pressures: reduced federal IT funding, staffing gaps in informatics, Minnesota
            Health Information Exchange alignment, litigation and policy shifts affecting data sharing,
            and Healthy Minnesota Partnership 2025-2029 indicators requiring better cross-program joins.
        """,
    },
    {
        'id': 'director_communications',
        'name': 'Allison Thrash',
        'title': 'Director, Communications',
        'bureau': 'Communications Office',
        'initials': 'AT',
        'color': 'gray',
        'context': """
            Allison Thrash directs MDH internal and external communications, media relations, and public
            information during health emergencies. She coordinates messaging on grant impacts, legislative
            priorities, and culturally competent outreach for diverse Minnesota communities.
        """,
    },
    {
        'id': 'director_health_equity_strategy',
        'name': 'Odi Akosionu-DeSouza',
        'title': 'Director, Health Equity Strategy',
        'bureau': 'Health Equity Bureau',
        'initials': 'OA',
        'color': 'teal',
        'context': """
            Odi Akosionu-DeSouza leads health equity strategy: community engagement, anti-racism initiatives,
            language access, and embedding equity in MDH policies and programs. Works closely with Healthy
            Minnesota Partnership and local health departments on disparities reduction.
        """,
    },
    {
        'id': 'director_infectious_disease',
        'name': 'Jessica Hancock-Allen',
        'title': 'Director, Infectious Disease',
        'bureau': 'Health Protection Bureau',
        'initials': 'JH',
        'color': 'orange',
        'context': """
            Jessica Hancock-Allen directs infectious disease prevention and control programs: immunizations,
            TB, HIV/STI, vaccine-preventable diseases, and healthcare infection prevention. Programs face
            funding pressure from terminated CDC/PHIG grants and increased demand for outbreak response.
        """,
    },
    {
        'id': 'director_environmental_health',
        'name': 'Tom Hogan',
        'title': 'Director, Environmental Health',
        'bureau': 'Health Protection Bureau',
        'initials': 'TH',
        'color': 'orange',
        'context': """
            Tom Hogan leads environmental health: drinking water, food safety, indoor air, climate-related
            health risks, and chemical exposure. Minnesota faces aging water infrastructure, PFAS concerns,
            and coordination with MPCA and local agencies on environmental health hazards.
        """,
    },
    {
        'id': 'director_public_health_lab',
        'name': 'Sara Vetter',
        'title': 'Director, Public Health Lab',
        'bureau': 'Health Improvement Bureau',
        'initials': 'SV',
        'color': 'green',
        'context': """
            Sara Vetter directs the Minnesota Department of Health Public Health Laboratory: clinical and
            environmental testing, newborn screening, reference microbiology, and emergency lab surge
            capacity. Lab operations depend on federal partnerships and state funding amid grant reductions.
        """,
    },
    {
        'id': 'director_emergency_preparedness',
        'name': 'Cheryl Petersen-Kroeber',
        'title': 'Director, Emergency Preparedness',
        'bureau': 'Health Operations Bureau',
        'initials': 'CP',
        'color': 'gray',
        'context': """
            Cheryl Petersen-Kroeber leads public health emergency preparedness and response: hospital
            readiness, medical countermeasures, exercise planning, and coordination with EMS and homeland
            security partners. Post-COVID grant cuts challenge sustaining preparedness infrastructure
            across Minnesota's regions.
        """,
    },
]


def leader_by_id(leader_id: str) -> dict | None:
    for leader in LEADERS:
        if leader['id'] == leader_id:
            return leader
    return None
