from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Sum, Avg, Count, Max, Min
from django.core.paginator import Paginator
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from decimal import Decimal
import json
import logging

from .models import (
    Transaction, Vendor, Contract, FraudFlag, BudgetRecord,
    Department, BudgetCategory, AnalysisResult
)
from .forms import (
    DataImportForm, TransactionFilterForm, FraudFlagFilterForm,
    TransactionForm, VendorForm, parse_csv_transactions
)
from .utils import run_full_analysis

logger = logging.getLogger(__name__)


def dashboard(request):
    """Main dashboard with overview statistics and recent flags."""
    # Get statistics
    total_transactions = Transaction.objects.count()
    total_amount = Transaction.objects.aggregate(Sum('amount'))['amount__sum'] or Decimal('0')
    total_vendors = Vendor.objects.count()
    total_flags = FraudFlag.objects.count()
    
    # Recent flags
    recent_flags = FraudFlag.objects.filter(status__in=['new', 'investigating']).order_by('-detected_at')[:10]
    
    # Flags by risk level
    flags_by_risk = FraudFlag.objects.values('risk_level').annotate(count=Count('id'))
    risk_counts = {item['risk_level']: item['count'] for item in flags_by_risk}
    
    # Flags by type
    flags_by_type = FraudFlag.objects.values('flag_type').annotate(count=Count('id'))
    type_counts = {item['flag_type']: item['count'] for item in flags_by_type}
    
    # Top vendors by transaction count
    top_vendors = Vendor.objects.annotate(
        transaction_count=Count('transactions'),
        total_amount=Sum('transactions__amount')
    ).order_by('-transaction_count')[:10]
    
    # Spending by department
    dept_spending = Department.objects.annotate(
        total_spending=Sum('transactions__amount'),
        transaction_count=Count('transactions')
    ).filter(total_spending__gt=0).order_by('-total_spending')[:10]
    
    # Recent transactions
    recent_transactions = Transaction.objects.select_related('vendor', 'department', 'category').order_by('-date')[:10]
    
    context = {
        'total_transactions': total_transactions,
        'total_amount': total_amount,
        'total_vendors': total_vendors,
        'total_flags': total_flags,
        'recent_flags': recent_flags,
        'risk_counts': risk_counts,
        'type_counts': type_counts,
        'top_vendors': top_vendors,
        'dept_spending': dept_spending,
        'recent_transactions': recent_transactions,
    }
    
    return render(request, 'fraud_detection/dashboard.html', context)


@login_required
def import_data(request):
    """View for importing data from files."""
    if request.method == 'POST':
        form = DataImportForm(request.POST, request.FILES)
        if form.is_valid():
            data_type = form.cleaned_data['data_type']
            file = form.cleaned_data['file']
            skip_first_row = form.cleaned_data['skip_first_row']
            
            try:
                if data_type == 'transactions':
                    # Parse CSV
                    transactions, errors = parse_csv_transactions(file, skip_header=skip_first_row)
                    
                    created_count = 0
                    for trans_data in transactions:
                        # Get or create vendor
                        vendor = None
                        if trans_data.get('vendor_name'):
                            vendor, _ = Vendor.objects.get_or_create(
                                name=trans_data['vendor_name']
                            )
                        
                        # Get or create department
                        department = None
                        if trans_data.get('department_name'):
                            department, _ = Department.objects.get_or_create(
                                name=trans_data['department_name']
                            )
                        
                        # Get or create category
                        category = None
                        if trans_data.get('category_name'):
                            category, _ = BudgetCategory.objects.get_or_create(
                                name=trans_data['category_name']
                            )
                        
                        # Create transaction
                        transaction, created = Transaction.objects.get_or_create(
                            transaction_id=trans_data['transaction_id'],
                            defaults={
                                'date': trans_data['date'],
                                'amount': trans_data['amount'],
                                'description': trans_data.get('description', ''),
                                'vendor': vendor,
                                'department': department,
                                'category': category,
                                'fiscal_year': trans_data.get('fiscal_year'),
                                'invoice_number': trans_data.get('invoice_number', ''),
                                'contract_number': trans_data.get('contract_number', ''),
                                'location': trans_data.get('location', ''),
                                'status': trans_data.get('status', 'approved'),
                                'created_by': request.user,
                            }
                        )
                        if created:
                            created_count += 1
                    
                    if errors:
                        for error in errors[:10]:  # Show first 10 errors
                            messages.warning(request, error)
                        if len(errors) > 10:
                            messages.warning(request, f"... and {len(errors) - 10} more errors")
                    
                    messages.success(request, f'Successfully imported {created_count} transactions.')
                    return redirect('fraud_detection:transaction_list')
                
                else:
                    messages.error(request, f'Import for {data_type} not yet implemented.')
                    
            except Exception as e:
                logger.error(f"Import error: {str(e)}", exc_info=True)
                messages.error(request, f'Error importing data: {str(e)}')
    else:
        form = DataImportForm()
    
    return render(request, 'fraud_detection/import.html', {'form': form})


