from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.urls import reverse
from decimal import Decimal


class Vendor(models.Model):
    """Vendor information for tracking relationships and patterns."""
    name = models.CharField(max_length=200)
    registration_number = models.CharField(max_length=100, blank=True, null=True, unique=True)
    address = models.TextField(blank=True)
    contact_email = models.EmailField(blank=True)
    contact_phone = models.CharField(max_length=20, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['registration_number']),
        ]
    
    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse('fraud_detection:vendor_detail', kwargs={'pk': self.pk})


class Department(models.Model):
    """Government department or agency."""
    name = models.CharField(max_length=200, unique=True)
    code = models.CharField(max_length=50, blank=True, null=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name


class BudgetCategory(models.Model):
    """Budget category for organizing spending."""
    name = models.CharField(max_length=200, unique=True)
    code = models.CharField(max_length=50, blank=True, null=True)
    description = models.TextField(blank=True)
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='children')
    
    class Meta:
        ordering = ['name']
        verbose_name_plural = 'Budget Categories'
    
    def __str__(self):
        return self.name


class Transaction(models.Model):
    """Individual transaction/expenditure record."""
    TRANSACTION_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('paid', 'Paid'),
        ('cancelled', 'Cancelled'),
    ]
    
    # Basic transaction info
    transaction_id = models.CharField(max_length=100, unique=True, db_index=True)
    date = models.DateField(db_index=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=TRANSACTION_STATUS_CHOICES, default='approved')
    
    # Relationships
    vendor = models.ForeignKey(Vendor, on_delete=models.SET_NULL, null=True, blank=True, related_name='transactions')
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True, related_name='transactions')
    category = models.ForeignKey(BudgetCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name='transactions')
    
    # Additional metadata
    fiscal_year = models.IntegerField(blank=True, null=True, db_index=True)
    invoice_number = models.CharField(max_length=100, blank=True)
    contract_number = models.CharField(max_length=100, blank=True, db_index=True)
    
    # Geographic data (optional)
    location = models.CharField(max_length=200, blank=True)
    
    # Audit fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_transactions')
    
    class Meta:
        ordering = ['-date', '-created_at']
        indexes = [
            models.Index(fields=['-date']),
            models.Index(fields=['vendor', 'date']),
            models.Index(fields=['department', 'date']),
            models.Index(fields=['amount']),
            models.Index(fields=['fiscal_year']),
        ]
    
    def __str__(self):
        return f"{self.transaction_id} - ${self.amount} - {self.date}"
    
    def get_absolute_url(self):
        return reverse('fraud_detection:transaction_detail', kwargs={'pk': self.pk})


class Contract(models.Model):
    """Contract information for analysis."""
    contract_number = models.CharField(max_length=100, unique=True, db_index=True)
    title = models.CharField(max_length=300)
    vendor = models.ForeignKey(Vendor, on_delete=models.SET_NULL, null=True, blank=True, related_name='contracts')
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True, related_name='contracts')
    
    # Financial info
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    
    # Contract details
    description = models.TextField(blank=True)
    terms = models.TextField(blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-start_date']
        indexes = [
            models.Index(fields=['vendor', 'start_date']),
            models.Index(fields=['department', 'start_date']),
        ]
    
    def __str__(self):
        return f"{self.contract_number} - {self.title}"
    
    def get_absolute_url(self):
        return reverse('fraud_detection:contract_detail', kwargs={'pk': self.pk})


class BudgetRecord(models.Model):
    """Budget allocation records."""
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='budget_records')
    category = models.ForeignKey(BudgetCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name='budget_records')
    fiscal_year = models.IntegerField(db_index=True)
    allocated_amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-fiscal_year', 'department']
        unique_together = [['department', 'category', 'fiscal_year']]
        indexes = [
            models.Index(fields=['fiscal_year', 'department']),
        ]
    
    def __str__(self):
        return f"{self.department} - FY{self.fiscal_year} - ${self.allocated_amount}"


class FraudFlag(models.Model):
    """Flags/alerts for potential fraud or waste."""
    RISK_LEVEL_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    FLAG_TYPE_CHOICES = [
        ('duplicate_payment', 'Duplicate Payment'),
        ('anomaly', 'Anomaly'),
        ('vendor_pattern', 'Suspicious Vendor Pattern'),
        ('round_number', 'Round Number Payment'),
        ('end_of_year_spike', 'End of Year Spending Spike'),
        ('contract_discrepancy', 'Contract Price Discrepancy'),
        ('employee_overlap', 'Employee/Vendor Overlap'),
        ('unusual_pattern', 'Unusual Spending Pattern'),
    ]
    
    flag_type = models.CharField(max_length=50, choices=FLAG_TYPE_CHOICES)
    risk_level = models.CharField(max_length=20, choices=RISK_LEVEL_CHOICES, default='medium')
    title = models.CharField(max_length=200)
    description = models.TextField()
    
    # Related objects
    transactions = models.ManyToManyField(Transaction, related_name='fraud_flags', blank=True)
    vendors = models.ManyToManyField(Vendor, related_name='fraud_flags', blank=True)
    contracts = models.ManyToManyField(Contract, related_name='fraud_flags', blank=True)
    
    # Status
    status = models.CharField(max_length=20, choices=[
        ('new', 'New'),
        ('investigating', 'Under Investigation'),
        ('resolved', 'Resolved'),
        ('false_positive', 'False Positive'),
    ], default='new')
    
    # Metadata
    detected_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='resolved_flags')
    notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-detected_at']
        indexes = [
            models.Index(fields=['-detected_at']),
            models.Index(fields=['risk_level', 'status']),
            models.Index(fields=['flag_type']),
        ]
    
    def __str__(self):
        return f"{self.get_flag_type_display()} - {self.title} ({self.get_risk_level_display()})"
    
    def get_absolute_url(self):
        return reverse('fraud_detection:flag_detail', kwargs={'pk': self.pk})


class AnalysisResult(models.Model):
    """Results from fraud detection analysis runs."""
    ANALYSIS_TYPE_CHOICES = [
        ('duplicate_detection', 'Duplicate Detection'),
        ('anomaly_detection', 'Anomaly Detection'),
        ('vendor_analysis', 'Vendor Analysis'),
        ('department_comparison', 'Department Comparison'),
        ('contract_analysis', 'Contract Analysis'),
        ('temporal_analysis', 'Temporal Analysis'),
        ('full_analysis', 'Full Analysis'),
    ]
    
    analysis_type = models.CharField(max_length=50, choices=ANALYSIS_TYPE_CHOICES)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=[
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ], default='running')
    
    # Results summary
    flags_created = models.IntegerField(default=0)
    transactions_analyzed = models.IntegerField(default=0)
    summary = models.TextField(blank=True)
    error_message = models.TextField(blank=True)
    
    # Parameters used
    parameters = models.JSONField(default=dict, blank=True)
    
    # User who ran the analysis
    run_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='analysis_runs')
    
    class Meta:
        ordering = ['-started_at']
    
    def __str__(self):
        return f"{self.get_analysis_type_display()} - {self.started_at}"
