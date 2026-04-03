# Loans, utilities, insurance, property tax, recurring bills + KPIs + accounting contacts section.

from datetime import date
from decimal import Decimal

from django.db import migrations

T_LOAN = 'loan'
T_UTILITY = 'utility'
T_INSURANCE = 'insurance'
T_TAX = 'property_tax'
T_BILL = 'bill'
T_MAINT = 'maintenance'
T_OTHER = 'other'


def _avg4(a, b, c, d):
    return (Decimal(str(a)) + Decimal(str(b)) + Decimal(str(c)) + Decimal(str(d))) / Decimal('4')


def seed(apps, schema_editor):
    BusinessCalendarEvent = apps.get_model('dream_blue', 'BusinessCalendarEvent')
    BusinessKPIEntry = apps.get_model('dream_blue', 'BusinessKPIEntry')
    BusinessReportSection = apps.get_model('dream_blue', 'BusinessReportSection')

    rows = [
        # --- Loans (monthly payment in amount where known) ---
        {
            'title': 'NWMF loan — 0% (1 yr to Sept 2026)',
            'event_type': T_LOAN,
            'due_date': date(2025, 9, 1),
            'end_date': date(2026, 9, 30),
            'amount': None,
            'property_label': 'Portfolio',
            'interest_rate_annual': Decimal('0'),
            'account_reference': '',
            'contact_info': '',
            'notes': 'Terms per note: one year until Sept 2026. Add monthly payment when known.',
            'sort_order': 200,
        },
        {
            'title': 'Eric loan (personal)',
            'event_type': T_LOAN,
            'due_date': date(2020, 1, 1),
            'end_date': None,
            'amount': None,
            'property_label': '',
            'interest_rate_annual': None,
            'account_reference': '',
            'contact_info': 'Eric',
            'notes': 'Details / payment schedule — update in admin.',
            'sort_order': 201,
        },
        {
            'title': 'Loans from Wendy — personal funds',
            'event_type': T_LOAN,
            'due_date': date(2020, 1, 1),
            'end_date': None,
            'amount': None,
            'property_label': '',
            'interest_rate_annual': None,
            'account_reference': '',
            'contact_info': 'Wendy',
            'notes': 'Terms and payment — update in admin.',
            'sort_order': 202,
        },
        {
            'title': 'Security Mortgage Loan 1 — #99706501',
            'event_type': T_LOAN,
            'due_date': date(2025, 6, 1),
            'end_date': date(2030, 6, 1),
            'amount': Decimal('1678.31'),
            'property_label': 'Commercial (Security)',
            'interest_rate_annual': Decimal('7.50'),
            'account_reference': '99706501',
            'contact_info': 'Security Mortgage / Servicing',
            'notes': 'Refi June 2025 at 7.5% for 5 years.',
            'sort_order': 210,
        },
        {
            'title': 'Security Loan 2 — remodel #99706502',
            'event_type': T_LOAN,
            'due_date': date(2025, 7, 18),
            'end_date': date(2027, 7, 18),
            'amount': Decimal('877.56'),
            'property_label': 'Commercial (Security)',
            'interest_rate_annual': Decimal('7.50'),
            'account_reference': '99706502',
            'contact_info': 'Security Mortgage',
            'notes': 'Refi 7/18/25 @ 7.5%; ~2-year payoff.',
            'sort_order': 211,
        },
        {
            'title': 'Security remodel loan — Kitchen #…6503',
            'event_type': T_LOAN,
            'due_date': date(2025, 7, 18),
            'end_date': date(2030, 7, 15),
            'amount': Decimal('483.00'),
            'property_label': 'Commercial (Security)',
            'interest_rate_annual': Decimal('7.50'),
            'account_reference': '…6503',
            'contact_info': 'Security Mortgage',
            'notes': 'Refi 7/18/25 @ 7.5% to 7/15/30.',
            'sort_order': 212,
        },
        {
            'title': 'Security Sprinkler Loan — x6504',
            'event_type': T_LOAN,
            'due_date': date(2023, 8, 1),
            'end_date': None,
            'amount': Decimal('740.34'),
            'property_label': 'Sprinkler',
            'interest_rate_annual': None,
            'account_reference': 'x6504',
            'contact_info': 'Security Mortgage',
            'notes': 'Original Aug 2023.',
            'sort_order': 213,
        },
        {
            'title': 'Bemidji City RLF — Spr sprinkler loan',
            'event_type': T_LOAN,
            'due_date': date(2023, 10, 18),
            'end_date': date(2043, 10, 18),
            'amount': Decimal('505.38'),
            'property_label': 'City RLF',
            'interest_rate_annual': Decimal('5.25'),
            'account_reference': '',
            'contact_info': 'City of Bemidji',
            'notes': (
                'Orig. 10/18/2023. Closing, attorney, filing fees; interest-only first two '
                'months (Nov & Dec 2023). 5.25% — 20 yr amortization.'
            ),
            'sort_order': 214,
        },
        # --- Utilities (avg of last 4 periods → typical monthly) ---
        {
            'title': 'MN Energy — 401 B Beltrami',
            'event_type': T_UTILITY,
            'due_date': date(2026, 1, 1),
            'end_date': None,
            'amount': _avg4('241.98', '235.05', '227.29', '145.11'),
            'property_label': '401 B Beltrami Ave.',
            'interest_rate_annual': None,
            'account_reference': '0619397773-00003',
            'contact_info': 'MN Energy',
            'notes': 'Avg of 4 recent bills (~$849.43 / 4 periods).',
            'sort_order': 310,
        },
        {
            'title': 'Otter Tail — 401 N space',
            'event_type': T_UTILITY,
            'due_date': date(2026, 1, 1),
            'end_date': None,
            'amount': Decimal('0'),
            'property_label': '401 N',
            'interest_rate_annual': None,
            'account_reference': '20001409',
            'contact_info': 'Otter Tail Energy',
            'notes': 'Per sheet $0 in sample — confirm usage/billing.',
            'sort_order': 311,
        },
        {
            'title': 'MN Energy — 207 4th St.',
            'event_type': T_UTILITY,
            'due_date': date(2026, 1, 1),
            'end_date': None,
            'amount': _avg4('109.25', '121.82', '128.09', '71.77'),
            'property_label': '207 4th St.',
            'interest_rate_annual': None,
            'account_reference': '0619397773-00001',
            'contact_info': 'MN Energy',
            'notes': 'Avg of 4 recent bills.',
            'sort_order': 312,
        },
        {
            'title': 'MN Energy — 211 4th St. NW',
            'event_type': T_UTILITY,
            'due_date': date(2026, 1, 1),
            'end_date': None,
            'amount': _avg4('207.98', '150.85', '160.60', '136.23'),
            'property_label': '211 4th St. NW',
            'interest_rate_annual': None,
            'account_reference': '0619397773-00002',
            'contact_info': 'MN Energy',
            'notes': 'Avg of 4 recent bills.',
            'sort_order': 313,
        },
        {
            'title': 'Otter Tail — 207 4th St.',
            'event_type': T_UTILITY,
            'due_date': date(2026, 1, 1),
            'end_date': None,
            'amount': _avg4('99.49', '116.10', '160.60', '136.23'),
            'property_label': '207 4th St.',
            'interest_rate_annual': None,
            'account_reference': '20000814',
            'contact_info': 'Otter Tail Energy',
            'notes': 'Avg of 4 periods on sheet.',
            'sort_order': 314,
        },
        {
            'title': 'Otter Tail — 211 4th St.',
            'event_type': T_UTILITY,
            'due_date': date(2026, 1, 1),
            'end_date': None,
            'amount': _avg4('47.89', '183.46', '64.03', '53.57'),
            'property_label': '211 4th St.',
            'interest_rate_annual': None,
            'account_reference': '20000816',
            'contact_info': 'Otter Tail Energy',
            'notes': 'Avg of 4 periods on sheet.',
            'sort_order': 315,
        },
        # --- Insurance & tax ---
        {
            'title': 'West Bend Mutual — building insurance',
            'event_type': T_INSURANCE,
            'due_date': date(2026, 1, 1),
            'end_date': None,
            'amount': Decimal('546.67'),
            'property_label': 'Portfolio',
            'interest_rate_annual': None,
            'account_reference': '',
            'contact_info': 'West Bend Mutual',
            'notes': '~$546.67/mo in sheet (×4 ≈ $2,186.68).',
            'sort_order': 410,
        },
        {
            'title': 'Property tax escrow / accrual',
            'event_type': T_TAX,
            'due_date': date(2026, 1, 1),
            'end_date': None,
            'amount': Decimal('883.00'),
            'property_label': 'Portfolio',
            'interest_rate_annual': None,
            'account_reference': '',
            'contact_info': '',
            'notes': '$883/mo per expense sheet.',
            'sort_order': 420,
        },
        # --- Bills & maintenance ---
        {
            'title': 'USPS — PO Box (annual)',
            'event_type': T_BILL,
            'due_date': date(2026, 1, 1),
            'end_date': None,
            'amount': None,
            'property_label': '',
            'interest_rate_annual': None,
            'account_reference': '',
            'contact_info': 'USPS',
            'notes': 'Annual rental; add dollar amount when renewed.',
            'sort_order': 510,
        },
        {
            'title': 'Security — loan closing fees',
            'event_type': T_BILL,
            'due_date': date(2025, 7, 1),
            'end_date': None,
            'amount': None,
            'property_label': 'Commercial',
            'interest_rate_annual': None,
            'account_reference': '',
            'contact_info': 'Security / closing agent',
            'notes': 'One-time fees around refi(s) — itemize when available.',
            'sort_order': 511,
        },
        {
            'title': 'Chase — card / operating',
            'event_type': T_BILL,
            'due_date': date(2026, 1, 1),
            'end_date': None,
            'amount': _avg4('188.63', '140.57', '147.38', '435.69'),
            'property_label': '',
            'interest_rate_annual': None,
            'account_reference': '',
            'contact_info': 'Chase',
            'notes': 'Avg of 4 periods on sheet (~$912.27 / 4).',
            'sort_order': 512,
        },
        {
            'title': 'Tax prep',
            'event_type': T_BILL,
            'due_date': date(2026, 3, 1),
            'end_date': None,
            'amount': Decimal('750.00'),
            'property_label': '',
            'interest_rate_annual': None,
            'account_reference': '',
            'contact_info': 'Preparer (add name)',
            'notes': 'Line item on sheet; may be annual — adjust timing in admin.',
            'sort_order': 513,
        },
        {
            'title': 'Snow plowing — Kurt Davis / Bobcat',
            'event_type': T_MAINT,
            'due_date': date(2026, 1, 1),
            'end_date': None,
            'amount': Decimal('130.00'),
            'property_label': '',
            'interest_rate_annual': None,
            'account_reference': '',
            'contact_info': 'Kurt Davis',
            'notes': 'Per sheet.',
            'sort_order': 520,
        },
        {
            'title': 'Bonded Lock and Key / sprinkler monitoring',
            'event_type': T_BILL,
            'due_date': date(2026, 1, 1),
            'end_date': None,
            'amount': Decimal('333.83'),
            'property_label': '',
            'interest_rate_annual': None,
            'account_reference': '',
            'contact_info': 'Bonded Lock and Key',
            'notes': 'Annual fee ~$333.83 on sheet.',
            'sort_order': 521,
        },
        {
            'title': 'MoeCo Fire Safety',
            'event_type': T_BILL,
            'due_date': date(2026, 1, 1),
            'end_date': None,
            'amount': Decimal('39.98'),
            'property_label': '',
            'interest_rate_annual': None,
            'account_reference': '',
            'contact_info': 'MoeCo Fire Safety',
            'notes': 'Line on expense sheet.',
            'sort_order': 522,
        },
        {
            'title': "Naylor's HVAC",
            'event_type': T_MAINT,
            'due_date': date(2026, 1, 1),
            'end_date': None,
            'amount': Decimal('89.67'),
            'property_label': '',
            'interest_rate_annual': None,
            'account_reference': '',
            'contact_info': "Naylor's HVAC",
            'notes': 'Maintenance line item.',
            'sort_order': 523,
        },
        {
            'title': 'Higgins Heating — Lennox (207 & 211)',
            'event_type': T_MAINT,
            'due_date': date(2026, 1, 1),
            'end_date': None,
            'amount': None,
            'property_label': '207 & 211 4th St.',
            'interest_rate_annual': None,
            'account_reference': '',
            'contact_info': 'Higgins Heating',
            'notes': 'Add amount / service schedule when billed.',
            'sort_order': 524,
        },
        {
            'title': 'Beltrami Co. Waste Management',
            'event_type': T_BILL,
            'due_date': date(2026, 1, 1),
            'end_date': None,
            'amount': None,
            'property_label': '',
            'interest_rate_annual': None,
            'account_reference': '',
            'contact_info': 'Beltrami County Waste',
            'notes': 'Add billing detail when available.',
            'sort_order': 525,
        },
        {
            'title': 'Sprinkler monitoring — annual (line item)',
            'event_type': T_BILL,
            'due_date': date(2026, 1, 1),
            'end_date': None,
            'amount': None,
            'property_label': '',
            'interest_rate_annual': None,
            'account_reference': '',
            'contact_info': '',
            'notes': 'Sheet references annual fee — may overlap Bonded Lock line; consolidate in admin.',
            'sort_order': 526,
        },
        {
            'title': 'Zetah Construction',
            'event_type': T_OTHER,
            'due_date': date(2026, 1, 1),
            'end_date': None,
            'amount': None,
            'property_label': '',
            'interest_rate_annual': None,
            'account_reference': '',
            'contact_info': 'Zetah Construction',
            'notes': 'Placeholder; no amounts on sheet — add projects here.',
            'sort_order': 527,
        },
        {
            'title': 'Lake n Woods Realty — Chris Hamilton',
            'event_type': T_OTHER,
            'due_date': date(2026, 1, 1),
            'end_date': None,
            'amount': None,
            'property_label': '',
            'interest_rate_annual': None,
            'account_reference': '',
            'contact_info': 'Chris Hamilton — Lake n Woods Realty',
            'notes': '$0 on sample sheet.',
            'sort_order': 528,
        },
    ]

    for spec in rows:
        clean = dict(spec)
        lookup = {
            'title': clean['title'],
            'event_type': clean['event_type'],
            'due_date': clean['due_date'],
        }
        defaults = {k: v for k, v in clean.items() if k not in lookup}
        BusinessCalendarEvent.objects.update_or_create(**lookup, defaults=defaults)

    BusinessKPIEntry.objects.update_or_create(
        label='Monthly loan payments (sheet total)',
        defaults={
            'value_display': '$4,831',
            'detail': (
                'Approx. total monthly loans from expense tracking. Detailed Security/City '
                'lines sum to ~$4,285/mo; sheet total higher — add NMWF / Eric / Wendy '
                'payments when finalized.'
            ),
            'period_hint': 'Per operations sheet',
            'is_active': True,
            'sort_order': 15,
        },
    )
    BusinessKPIEntry.objects.update_or_create(
        label='Utilities & energy (avg / mo)',
        defaults={
            'value_display': '~$699',
            'detail': (
                'Rough sum of avg monthly electric/gas lines (MN Energy + Otter Tail '
                'accounts, excl. zero 401 N line). Recalculate from admin if rates change.'
            ),
            'period_hint': 'From recent 4-period averages',
            'is_active': True,
            'sort_order': 16,
        },
    )
    BusinessKPIEntry.objects.update_or_create(
        label='Expense sheet reference total',
        defaults={
            'value_display': '$24,378',
            'detail': (
                'Grand total from pasted expense workbook for the tracked period. Use as '
                'benchmark; individual rows are seeded into calendar for reporting.'
            ),
            'period_hint': 'Imported reference',
            'is_active': True,
            'sort_order': 17,
        },
    )

    BusinessReportSection.objects.update_or_create(
        slug='accounting-loan-contacts',
        defaults={
            'title': 'Accounting, loan & municipal contacts',
            'body': (
                'Security commercial accounting: bank loan, tax-year interest and balances.\n'
                'Accounting / financial contacts at City of Bemidji (loan compliance, RLF, '
                'utility billing as applicable).'
            ),
            'source': 'manual',
            'is_active': True,
            'sort_order': 2,
        },
    )


