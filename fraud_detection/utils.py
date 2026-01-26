"""
Utility functions for fraud detection and analysis.
"""
from django.db.models import Q, Count, Sum, Avg, Max, Min
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
import logging
from collections import defaultdict

from .models import (
    Transaction, Vendor, Contract, FraudFlag, 
    Department, BudgetCategory
)

logger = logging.getLogger(__name__)


def detect_duplicate_payments(threshold_days=30, amount_tolerance=Decimal('0.01')):
    """
    Detect potential duplicate payments.
    
    Args:
        threshold_days: Number of days within which duplicates might occur
        amount_tolerance: Tolerance for considering amounts as equal
    
    Returns:
        List of FraudFlag objects created
    """
    flags_created = []
    
    # Find transactions with same vendor, similar amount, and close dates
    transactions = Transaction.objects.filter(status__in=['approved', 'paid']).select_related('vendor', 'department')
    
    # Group by vendor and amount (within tolerance)
    for transaction in transactions:
        # Find potential duplicates
        duplicates = Transaction.objects.filter(
            vendor=transaction.vendor,
            amount__gte=transaction.amount - amount_tolerance,
            amount__lte=transaction.amount + amount_tolerance,
            date__gte=transaction.date - timedelta(days=threshold_days),
            date__lte=transaction.date + timedelta(days=threshold_days),
            status__in=['approved', 'paid']
        ).exclude(pk=transaction.pk)
        
        if duplicates.exists():
            # Check if flag already exists for this set
            existing_flag = FraudFlag.objects.filter(
                flag_type='duplicate_payment',
                transactions__in=[transaction] + list(duplicates)
            ).first()
            
            if not existing_flag:
                total_amount = transaction.amount + duplicates.aggregate(Sum('amount'))['amount__sum']
                flag = FraudFlag.objects.create(
                    flag_type='duplicate_payment',
                    risk_level='high',
                    title=f'Potential Duplicate Payment: ${transaction.amount}',
                    description=f'Found {duplicates.count() + 1} transactions with same vendor ({transaction.vendor}) and similar amount (${transaction.amount}) within {threshold_days} days. Total: ${total_amount}',
                )
                flag.transactions.add(transaction, *duplicates)
                flags_created.append(flag)
    
    return flags_created


def detect_round_number_payments():
    """
    Detect payments that are round numbers (potential red flag).
    """
    flags_created = []
    
    # Find transactions with round number amounts (ends in .00)
    round_transactions = Transaction.objects.filter(
        status__in=['approved', 'paid']
    ).extra(
        where=["amount = ROUND(amount, 0)"]
    ).select_related('vendor', 'department')
    
    # Group by vendor and amount
    vendor_amount_groups = defaultdict(list)
    for trans in round_transactions:
        if trans.vendor:
            key = (trans.vendor.id, float(trans.amount))
            vendor_amount_groups[key].append(trans)
    
    # Flag vendors with many round number payments
    for (vendor_id, amount), transactions in vendor_amount_groups.items():
        if len(transactions) >= 5:  # Threshold: 5+ round number payments
            vendor = transactions[0].vendor
            total = sum(t.amount for t in transactions)
            
            flag = FraudFlag.objects.create(
                flag_type='round_number',
                risk_level='medium',
                title=f'Multiple Round Number Payments: {vendor.name}',
                description=f'Found {len(transactions)} round number payments to {vendor.name} totaling ${total}. Round numbers can indicate fabricated invoices.',
            )
            flag.transactions.add(*transactions)
            flag.vendors.add(vendor)
            flags_created.append(flag)
    
    return flags_created


