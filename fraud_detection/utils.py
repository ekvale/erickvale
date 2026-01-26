"""
Utility functions for fraud detection and analysis.
"""
from django.db.models import Q, Count, Sum, Avg, Max, Min
from django.utils import timezone
from datetime import timedelta, datetime
from decimal import Decimal
import logging
import random
import numpy as np
import pandas as pd
from collections import defaultdict

from .models import (
    Transaction, Vendor, Contract, FraudFlag, 
    Department, BudgetCategory, RiskScore, Audit, HumanIntervention
)

logger = logging.getLogger(__name__)

# Try to import ML libraries (optional)
try:
    from pyod.models.ecod import ECOD
    from pyod.models.isolation_forest import IForest
    PYOD_AVAILABLE = True
except ImportError:
    PYOD_AVAILABLE = False
    logger.warning("PyOD not available. Install with: pip install pyod")

try:
    import xgboost as xgb
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False
    logger.warning("XGBoost not available. Install with: pip install xgboost")


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
        
        # Calculate ML risk scores
        logger.info("Calculating ML risk scores...")
        all_transactions = Transaction.objects.all()
        if all_transactions.exists():
            calculate_risk_scores(all_transactions)
        
        analysis.status = 'completed'
        analysis.flags_created = len(all_flags)
        analysis.transactions_analyzed = Transaction.objects.count()
        analysis.summary = f"Analysis completed. Created {len(all_flags)} fraud flags across {len(set(f.flag_type for f in all_flags))} different detection types. Calculated risk scores for all transactions."
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


def extract_features_for_ml(transactions):
    """
    Extract features from transactions for ML models.
    Returns a pandas DataFrame with features.
    """
    features = []
    
    for trans in transactions.select_related('vendor', 'department', 'category'):
        # Basic features
        feature_dict = {
            'amount': float(trans.amount),
            'fiscal_year': trans.fiscal_year or 0,
            'has_vendor': 1 if trans.vendor else 0,
            'has_department': 1 if trans.department else 0,
            'has_category': 1 if trans.category else 0,
        }
        
        # Temporal features
        if trans.date:
            feature_dict.update({
                'day_of_week': trans.date.weekday(),
                'day_of_month': trans.date.day,
                'month': trans.date.month,
                'is_weekend': 1 if trans.date.weekday() >= 5 else 0,
                'is_month_end': 1 if trans.date.day >= 25 else 0,
                'is_fiscal_year_end': 1 if trans.date.month in [4, 5, 6] else 0,
            })
        
        # Vendor features
        if trans.vendor:
            vendor_trans = Transaction.objects.filter(vendor=trans.vendor)
            vendor_stats = vendor_trans.aggregate(
                avg_amount=Avg('amount'),
                count=Count('id')
            )
            feature_dict.update({
                'vendor_avg_amount': float(vendor_stats['avg_amount'] or 0),
                'vendor_transaction_count': vendor_stats['count'] or 0,
            })
            
            # Check for round numbers
            if trans.amount == trans.amount.quantize(Decimal('1')):
                feature_dict['is_round_number'] = 1
            else:
                feature_dict['is_round_number'] = 0
        
        # Department features
        if trans.department:
            dept_trans = Transaction.objects.filter(department=trans.department)
            dept_stats = dept_trans.aggregate(
                avg_amount=Avg('amount'),
                count=Count('id')
            )
            feature_dict.update({
                'dept_avg_amount': float(dept_stats['avg_amount'] or 0),
                'dept_transaction_count': dept_stats['count'] or 0,
            })
        
        features.append(feature_dict)
    
    if not features:
        return pd.DataFrame()
    
    return pd.DataFrame(features)


def calculate_risk_scores_pyod(transactions):
    """
    Calculate anomaly scores using PyOD.
    Returns dictionary mapping transaction IDs to scores.
    """
    if not PYOD_AVAILABLE:
        logger.warning("PyOD not available, skipping anomaly detection")
        return {}
    
    try:
        # Extract features
        features_df = extract_features_for_ml(transactions)
        if features_df.empty:
            return {}
        
        # Fill NaN values
        features_df = features_df.fillna(0)
        
        # Use ECOD (Empirical-CDF-based Outlier Detection)
        detector = ECOD(contamination=0.1)
        detector.fit(features_df.values)
        scores = detector.decision_scores_
        
        # Map scores to transactions
        score_dict = {}
        for idx, trans in enumerate(transactions):
            score_dict[trans.id] = float(scores[idx]) if idx < len(scores) else 0.0
        
        return score_dict
    except Exception as e:
        logger.error(f"PyOD anomaly detection failed: {str(e)}", exc_info=True)
        return {}


