# Fraud Detection & Budget Analysis App

A Django application for analyzing government budget data and detecting potential fraud, waste, and abuse in spending.

## Features

### Data Management
- Import transactions, budgets, contracts, and vendor data from CSV, Excel, or JSON files
- Comprehensive data models for tracking financial records
- Support for multiple departments, categories, and fiscal years

### Fraud Detection Algorithms
- **Duplicate Payment Detection**: Identifies potential duplicate transactions
- **Round Number Detection**: Flags vendors with many round-number payments
- **Anomaly Detection**: Uses statistical analysis to find outliers
- **End of Year Spike Detection**: Identifies unusual spending at fiscal year end
- **Vendor Pattern Analysis**: Detects suspicious vendor payment patterns
- **Contract Price Comparison**: Compares similar contracts for discrepancies

### Visualization & Reporting
- Interactive dashboard with key statistics
- Transaction listing with advanced filtering
- Fraud flag management and tracking
- Vendor analysis and profiling
- Department spending comparisons

## Models

- **Transaction**: Individual expenditure records
- **Vendor**: Vendor information and relationships
- **Department**: Government departments/agencies
- **BudgetCategory**: Budget categorization
- **Contract**: Contract information
- **BudgetRecord**: Budget allocations
- **FraudFlag**: Detected fraud/waste alerts
- **AnalysisResult**: Analysis run history

## Usage

### Accessing the App

Navigate to `/apps/fraud-detection/` in your browser.

### Generating Sample Data

To generate synthetic data for demo purposes:

```bash
python manage.py generate_sample_data --transactions 500
```

Options:
- `--transactions N`: Number of transactions to generate (default: 500)
- `--clear`: Clear existing data before generating new data

The command will create:
- 10 departments
- 8 budget categories
- 10 vendors (including 5 with suspicious patterns)
- ~17 contracts (including some with price discrepancies)
- Budget records for departments/categories
- Transactions with various fraud patterns:
  - Round number payments
  - Payments just under reporting thresholds
  - Duplicate payments
  - End of year spending spikes
  - Statistical anomalies

### Importing Data

1. Go to the Import Data page
2. Select data type (Transactions, Budgets, Contracts, or Vendors)
3. Upload a CSV file with the required columns
4. The system will automatically create related entities (vendors, departments, categories) if they don't exist

### Running Analysis

1. Import your transaction data (or use sample data)
2. Go to the Dashboard
3. Click "Run Full Analysis" to execute all fraud detection algorithms
4. Review the generated fraud flags

### CSV Format for Transactions

Required columns:
- `transaction_id` (unique identifier)
- `date` (YYYY-MM-DD or MM/DD/YYYY)
- `amount` (numeric)

Optional columns:
- `description`, `vendor_name`, `department_name`, `category_name`
- `fiscal_year`, `invoice_number`, `contract_number`, `location`, `status`

## Fraud Detection Types

1. **Duplicate Payment**: Same vendor, similar amount, close dates
2. **Round Number**: Multiple round-number payments to same vendor
3. **Anomaly**: Transactions significantly above average
4. **End of Year Spike**: Unusual spending at fiscal year end
5. **Vendor Pattern**: Payments just under reporting thresholds
6. **Contract Discrepancy**: Significant price differences in similar contracts

## Permissions

- View access: All authenticated users
- Import data: Authenticated users
- Run analysis: Authenticated users
- Admin access: Staff users (via Django admin)
- Navbar link: Staff users only

## Demo Workflow

1. **Generate sample data:**
   ```bash
   python manage.py generate_sample_data --transactions 500
   ```

2. **Visit the dashboard:**
   Navigate to `/apps/fraud-detection/`

3. **Run analysis:**
   Click "Run Full Analysis" button on the dashboard

4. **Review results:**
   - Check the "Fraud Flags" section
   - View individual flags for details
   - Explore transactions and vendors

5. **Explore patterns:**
   - View vendors with suspicious patterns
   - Check duplicate payments
   - Review end of year spending

## Future Enhancements

- Machine learning models for fraud detection
- Geographic visualization of spending
- Advanced reporting and export (PDF, Excel)
- Email alerts for high-risk flags
- Integration with external data sources
- Real-time monitoring and alerts
