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
        'title': 'Assistant Commissioner',
        'bureau': 'Health Operations Bureau',
        'initials': 'MG',
        'color': 'gray',
        'context': """
            Mel Gresczyk leads the Health Operations Bureau: licensing, certification, vital records,
            health care facilities regulation, and operational backbone services. Current pressures
            include workforce retention in regulatory programs, modernizing licensing systems, and
            sustaining operations amid federal funding uncertainty.
        """,
    },
    {
        'id': 'ac_health_equity_acting',
        'name': 'Wendy Underwood',
        'title': 'Assistant Commissioner (Acting)',
        'bureau': 'Health Equity Bureau',
        'initials': 'WU',
        'color': 'teal',
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