def calculate_risk_scores_xgboost(transactions):
    """
    Calculate fraud probability scores using XGBoost.
    This is a simplified version - in production, you'd train on historical fraud flags.
    """
    if not XGBOOST_AVAILABLE:
        logger.warning("XGBoost not available, skipping ML scoring")
        return {}
    
    try:
        # Extract features
        features_df = extract_features_for_ml(transactions)
        if features_df.empty:
            return {}
        
        # Fill NaN values
        features_df = features_df.fillna(0)
        
        # For now, use a simple heuristic-based model
        # In production, load a trained XGBoost model
        # model = xgb.Booster()
        # model.load_model('fraud_model.json')
        # predictions = model.predict(xgb.DMatrix(features_df))
        
        # Simple heuristic: combine multiple risk factors
        scores = {}
        for idx, trans in enumerate(transactions):
            score = 0.0
            
            # Round numbers increase risk
            if trans.amount == trans.amount.quantize(Decimal('1')):
                score += 0.2
            
            # Large amounts increase risk
            if trans.amount > Decimal('10000'):
                score += 0.3
            
            # End of fiscal year increases risk
            if trans.date and trans.date.month in [4, 5, 6]:
                score += 0.2
            
            # Vendor with many transactions might be suspicious
            if trans.vendor:
                vendor_count = Transaction.objects.filter(vendor=trans.vendor).count()
                if vendor_count > 50:
                    score += 0.1
            
            # Check if transaction has fraud flags
            if trans.fraud_flags.exists():
                score += 0.3
            
            scores[trans.id] = min(score, 1.0)  # Cap at 1.0
        
        return scores
    except Exception as e:
        logger.error(f"XGBoost scoring failed: {str(e)}", exc_info=True)
        return {}


def calculate_risk_scores(transactions):
    """
    Calculate risk scores for transactions using ML models.
    Creates or updates RiskScore objects.
    """
    if not transactions.exists():
        return
    
    logger.info(f"Calculating risk scores for {transactions.count()} transactions")
    
    # Calculate PyOD scores
    pyod_scores = calculate_risk_scores_pyod(transactions)
    
    # Calculate XGBoost scores
    xgb_scores = calculate_risk_scores_xgboost(transactions)
    
    # Create/update RiskScore objects
    for trans in transactions:
        pyod_score = pyod_scores.get(trans.id, None)
        xgb_score = xgb_scores.get(trans.id, None)
        
        # Calculate ensemble score (weighted average)
        ensemble_score = None
        if pyod_score is not None and xgb_score is not None:
            # Normalize PyOD score (typically 0-100, convert to 0-1)
            normalized_pyod = min(pyod_score / 100.0, 1.0) if pyod_score > 0 else 0.0
            ensemble_score = Decimal(str(0.4 * normalized_pyod + 0.6 * xgb_score))
        elif xgb_score is not None:
            ensemble_score = Decimal(str(xgb_score))
        elif pyod_score is not None:
            normalized_pyod = min(pyod_score / 100.0, 1.0) if pyod_score > 0 else 0.0
            ensemble_score = Decimal(str(normalized_pyod))
        
        # Determine risk level
        if ensemble_score:
            if ensemble_score >= Decimal('0.8'):
                risk_level = 'critical'
            elif ensemble_score >= Decimal('0.6'):
                risk_level = 'high'
            elif ensemble_score >= Decimal('0.4'):
                risk_level = 'medium'
            else:
                risk_level = 'low'
        else:
            risk_level = 'low'
        
        # Create or update RiskScore
        risk_score, created = RiskScore.objects.get_or_create(
            transaction=trans,
            defaults={
                'pyod_anomaly_score': Decimal(str(pyod_score)) if pyod_score is not None else None,
                'xgboost_score': Decimal(str(xgb_score)) if xgb_score is not None else None,
                'ensemble_score': ensemble_score,
                'risk_level': risk_level,
                'model_version': 'v1.0',
            }
        )
        
        if not created:
            risk_score.pyod_anomaly_score = Decimal(str(pyod_score)) if pyod_score is not None else None
            risk_score.xgboost_score = Decimal(str(xgb_score)) if xgb_score is not None else None
            risk_score.ensemble_score = ensemble_score
            risk_score.risk_level = risk_level
            risk_score.save()


