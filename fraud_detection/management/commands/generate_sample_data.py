"""
Management command to generate synthetic data for fraud detection demo.
Creates vendors, departments, transactions, contracts, and budget records
with patterns that will trigger fraud detection algorithms.
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Avg
from decimal import Decimal
from datetime import datetime, timedelta
import random

from fraud_detection.models import (
    Vendor, Department, BudgetCategory, Transaction,
    Contract, BudgetRecord
)


class Command(BaseCommand):
    help = 'Generate synthetic data for fraud detection demo'

    def add_arguments(self, parser):
        parser.add_argument(
            '--transactions',
            type=int,
            default=500,
            help='Number of transactions to generate (default: 500)'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before generating'
        )

    def handle(self, *args, **options):
        num_transactions = options['transactions']
        clear_existing = options['clear']

        if clear_existing:
            self.stdout.write(self.style.WARNING('Clearing existing data...'))
            Transaction.objects.all().delete()
            Contract.objects.all().delete()
            BudgetRecord.objects.all().delete()
            Vendor.objects.all().delete()
            Department.objects.all().delete()
            BudgetCategory.objects.all().delete()

        self.stdout.write(self.style.SUCCESS('Generating synthetic data...'))

        # Create departments
        departments = self.create_departments()
        self.stdout.write(f'Created {len(departments)} departments')

        # Create budget categories
        categories = self.create_categories()
        self.stdout.write(f'Created {len(categories)} budget categories')

        # Create vendors
        vendors = self.create_vendors()
        self.stdout.write(f'Created {len(vendors)} vendors')

        # Create contracts
        contracts = self.create_contracts(vendors, departments)
        self.stdout.write(f'Created {len(contracts)} contracts')

        # Create budget records
        budget_records = self.create_budget_records(departments, categories)
        self.stdout.write(f'Created {len(budget_records)} budget records')

        # Create transactions with fraud patterns
        transactions = self.create_transactions(
            num_transactions, vendors, departments, categories
        )
        self.stdout.write(f'Created {len(transactions)} transactions')

        self.stdout.write(
            self.style.SUCCESS(
                f'\nSuccessfully generated demo data!\n'
                f'- {len(departments)} departments\n'
                f'- {len(categories)} categories\n'
                f'- {len(vendors)} vendors\n'
                f'- {len(contracts)} contracts\n'
                f'- {len(budget_records)} budget records\n'
                f'- {len(transactions)} transactions\n\n'
                f'Visit /apps/fraud-detection/ and run "Run Full Analysis" to see fraud detection in action!'
            )
        )

    def create_departments(self):
        """Create government departments."""
        dept_names = [
            'Public Works',
            'Finance',
            'IT Services',
            'Public Safety',
            'Health & Human Services',
            'Parks & Recreation',
            'Transportation',
            'Planning & Development',
            'Administration',
            'Legal Services',
        ]

        departments = []
        for name in dept_names:
            dept, created = Department.objects.get_or_create(
                name=name,
                defaults={'code': name.upper().replace(' ', '_')[:10]}
            )
            departments.append(dept)

        return departments

    def create_categories(self):
        """Create budget categories."""
        category_data = [
            ('Personnel', 'PERS'),
            ('Equipment', 'EQUIP'),
            ('Services', 'SERV'),
            ('Supplies', 'SUPP'),
            ('Contractual', 'CONT'),
            ('Utilities', 'UTIL'),
            ('Maintenance', 'MAINT'),
            ('Professional Services', 'PROF'),
        ]

        categories = []
        for name, code in category_data:
            cat, created = BudgetCategory.objects.get_or_create(
                name=name,
                defaults={'code': code}
            )
            categories.append(cat)

        return categories

    def create_vendors(self):
        """Create vendors with various patterns."""
        vendor_data = [
            # Normal vendors
            ('Acme Corporation', 'ACME-001', '123 Main St, City, ST 12345'),
            ('Global Services Inc', 'GSI-002', '456 Oak Ave, City, ST 12345'),
            ('Tech Solutions LLC', 'TECH-003', '789 Pine Rd, City, ST 12345'),
            ('City Supplies Co', 'CSC-004', '321 Elm St, City, ST 12345'),
            ('Professional Services Group', 'PSG-005', '654 Maple Dr, City, ST 12345'),
            
            # Suspicious vendors (will have patterns)
            ('Quick Pay Services', 'QPS-100', '999 Suspicious Ln, City, ST 12345'),  # Round numbers
            ('Just Under LLC', 'JUL-101', '888 Threshold Way, City, ST 12345'),  # Just under thresholds
            ('Duplicate Co', 'DUP-102', '777 Duplicate St, City, ST 12345'),  # Duplicate payments
            ('End Year Specialists', 'EYS-103', '666 Fiscal Blvd, City, ST 12345'),  # End of year spikes
            ('Anomaly Industries', 'ANI-104', '555 Outlier Ave, City, ST 12345'),  # Anomalies
        ]

        vendors = []
        for name, reg_num, address in vendor_data:
            vendor, created = Vendor.objects.get_or_create(
                name=name,
                defaults={
                    'registration_number': reg_num,
                    'address': address,
                    'contact_email': f'{name.lower().replace(" ", ".")}@example.com',
                    'contact_phone': f'555-{random.randint(100,999)}-{random.randint(1000,9999)}'
                }
            )
            vendors.append(vendor)

        return vendors

    def create_contracts(self, vendors, departments):
        """Create contracts with some price discrepancies."""
        contracts = []
        contract_counter = 1

        # Create normal contracts
        for i in range(15):
            vendor = random.choice(vendors)
            dept = random.choice(departments)
            start_date = timezone.now().date() - timedelta(days=random.randint(30, 365))
            
            contract, created = Contract.objects.get_or_create(
                contract_number=f'CONTRACT-{contract_counter:04d}',
                defaults={
                    'title': f'{vendor.name} - {dept.name} Services',
                    'vendor': vendor,
                    'department': dept,
                    'total_amount': Decimal(random.randint(10000, 100000)),
                    'start_date': start_date,
                    'end_date': start_date + timedelta(days=365),
                    'description': f'Service contract between {vendor.name} and {dept.name}'
                }
            )
            contracts.append(contract)
            contract_counter += 1

        # Create contracts with price discrepancies (same department, similar services, different prices)
        dept = random.choice(departments)
        vendor1 = vendors[0]
        vendor2 = vendors[1]
        
        contract1, _ = Contract.objects.get_or_create(
            contract_number=f'CONTRACT-{contract_counter:04d}',
            defaults={
                'title': f'{vendor1.name} - {dept.name} Consulting',
                'vendor': vendor1,
                'department': dept,
                'total_amount': Decimal('50000'),
                'start_date': timezone.now().date() - timedelta(days=180),
                'end_date': timezone.now().date() + timedelta(days=185),
                'description': f'Consulting services for {dept.name}'
            }
        )
        contracts.append(contract1)
        contract_counter += 1

        contract2, _ = Contract.objects.get_or_create(
            contract_number=f'CONTRACT-{contract_counter:04d}',
            defaults={
                'title': f'{vendor2.name} - {dept.name} Consulting',
                'vendor': vendor2,
                'department': dept,
                'total_amount': Decimal('125000'),  # 2.5x the price - will trigger discrepancy detection
                'start_date': timezone.now().date() - timedelta(days=180),
                'end_date': timezone.now().date() + timedelta(days=185),
                'description': f'Consulting services for {dept.name}'
            }
        )
        contracts.append(contract2)

        return contracts

    def create_budget_records(self, departments, categories):
        """Create budget allocation records."""
        budget_records = []
        fiscal_year = 2024

        for dept in departments:
            for category in categories:
                # Skip some combinations to make it realistic
                if random.random() > 0.6:
                    continue

                budget, created = BudgetRecord.objects.get_or_create(
                    department=dept,
                    category=category,
                    fiscal_year=fiscal_year,
                    defaults={
                        'allocated_amount': Decimal(random.randint(50000, 500000)),
                        'description': f'FY{fiscal_year} budget for {category.name} in {dept.name}'
                    }
                )
                budget_records.append(budget)

        return budget_records

    def create_transactions(self, num_transactions, vendors, departments, categories):
        """Create transactions with various fraud patterns."""
        transactions = []
        transaction_counter = 1
        base_date = timezone.now().date() - timedelta(days=365)
        fiscal_year = 2024

        # Get suspicious vendors
        suspicious_vendors = {
            'round_numbers': Vendor.objects.get(name='Quick Pay Services'),
            'just_under': Vendor.objects.get(name='Just Under LLC'),
            'duplicate': Vendor.objects.get(name='Duplicate Co'),
            'end_year': Vendor.objects.get(name='End Year Specialists'),
            'anomaly': Vendor.objects.get(name='Anomaly Industries'),
        }

        # Create normal transactions (70% of total)
        normal_count = int(num_transactions * 0.7)
        for i in range(normal_count):
            date = base_date + timedelta(days=random.randint(0, 365))
            vendor = random.choice(vendors)
            dept = random.choice(departments)
            category = random.choice(categories)
            
            # Normal transaction amounts
            amount = Decimal(random.randint(100, 10000) + random.random() * 100).quantize(Decimal('0.01'))
            
            transaction = Transaction.objects.create(
                transaction_id=f'TXN{transaction_counter:06d}',
                date=date,
                amount=amount,
                description=f'Payment to {vendor.name} for {category.name}',
                vendor=vendor,
                department=dept,
                category=category,
                fiscal_year=fiscal_year if date.year == 2024 else 2023,
                invoice_number=f'INV-{random.randint(1000, 9999)}',
                status=random.choice(['approved', 'paid']),
            )
            transactions.append(transaction)
            transaction_counter += 1

        # Create round number transactions (10%)
        round_count = int(num_transactions * 0.1)
        for i in range(round_count):
            date = base_date + timedelta(days=random.randint(0, 365))
            vendor = suspicious_vendors['round_numbers']
            dept = random.choice(departments)
            category = random.choice(categories)
            
            # Round number amounts (will trigger detection)
            round_amounts = [1000, 2000, 3000, 5000, 10000, 15000, 20000, 25000]
            amount = Decimal(random.choice(round_amounts))
            
            transaction = Transaction.objects.create(
                transaction_id=f'TXN{transaction_counter:06d}',
                date=date,
                amount=amount,
                description=f'Payment to {vendor.name} for {category.name}',
                vendor=vendor,
                department=dept,
                category=category,
                fiscal_year=fiscal_year if date.year == 2024 else 2023,
                invoice_number=f'INV-{random.randint(1000, 9999)}',
                status=random.choice(['approved', 'paid']),
            )
            transactions.append(transaction)
            transaction_counter += 1

        # Create transactions just under thresholds (5%)
        threshold_count = int(num_transactions * 0.05)
        for i in range(threshold_count):
            date = base_date + timedelta(days=random.randint(0, 365))
            vendor = suspicious_vendors['just_under']
            dept = random.choice(departments)
            category = random.choice(categories)
            
            # Just under common thresholds (90% of threshold)
            thresholds = [5000, 10000, 25000]
            threshold = random.choice(thresholds)
            amount = Decimal(threshold * 0.9).quantize(Decimal('0.01'))
            
            transaction = Transaction.objects.create(
                transaction_id=f'TXN{transaction_counter:06d}',
                date=date,
                amount=amount,
                description=f'Payment to {vendor.name} for {category.name}',
                vendor=vendor,
                department=dept,
                category=category,
                fiscal_year=fiscal_year if date.year == 2024 else 2023,
                invoice_number=f'INV-{random.randint(1000, 9999)}',
                status=random.choice(['approved', 'paid']),
            )
            transactions.append(transaction)
            transaction_counter += 1

        # Create duplicate payments (5%)
        duplicate_count = int(num_transactions * 0.05)
        duplicate_amounts = [Decimal('5000.00'), Decimal('7500.00'), Decimal('10000.00')]
        
        for i in range(duplicate_count):
            base_trans_date = base_date + timedelta(days=random.randint(0, 300))
            vendor = suspicious_vendors['duplicate']
            dept = random.choice(departments)
            category = random.choice(categories)
            amount = random.choice(duplicate_amounts)
            
            # Create first transaction
            transaction1 = Transaction.objects.create(
                transaction_id=f'TXN{transaction_counter:06d}',
                date=base_trans_date,
                amount=amount,
                description=f'Payment to {vendor.name} for {category.name}',
                vendor=vendor,
                department=dept,
                category=category,
                fiscal_year=fiscal_year if base_trans_date.year == 2024 else 2023,
                invoice_number=f'INV-{random.randint(1000, 9999)}',
                status=random.choice(['approved', 'paid']),
            )
            transactions.append(transaction1)
            transaction_counter += 1

            # Create duplicate within 30 days
            duplicate_date = base_trans_date + timedelta(days=random.randint(1, 30))
            transaction2 = Transaction.objects.create(
                transaction_id=f'TXN{transaction_counter:06d}',
                date=duplicate_date,
                amount=amount,  # Same amount
                description=f'Payment to {vendor.name} for {category.name}',
                vendor=vendor,  # Same vendor
                department=dept,
                category=category,
                fiscal_year=fiscal_year if duplicate_date.year == 2024 else 2023,
                invoice_number=f'INV-{random.randint(1000, 9999)}',
                status=random.choice(['approved', 'paid']),
            )
            transactions.append(transaction2)
            transaction_counter += 1

        # Create end of year spike transactions (5%)
        eoy_count = int(num_transactions * 0.05)
        # End of fiscal year is June (months 4, 5, 6)
        eoy_months = [4, 5, 6]
        
        for i in range(eoy_count):
            # Random day in April, May, or June
            month = random.choice(eoy_months)
            day = random.randint(1, 28)
            date = datetime(2024, month, day).date()
            
            vendor = suspicious_vendors['end_year']
            dept = random.choice(departments)
            category = random.choice(categories)
            amount = Decimal(random.randint(5000, 50000) + random.random() * 100).quantize(Decimal('0.01'))
            
            transaction = Transaction.objects.create(
                transaction_id=f'TXN{transaction_counter:06d}',
                date=date,
                amount=amount,
                description=f'End of year payment to {vendor.name} for {category.name}',
                vendor=vendor,
                department=dept,
                category=category,
                fiscal_year=2024,
                invoice_number=f'INV-{random.randint(1000, 9999)}',
                status=random.choice(['approved', 'paid']),
            )
            transactions.append(transaction)
            transaction_counter += 1

        # Create anomaly transactions (5%)
        # These should be created after normal transactions to have averages to compare against
        anomaly_count = int(num_transactions * 0.05)
        
        for i in range(anomaly_count):
            date = base_date + timedelta(days=random.randint(0, 365))
            vendor = suspicious_vendors['anomaly']
            dept = random.choice(departments)
            category = random.choice(categories)
            
            # Get average for this dept/category combination from existing transactions
            avg_trans = Transaction.objects.filter(
                department=dept, category=category
            ).aggregate(avg=Avg('amount'))['avg']
            
            if avg_trans:
                # Create transaction significantly above average (5x)
                base_amount = Decimal(str(avg_trans))
                amount = base_amount * Decimal('5')  # 5x average - will trigger anomaly detection
            else:
                # Very large amount if no average exists yet
                amount = Decimal(random.randint(50000, 100000))
            
            transaction = Transaction.objects.create(
                transaction_id=f'TXN{transaction_counter:06d}',
                date=date,
                amount=amount,
                description=f'Large payment to {vendor.name} for {category.name}',
                vendor=vendor,
                department=dept,
                category=category,
                fiscal_year=fiscal_year if date.year == 2024 else 2023,
                invoice_number=f'INV-{random.randint(1000, 9999)}',
                status=random.choice(['approved', 'paid']),
            )
            transactions.append(transaction)
            transaction_counter += 1

        return transactions