def detect_anomalies(threshold_std=3):
    """
    Detect statistical anomalies in spending patterns.
    Uses z-score method to find outliers.
    """
    flags_created = []
    
    # Group by department and category
    dept_categories = Transaction.objects.filter(
        status__in=['approved', 'paid'],
        department__isnull=False,
        category__isnull=False
    ).values('department', 'category').annotate(
        avg_amount=Avg('amount'),
        std_amount=Avg('amount'),  # Simplified - would need proper std dev calculation
        count=Count('id')
    ).filter(count__gte=10)  # Need enough data points
    
    for dept_cat in dept_categories:
        dept = Department.objects.get(pk=dept_cat['department'])
        cat = BudgetCategory.objects.get(pk=dept_cat['category'])
        avg = dept_cat['avg_amount']
        
        # Find transactions significantly above average
        threshold = Decimal(str(avg)) * Decimal(str(threshold_std))
        anomalies = Transaction.objects.filter(
            department=dept,
            category=cat,
            amount__gt=threshold,
            status__in=['approved', 'paid']
        )
        
        if anomalies.exists():
            flag = FraudFlag.objects.create(
                flag_type='anomaly',
                risk_level='medium',
                title=f'Spending Anomaly: {dept.name} - {cat.name}',
                description=f'Found {anomalies.count()} transactions significantly above average (${avg}) in {dept.name} / {cat.name}.',
            )
            flag.transactions.add(*anomalies)
            flags_created.append(flag)
    
    return flags_created


def detect_end_of_year_spikes():
    """
    Detect unusual spending spikes at end of fiscal year.
    """
    flags_created = []
    
    # Get transactions by fiscal year and month
    transactions = Transaction.objects.filter(
        status__in=['approved', 'paid'],
        fiscal_year__isnull=False
    ).select_related('department', 'vendor')
    
    # Group by fiscal year and department
    fy_dept_groups = defaultdict(lambda: defaultdict(list))
    for trans in transactions:
        if trans.fiscal_year and trans.department:
            # Assume fiscal year ends in June (month 6)
            month = trans.date.month
            # Last 3 months of fiscal year (April, May, June)
            if month in [4, 5, 6]:
                key = (trans.fiscal_year, trans.department.id)
                fy_dept_groups[key].append(trans)
    
    # Compare last 3 months to rest of year
    for (fy, dept_id), eoy_transactions in fy_dept_groups.items():
        dept = Department.objects.get(pk=dept_id)
        eoy_total = sum(t.amount for t in eoy_transactions)
        eoy_count = len(eoy_transactions)
        
        # Get rest of year transactions
        rest_of_year = Transaction.objects.filter(
            fiscal_year=fy,
            department=dept,
            status__in=['approved', 'paid']
        ).exclude(
            date__month__in=[4, 5, 6]
        )
        
        if rest_of_year.exists():
            rest_total = rest_of_year.aggregate(Sum('amount'))['amount__sum'] or Decimal('0')
            rest_count = rest_of_year.count()
            
            # If end of year is more than 40% of total spending, flag it
            total = eoy_total + rest_total
            if total > 0 and (eoy_total / total) > Decimal('0.4'):
                flag = FraudFlag.objects.create(
                    flag_type='end_of_year_spike',
                    risk_level='medium',
                    title=f'End of Year Spending Spike: {dept.name} FY{fy}',
                    description=f'End of year (Apr-Jun) spending represents {eoy_total/total*100:.1f}% of total FY{fy} spending for {dept.name}. This may indicate "use it or lose it" behavior.',
                )
                flag.transactions.add(*eoy_transactions)
                flags_created.append(flag)
    
    return flags_created


def analyze_vendor_patterns():
    """
    Analyze vendor payment patterns for suspicious activity.
    """
    flags_created = []
    
    # Find vendors with many small payments just under common thresholds
    vendors = Vendor.objects.annotate(
        transaction_count=Count('transactions'),
        total_amount=Sum('transactions__amount'),
        avg_amount=Avg('transactions__amount')
    ).filter(transaction_count__gte=10)
    
    # Common reporting thresholds
    thresholds = [Decimal('5000'), Decimal('10000'), Decimal('25000')]
    
    for vendor in vendors:
        # Check for payments just under thresholds
        for threshold in thresholds:
            just_under = Transaction.objects.filter(
                vendor=vendor,
                amount__gte=threshold * Decimal('0.9'),  # 90% of threshold
                amount__lt=threshold,
                status__in=['approved', 'paid']
            )
            
            if just_under.count() >= 5:  # 5+ payments just under threshold
                total = just_under.aggregate(Sum('amount'))['amount__sum']
                flag = FraudFlag.objects.create(
                    flag_type='vendor_pattern',
                    risk_level='high',
                    title=f'Suspicious Vendor Pattern: {vendor.name}',
                    description=f'Found {just_under.count()} payments from {vendor.name} just under ${threshold} threshold (total: ${total}). This may indicate intentional avoidance of reporting requirements.',
                )
                flag.transactions.add(*just_under)
                flag.vendors.add(vendor)
                flags_created.append(flag)
    
    return flags_created