def transaction_list(request):
    """List all transactions with filtering."""
    transactions = Transaction.objects.select_related('vendor', 'department', 'category').all()
    
    # Apply filters
    form = TransactionFilterForm(request.GET)
    if form.is_valid():
        search = form.cleaned_data.get('search')
        if search:
            transactions = transactions.filter(
                Q(transaction_id__icontains=search) |
                Q(description__icontains=search) |
                Q(invoice_number__icontains=search) |
                Q(contract_number__icontains=search)
            )
        
        if form.cleaned_data.get('vendor'):
            transactions = transactions.filter(vendor=form.cleaned_data['vendor'])
        
        if form.cleaned_data.get('department'):
            transactions = transactions.filter(department=form.cleaned_data['department'])
        
        if form.cleaned_data.get('category'):
            transactions = transactions.filter(category=form.cleaned_data['category'])
        
        if form.cleaned_data.get('date_from'):
            transactions = transactions.filter(date__gte=form.cleaned_data['date_from'])
        
        if form.cleaned_data.get('date_to'):
            transactions = transactions.filter(date__lte=form.cleaned_data['date_to'])
        
        if form.cleaned_data.get('amount_min'):
            transactions = transactions.filter(amount__gte=form.cleaned_data['amount_min'])
        
        if form.cleaned_data.get('amount_max'):
            transactions = transactions.filter(amount__lte=form.cleaned_data['amount_max'])
        
        if form.cleaned_data.get('fiscal_year'):
            transactions = transactions.filter(fiscal_year=form.cleaned_data['fiscal_year'])
    
    # Pagination
    paginator = Paginator(transactions, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Calculate totals for current page/filter
    total_amount = transactions.aggregate(Sum('amount'))['amount__sum'] or Decimal('0')
    
    context = {
        'page_obj': page_obj,
        'form': form,
        'total_amount': total_amount,
        'total_count': transactions.count(),
    }
    
    return render(request, 'fraud_detection/transaction_list.html', context)


def transaction_detail(request, pk):
    """View individual transaction details."""
    transaction = get_object_or_404(
        Transaction.objects.select_related('vendor', 'department', 'category', 'created_by'),
        pk=pk
    )
    
    # Get related fraud flags
    fraud_flags = transaction.fraud_flags.all()
    
    context = {
        'transaction': transaction,
        'fraud_flags': fraud_flags,
    }
    
    return render(request, 'fraud_detection/transaction_detail.html', context)


def fraud_flag_list(request):
    """List all fraud flags with filtering."""
    flags = FraudFlag.objects.prefetch_related('transactions', 'vendors', 'contracts').all()
    
    # Apply filters
    form = FraudFlagFilterForm(request.GET)
    if form.is_valid():
        if form.cleaned_data.get('risk_level'):
            flags = flags.filter(risk_level=form.cleaned_data['risk_level'])
        
        if form.cleaned_data.get('flag_type'):
            flags = flags.filter(flag_type=form.cleaned_data['flag_type'])
        
        if form.cleaned_data.get('status'):
            flags = flags.filter(status=form.cleaned_data['status'])
    
    # Pagination
    paginator = Paginator(flags, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'form': form,
    }
    
    return render(request, 'fraud_detection/fraud_flag_list.html', context)


def fraud_flag_detail(request, pk):
    """View individual fraud flag details."""
    flag = get_object_or_404(
        FraudFlag.objects.prefetch_related('transactions', 'vendors', 'contracts', 'resolved_by'),
        pk=pk
    )
    
    context = {
        'flag': flag,
    }
    
    return render(request, 'fraud_detection/fraud_flag_detail.html', context)


@login_required
def run_analysis(request):
    """Run fraud detection analysis."""
    if request.method == 'POST':
        try:
            analysis = run_full_analysis()
            messages.success(request, f'Analysis completed! Created {analysis.flags_created} fraud flags.')
            return redirect('fraud_detection:fraud_flag_list')
        except Exception as e:
            logger.error(f"Analysis error: {str(e)}", exc_info=True)
            messages.error(request, f'Error running analysis: {str(e)}')
            return redirect('fraud_detection:dashboard')
    
    return redirect('fraud_detection:dashboard')


def vendor_list(request):
    """List all vendors."""
    vendors = Vendor.objects.annotate(
        transaction_count=Count('transactions'),
        total_amount=Sum('transactions__amount'),
        fraud_flag_count=Count('fraud_flags')
    ).order_by('-transaction_count')
    
    # Search
    search = request.GET.get('search', '')
    if search:
        vendors = vendors.filter(
            Q(name__icontains=search) |
            Q(registration_number__icontains=search)
        )
    
    paginator = Paginator(vendors, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search': search,
    }
    
    return render(request, 'fraud_detection/vendor_list.html', context)


def vendor_detail(request, pk):
    """View vendor details."""
    vendor = get_object_or_404(Vendor, pk=pk)
    
    transactions = vendor.transactions.select_related('department', 'category').order_by('-date')
    contracts = vendor.contracts.select_related('department').order_by('-start_date')
    fraud_flags = vendor.fraud_flags.all()
    
    # Statistics
    total_spending = transactions.aggregate(Sum('amount'))['amount__sum'] or Decimal('0')
    avg_transaction = transactions.aggregate(Avg('amount'))['amount__avg'] or Decimal('0')
    
    paginator = Paginator(transactions, 25)
    page_number = request.GET.get('page')
    transaction_page = paginator.get_page(page_number)
    
    context = {
        'vendor': vendor,
        'transaction_page': transaction_page,
        'contracts': contracts,
        'fraud_flags': fraud_flags,
        'total_spending': total_spending,
        'avg_transaction': avg_transaction,
        'transaction_count': transactions.count(),
    }
    
    return render(request, 'fraud_detection/vendor_detail.html', context)


@require_http_methods(["GET"])
def dashboard_api(request):
    """API endpoint for dashboard data (for AJAX requests)."""
    # Spending by month
    monthly_spending = Transaction.objects.extra(
        select={'year_month': "TO_CHAR(date, 'YYYY-MM')"}
    ).values('year_month').annotate(
        total=Sum('amount'),
        count=Count('id')
    ).order_by('year_month')
    
    # Flags by risk level
    flags_by_risk = FraudFlag.objects.values('risk_level').annotate(count=Count('id'))
    
    data = {
        'monthly_spending': list(monthly_spending),
        'flags_by_risk': list(flags_by_risk),
    }
    
    return JsonResponse(data)