def generate_automated_audits(risk_threshold=0.6, random_percentage=5, user=None):
    """
    Generate automated randomized audits based on risk scores.
    
    Args:
        risk_threshold: Minimum risk score for risk-based audits
        random_percentage: Percentage of transactions to randomly audit
        user: User creating the audits
    
    Returns:
        List of Audit objects created
    """
    audits_created = []
    
    # Risk-based audits
    high_risk_transactions = Transaction.objects.filter(
        risk_score__ensemble_score__gte=risk_threshold
    ).select_related('vendor', 'department')
    
    if high_risk_transactions.exists():
        # Group by vendor for vendor audits
        vendors_with_high_risk = Vendor.objects.filter(
            transactions__risk_score__ensemble_score__gte=risk_threshold
        ).distinct()
        
        for vendor in vendors_with_high_risk[:5]:  # Top 5 vendors
            vendor_trans = high_risk_transactions.filter(vendor=vendor)
            
            audit = Audit.objects.create(
                audit_type='risk_based',
                title=f'Risk-Based Audit: {vendor.name}',
                description=f'Automated audit triggered for {vendor.name} due to high-risk transactions. '
                           f'Found {vendor_trans.count()} high-risk transactions.',
                risk_threshold=risk_threshold,
                assigned_to=user,
                created_by=user,
                scheduled_date=timezone.now().date(),
                due_date=(timezone.now() + timedelta(days=30)).date(),
            )
            audit.vendors.add(vendor)
            audit.transactions.set(vendor_trans[:20])  # Limit to 20 transactions
            audits_created.append(audit)
    
    # Random audits
    all_transactions = Transaction.objects.all()
    if all_transactions.exists():
        num_random = max(1, int(all_transactions.count() * random_percentage / 100))
        random_transactions = random.sample(list(all_transactions), min(num_random, all_transactions.count()))
        
        if random_transactions:
            # Group by department
            departments = Department.objects.filter(
                transactions__in=random_transactions
            ).distinct()
            
            for dept in departments[:3]:  # Top 3 departments
                dept_trans = [t for t in random_transactions if t.department == dept]
                
                if dept_trans:
                    audit = Audit.objects.create(
                        audit_type='random',
                        title=f'Random Audit: {dept.name}',
                        description=f'Randomly selected audit for {dept.name}. '
                                   f'Selected {len(dept_trans)} transactions for review.',
                        random_percentage=random_percentage,
                        assigned_to=user,
                        created_by=user,
                        scheduled_date=timezone.now().date(),
                        due_date=(timezone.now() + timedelta(days=30)).date(),
                    )
                    audit.departments.add(dept)
                    audit.transactions.set(dept_trans[:15])  # Limit to 15 transactions
                    audits_created.append(audit)
    
    # Create interventions for high-risk transactions
    high_risk = Transaction.objects.filter(
        risk_score__ensemble_score__gte=risk_threshold
    ).exclude(interventions__status__in=['resolved', 'approved'])
    
    interventions_created = 0
    for trans in high_risk[:20]:  # Limit to 20 to avoid overwhelming
        intervention = create_intervention_for_high_risk(trans, user)
        if intervention:
            interventions_created += 1
    
    logger.info(f"Created {len(audits_created)} automated audits and {interventions_created} interventions")
    return audits_created


def create_intervention_for_high_risk(transaction, user=None):
    """
    Create human intervention workflow for high-risk transactions.
    """
    if not transaction.risk_score or not transaction.risk_score.ensemble_score:
        return None
    
    risk_score = transaction.risk_score.ensemble_score
    
    # Determine intervention type based on risk
    if risk_score >= Decimal('0.8'):
        intervention_type = 'escalation'
        priority = 'urgent'
        action_required = 'Immediate review required. Transaction flagged as critical risk.'
    elif risk_score >= Decimal('0.6'):
        intervention_type = 'review'
        priority = 'high'
        action_required = 'Review transaction details and verify legitimacy.'
    else:
        return None  # Only create interventions for high-risk
    
    intervention = HumanIntervention.objects.create(
        intervention_type=intervention_type,
        priority=priority,
        transaction=transaction,
        title=f'High-Risk Transaction Review: {transaction.transaction_id}',
        description=f'Transaction {transaction.transaction_id} has a risk score of {risk_score:.2%}. '
                   f'Amount: ${transaction.amount}, Vendor: {transaction.vendor.name if transaction.vendor else "N/A"}',
        action_required=action_required,
        assigned_to=user,
        created_by=user,
        due_date=timezone.now() + timedelta(days=7 if priority == 'urgent' else 14),
    )
    
    return intervention