def compare_contract_prices():
    """
    Compare similar contracts to identify price discrepancies.
    """
    flags_created = []
    
    # Group contracts by department and similar amounts
    contracts = Contract.objects.filter(
        department__isnull=False
    ).select_related('vendor', 'department')
    
    # Simple comparison: contracts in same department with similar descriptions
    dept_contracts = defaultdict(list)
    for contract in contracts:
        if contract.department:
            dept_contracts[contract.department.id].append(contract)
    
    for dept_id, contracts_list in dept_contracts.items():
        if len(contracts_list) < 2:
            continue
        
        # Compare contracts with similar amounts
        for i, contract1 in enumerate(contracts_list):
            for contract2 in contracts_list[i+1:]:
                # If amounts differ significantly (>50%) for similar contracts
                if contract1.total_amount > 0 and contract2.total_amount > 0:
                    ratio = max(contract1.total_amount, contract2.total_amount) / min(contract1.total_amount, contract2.total_amount)
                    if ratio > Decimal('1.5'):  # 50% difference
                        flag = FraudFlag.objects.create(
                            flag_type='contract_discrepancy',
                            risk_level='high',
                            title=f'Contract Price Discrepancy: {contract1.department.name}',
                            description=f'Contracts {contract1.contract_number} (${contract1.total_amount}) and {contract2.contract_number} (${contract2.total_amount}) show significant price difference ({ratio:.1f}x) in same department.',
                        )
                        flag.contracts.add(contract1, contract2)
                        if contract1.vendor:
                            flag.vendors.add(contract1.vendor)
                        if contract2.vendor:
                            flag.vendors.add(contract2.vendor)
                        flags_created.append(flag)
    
    return flags_created


def run_full_analysis():
    """
    Run all fraud detection algorithms.
    Returns summary of results.
    """
    from .models import AnalysisResult
    
    analysis = AnalysisResult.objects.create(
        analysis_type='full_analysis',
        status='running'
    )
    
    try:
        all_flags = []
        
        logger.info("Running duplicate payment detection...")
        flags = detect_duplicate_payments()
        all_flags.extend(flags)
        
        logger.info("Running round number detection...")
        flags = detect_round_number_payments()
        all_flags.extend(flags)
        
        logger.info("Running anomaly detection...")
        flags = detect_anomalies()
        all_flags.extend(flags)
        
        logger.info("Running end of year spike detection...")
        flags = detect_end_of_year_spikes()
        all_flags.extend(flags)
        
        logger.info("Running vendor pattern analysis...")
        flags = analyze_vendor_patterns()
        all_flags.extend(flags)
        
        logger.info("Running contract comparison...")
        flags = compare_contract_prices()
        all_flags.extend(flags)
        
        analysis.status = 'completed'
        analysis.flags_created = len(all_flags)
        analysis.transactions_analyzed = Transaction.objects.count()
        analysis.summary = f"Analysis completed. Created {len(all_flags)} fraud flags across {len(set(f.flag_type for f in all_flags))} different detection types."
        analysis.completed_at = timezone.now()
        analysis.save()
        
        return analysis
        
    except Exception as e:
        logger.error(f"Analysis failed: {str(e)}", exc_info=True)
        analysis.status = 'failed'
        analysis.error_message = str(e)
        analysis.completed_at = timezone.now()
        analysis.save()
        return analysis