def unseed(apps, schema_editor):
    BusinessCalendarEvent = apps.get_model('dream_blue', 'BusinessCalendarEvent')
    BusinessKPIEntry = apps.get_model('dream_blue', 'BusinessKPIEntry')
    BusinessReportSection = apps.get_model('dream_blue', 'BusinessReportSection')

    titles = [
        'NWMF loan — 0% (1 yr to Sept 2026)',
        'Eric loan (personal)',
        'Loans from Wendy — personal funds',
        'Security Mortgage Loan 1 — #99706501',
        'Security Loan 2 — remodel #99706502',
        'Security remodel loan — Kitchen #…6503',
        'Security Sprinkler Loan — x6504',
        'Bemidji City RLF — Spr sprinkler loan',
        'MN Energy — 401 B Beltrami',
        'Otter Tail — 401 N space',
        'MN Energy — 207 4th St.',
        'MN Energy — 211 4th St. NW',
        'Otter Tail — 207 4th St.',
        'Otter Tail — 211 4th St.',
        'West Bend Mutual — building insurance',
        'Property tax escrow / accrual',
        'USPS — PO Box (annual)',
        'Security — loan closing fees',
        'Chase — card / operating',
        'Tax prep',
        'Snow plowing — Kurt Davis / Bobcat',
        'Bonded Lock and Key / sprinkler monitoring',
        'MoeCo Fire Safety',
        "Naylor's HVAC",
        'Higgins Heating — Lennox (207 & 211)',
        'Beltrami Co. Waste Management',
        'Sprinkler monitoring — annual (line item)',
        'Zetah Construction',
        'Lake n Woods Realty — Chris Hamilton',
    ]
    BusinessCalendarEvent.objects.filter(title__in=titles).delete()
    BusinessKPIEntry.objects.filter(
        label__in=[
            'Monthly loan payments (sheet total)',
            'Utilities & energy (avg / mo)',
            'Expense sheet reference total',
        ]
    ).delete()
    BusinessReportSection.objects.filter(slug='accounting-loan-contacts').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('dream_blue', '0006_expense_detail_fields'),
    ]

    operations = [
        migrations.RunPython(seed, unseed),
    ]
