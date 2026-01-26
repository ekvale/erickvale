from django import forms
from .models import Transaction, Vendor, Department, BudgetCategory, Contract, BudgetRecord, FraudFlag
import csv
import json
from decimal import Decimal, InvalidOperation
from datetime import datetime


class DataImportForm(forms.Form):
    """Form for importing data from CSV, Excel, or JSON."""
    
    DATA_TYPE_CHOICES = [
        ('transactions', 'Transactions'),
        ('budgets', 'Budget Records'),
        ('contracts', 'Contracts'),
        ('vendors', 'Vendors'),
    ]
    
    data_type = forms.ChoiceField(
        choices=DATA_TYPE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    file = forms.FileField(
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.csv,.xlsx,.xls,.json'
        }),
        help_text='Upload CSV, Excel, or JSON file'
    )
    skip_first_row = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text='Skip first row (header row)'
    )
    
    def clean_file(self):
        file = self.cleaned_data.get('file')
        if file:
            # Check file extension
            file_name = file.name.lower()
            if not any(file_name.endswith(ext) for ext in ['.csv', '.xlsx', '.xls', '.json']):
                raise forms.ValidationError('File must be CSV, Excel, or JSON format.')
            
            # Check file size (max 50MB)
            max_size = 50 * 1024 * 1024  # 50MB
            if file.size > max_size:
                raise forms.ValidationError(f'File size cannot exceed {max_size / (1024*1024):.0f}MB.')
        
        return file


class TransactionFilterForm(forms.Form):
    """Form for filtering transactions."""
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search by ID, description, invoice...'
        })
    )
    vendor = forms.ModelChoiceField(
        required=False,
        queryset=Vendor.objects.all().order_by('name'),
        widget=forms.Select(attrs={'class': 'form-control'}),
        empty_label='All Vendors'
    )
    department = forms.ModelChoiceField(
        required=False,
        queryset=Department.objects.all().order_by('name'),
        widget=forms.Select(attrs={'class': 'form-control'}),
        empty_label='All Departments'
    )
    category = forms.ModelChoiceField(
        required=False,
        queryset=BudgetCategory.objects.all().order_by('name'),
        widget=forms.Select(attrs={'class': 'form-control'}),
        empty_label='All Categories'
    )
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    amount_min = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'placeholder': 'Min amount'
        })
    )
    amount_max = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'placeholder': 'Max amount'
        })
    )
    fiscal_year = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Fiscal year'
        })
    )


class FraudFlagFilterForm(forms.Form):
    """Form for filtering fraud flags."""
    risk_level = forms.ChoiceField(
        required=False,
        choices=[('', 'All Risk Levels')] + FraudFlag.RISK_LEVEL_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    flag_type = forms.ChoiceField(
        required=False,
        choices=[('', 'All Types')] + FraudFlag.FLAG_TYPE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    status = forms.ChoiceField(
        required=False,
        choices=[('', 'All Statuses')] + [
            ('new', 'New'),
            ('investigating', 'Under Investigation'),
            ('resolved', 'Resolved'),
            ('false_positive', 'False Positive'),
        ],
        widget=forms.Select(attrs={'class': 'form-control'})
    )


class TransactionForm(forms.ModelForm):
    """Form for creating/editing transactions."""
    class Meta:
        model = Transaction
        fields = [
            'transaction_id', 'date', 'amount', 'description', 'status',
            'vendor', 'department', 'category', 'fiscal_year',
            'invoice_number', 'contract_number', 'location'
        ]
        widgets = {
            'transaction_id': forms.TextInput(attrs={'class': 'form-control'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'vendor': forms.Select(attrs={'class': 'form-control'}),
            'department': forms.Select(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'fiscal_year': forms.NumberInput(attrs={'class': 'form-control'}),
            'invoice_number': forms.TextInput(attrs={'class': 'form-control'}),
            'contract_number': forms.TextInput(attrs={'class': 'form-control'}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
        }


class VendorForm(forms.ModelForm):
    """Form for creating/editing vendors."""
    class Meta:
        model = Vendor
        fields = ['name', 'registration_number', 'address', 'contact_email', 'contact_phone']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'registration_number': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'contact_email': forms.EmailInput(attrs={'class': 'form-control'}),
            'contact_phone': forms.TextInput(attrs={'class': 'form-control'}),
        }


def parse_csv_transactions(file, skip_header=True):
    """
    Parse CSV file and return list of transaction dictionaries.
    Expected columns: transaction_id, date, amount, description, vendor_name, 
                      department_name, category_name, fiscal_year, invoice_number, etc.
    """
    transactions = []
    errors = []
    
    try:
        # Try to decode as UTF-8, fallback to latin-1
        content = file.read()
        try:
            content = content.decode('utf-8')
        except UnicodeDecodeError:
            content = content.decode('latin-1')
        
        reader = csv.DictReader(content.splitlines())
        
        for row_num, row in enumerate(reader, start=2 if skip_header else 1):
            try:
                # Required fields
                if not row.get('transaction_id'):
                    errors.append(f"Row {row_num}: Missing transaction_id")
                    continue
                
                if not row.get('date'):
                    errors.append(f"Row {row_num}: Missing date")
                    continue
                
                if not row.get('amount'):
                    errors.append(f"Row {row_num}: Missing amount")
                    continue
                
                # Parse date
                try:
                    date = datetime.strptime(row['date'], '%Y-%m-%d').date()
                except ValueError:
                    try:
                        date = datetime.strptime(row['date'], '%m/%d/%Y').date()
                    except ValueError:
                        errors.append(f"Row {row_num}: Invalid date format: {row['date']}")
                        continue
                
                # Parse amount
                try:
                    amount = Decimal(str(row['amount']).replace('$', '').replace(',', '').strip())
                except (InvalidOperation, ValueError):
                    errors.append(f"Row {row_num}: Invalid amount: {row['amount']}")
                    continue
                
                transaction_data = {
                    'transaction_id': row['transaction_id'].strip(),
                    'date': date,
                    'amount': amount,
                    'description': row.get('description', '').strip(),
                    'vendor_name': row.get('vendor_name', '').strip(),
                    'department_name': row.get('department_name', '').strip(),
                    'category_name': row.get('category_name', '').strip(),
                    'fiscal_year': int(row['fiscal_year']) if row.get('fiscal_year') else None,
                    'invoice_number': row.get('invoice_number', '').strip(),
                    'contract_number': row.get('contract_number', '').strip(),
                    'location': row.get('location', '').strip(),
                    'status': row.get('status', 'approved').strip(),
                }
                
                transactions.append(transaction_data)
                
            except Exception as e:
                errors.append(f"Row {row_num}: Error parsing row - {str(e)}")
                continue
        
    except Exception as e:
        errors.append(f"Error reading CSV file: {str(e)}")
    
    return transactions, errors
