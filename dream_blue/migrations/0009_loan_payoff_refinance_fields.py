# Loan detail fields + Security / City / NMF / Wendy rows from owner-provided statements.

from datetime import date
from decimal import Decimal

from django.db import migrations, models


def apply_loan_updates(apps, schema_editor):
    Event = apps.get_model('dream_blue', 'BusinessCalendarEvent')
    Event.objects.filter(title='Eric loan (personal)').delete()

    D = Decimal
    blocks = [
        {
            'match': {'title': 'Security Mortgage Loan 1 — #99706501', 'event_type': 'loan'},
            'set': {
                'title': 'Loan xx6501 — Mortgage (401 Beltrami Ave)',
                'property_label': '401 Beltrami Ave — Security Bank USA',
                'due_date': date(2012, 5, 3),
                'end_date': None,
                'amount': D('1678.31'),
                'interest_rate_annual': D('7.50'),
                'account_reference': 'xx6501',
                'contact_info': 'Security Bank USA',
                'refinance_date': date(2025, 4, 24),
                'payoff_target_date': date(2026, 3, 31),
                'payoff_balance': D('99457.00'),
                'payoff_balance_as_of': date(2026, 3, 31),
                'original_principal': D('240000.00'),
                'notes': (
                    'Opened 5/3/2012; original principal $240,000. Refinanced 4/24/2025 at 7.50% ITR; '
                    'closing fees $578.90. Interest paid 2025: $6,927.77. Payoff amount shown is for '
                    '3/31/2026 per lender ($99,457).'
                ),
            },
        },
        {
            'match': {'title': 'Security Loan 2 — remodel #99706502', 'event_type': 'loan'},
            'set': {
                'title': 'Loan xx6502 — Building remodel (Security Bank USA)',
                'property_label': '401 Beltrami Ave — Security Bank USA',
                'due_date': date(2012, 8, 17),
                'end_date': date(2027, 8, 20),
                'amount': D('877.56'),
                'interest_rate_annual': D('7.50'),
                'account_reference': 'xx6502',
                'contact_info': 'Security Bank USA',
                'refinance_date': date(2025, 8, 15),
                'payoff_target_date': date(2026, 3, 31),
                'payoff_balance': D('14139.73'),
                'payoff_balance_as_of': date(2026, 3, 31),
                'original_principal': D('120000.00'),
                'notes': (
                    'Opened 8/17/2012; original $120,000. Refinanced 8/15/2025 at 7.50%; closing fees '
                    '$183.61. Payment $877.56/mo. Interest paid 2025: $1,161.91. Payoff 3/31/2026: '
                    '$14,139.73. Maturity 8/20/2027.'
                ),
            },
        },
        {
            'match': {'title': 'Security remodel loan — Kitchen #…6503', 'event_type': 'loan'},
            'set': {
                'title': 'Loan xx6503 — Kitchen installation remodel (Security Bank USA)',
                'property_label': '401 Beltrami Ave — Security Bank USA',
                'due_date': date(2016, 7, 21),
                'end_date': date(2030, 7, 15),
                'amount': D('483.00'),
                'interest_rate_annual': D('7.50'),
                'account_reference': 'xx6503',
                'contact_info': 'Security Bank USA',
                'refinance_date': date(2025, 7, 18),
                'payoff_target_date': date(2026, 3, 31),
                'payoff_balance': D('20853.82'),
                'payoff_balance_as_of': date(2026, 3, 31),
                'original_principal': D('50000.00'),
                'notes': (
                    'Opened 7/21/2016; original $50,000. Refinanced 7/18/2025 at 7.50%; closing fees '
                    '$408.43. Payment $483/mo. Interest paid 2025: $1,376.77. Payoff 3/31/2026: '
                    '$20,853.82. Maturity 7/15/2030.'
                ),
            },
        },
        {
            'match': {'title': 'Security Sprinkler Loan — x6504', 'event_type': 'loan'},
            'set': {
                'title': 'Loan xx6504 — Fire suppression sprinkler (Security Bank USA)',
                'property_label': '401 Beltrami Ave — Security Bank USA',
                'due_date': date(2023, 8, 8),
                'end_date': date(2028, 8, 15),
                'amount': D('740.34'),
                'interest_rate_annual': D('7.50'),
                'account_reference': 'xx6504',
                'contact_info': 'Security Bank USA',
                'refinance_date': None,
                'payoff_target_date': date(2026, 3, 31),
                'payoff_balance': D('94488.00'),
                'payoff_balance_as_of': date(2026, 3, 31),
                'original_principal': D('91000.00'),
                'notes': (
                    'Opened 8/8/2023; original $91,000 at 7.50% ITR. Next payment $740.34/mo. '
                    'Interest paid 2025: $6,629.66. Payoff 3/31/2026: $94,488. Maturity 8/15/2028.'
                ),
            },
        },
        {
            'match': {'title': 'Bemidji City RLF — Spr sprinkler loan', 'event_type': 'loan'},
            'set': {
                'title': 'City of Bemidji RLF — Fire sprinkler installation loan',
                'property_label': 'City of Bemidji Revolving Loan Fund',
                'due_date': date(2023, 10, 18),
                'end_date': date(2043, 10, 18),
                'amount': D('505.38'),
                'interest_rate_annual': D('5.25'),
                'account_reference': 'Bemidji RLF',
                'contact_info': 'City of Bemidji RLF',
                'refinance_date': None,
                'payoff_target_date': date(2025, 12, 31),
                'payoff_balance': D('70524.81'),
                'payoff_balance_as_of': date(2025, 12, 31),
                'original_principal': D('75000.00'),
                'notes': (
                    'Opened 10/18/2023; original $75,000 @ 5.25%. Interest paid 2025: $3,768.36. '
                    'Payoff balance as of 12/31/2025: $70,524.81.'
                ),
            },
        },
        {
            'match': {'title': 'NWMF loan — 0% (1 yr to Sept 2026)', 'event_type': 'loan'},
            'set': {
                'title': 'Northwest Minnesota Foundation — $10k (0% to Sept 2026)',
                'property_label': 'Portfolio — June 2025 storm damage',
                'due_date': date(2025, 9, 1),
                'end_date': date(2026, 9, 30),
                'amount': None,
                'interest_rate_annual': D('0.00'),
                'account_reference': 'NWMF',
                'contact_info': 'Northwest Minnesota Foundation',
                'refinance_date': None,
                'payoff_target_date': date(2026, 9, 30),
                'payoff_balance': None,
                'payoff_balance_as_of': None,
                'original_principal': D('10000.00'),
                'notes': (
                    'Received Sept 2025: $10,000 at 0% for one year until Sept 2026 for June 2025 '
                    'storm damage expenses.'
                ),
            },
        },
        {
            'match': {'title': 'Loans from Wendy — personal funds', 'event_type': 'loan'},
            'set': {
                'title': 'Wendy — personal loan ($5,000)',
                'property_label': 'June 2025 storm damage',
                'due_date': date(2025, 6, 1),
                'end_date': None,
                'amount': None,
                'interest_rate_annual': None,
                'account_reference': '',
                'contact_info': 'Wendy',
                'refinance_date': None,
                'payoff_target_date': None,
                'payoff_balance': None,
                'payoff_balance_as_of': None,
                'original_principal': D('5000.00'),
                'notes': '$5,000 in 2025 to cover June 2025 storm damage; document repayment terms in admin.',
            },
        },
    ]
    for block in blocks:
        qs = Event.objects.filter(**block['match'])
        n = qs.update(**block['set'])
        if not n:
            # Title may have been edited in admin; skip silently.
            continue


class Migration(migrations.Migration):
    dependencies = [
        ('dream_blue', '0008_lease_comp_research_run'),
    ]

    operations = [
        migrations.AddField(
            model_name='businesscalendarevent',
            name='original_principal',
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                help_text='Original loan amount at opening (loans)',
                max_digits=14,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name='businesscalendarevent',
            name='payoff_balance',
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                help_text='Principal payoff / balance for the as-of date below',
                max_digits=14,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name='businesscalendarevent',
            name='payoff_balance_as_of',
            field=models.DateField(
                blank=True,
                help_text='Date the payoff_balance figure applies to',
                null=True,
            ),
        ),
        migrations.AddField(
            model_name='businesscalendarevent',
            name='payoff_target_date',
            field=models.DateField(
                blank=True,
                db_index=True,
                help_text='Show on calendar (e.g. payoff quote target date)',
                null=True,
            ),
        ),
        migrations.AddField(
            model_name='businesscalendarevent',
            name='refinance_date',
            field=models.DateField(
                blank=True,
                db_index=True,
                help_text='Last refinance closing date — shown on calendar',
                null=True,
            ),
        ),
        migrations.RunPython(apply_loan_updates, migrations.RunPython.noop),
    ]
