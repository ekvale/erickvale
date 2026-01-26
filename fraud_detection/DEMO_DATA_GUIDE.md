# Generating Demo Data for Fraud Detection App

This guide explains how to generate synthetic data to demonstrate the fraud detection capabilities.

## Quick Start

```bash
# Generate 500 transactions with fraud patterns
python manage.py generate_sample_data --transactions 500

# Or generate more data
python manage.py generate_sample_data --transactions 1000

# Clear existing data and generate fresh
python manage.py generate_sample_data --transactions 500 --clear
```

## What Gets Generated

The command creates realistic synthetic data including:

### Departments (10)
- Public Works, Finance, IT Services, Public Safety, Health & Human Services, etc.

### Budget Categories (8)
- Personnel, Equipment, Services, Supplies, Contractual, Utilities, Maintenance, Professional Services

### Vendors (10)
- 5 normal vendors (Acme Corporation, Global Services Inc, etc.)
- 5 suspicious vendors with specific patterns:
  - **Quick Pay Services**: Round number payments
  - **Just Under LLC**: Payments just under reporting thresholds
  - **Duplicate Co**: Duplicate payments
  - **End Year Specialists**: End of fiscal year spending spikes
  - **Anomaly Industries**: Statistical anomalies

### Contracts (~17)
- Normal contracts with various vendors and departments
- Some contracts with price discrepancies (same department, similar services, different prices)

### Budget Records
- Budget allocations for departments and categories for FY2024

### Transactions
The transactions are created with specific patterns:

1. **Normal Transactions (70%)**
   - Regular payments with realistic amounts
   - Various vendors, departments, and categories
   - Spread throughout the year

2. **Round Number Payments (10%)**
   - Payments in round amounts ($1,000, $2,000, $5,000, $10,000, etc.)
   - All from "Quick Pay Services" vendor
   - Will trigger round number detection

3. **Just Under Threshold (5%)**
   - Payments at 90% of common thresholds ($4,500, $9,000, $22,500)
   - All from "Just Under LLC" vendor
   - Will trigger vendor pattern detection

4. **Duplicate Payments (5%)**
   - Pairs of transactions with same vendor, same amount, within 30 days
   - All from "Duplicate Co" vendor
   - Will trigger duplicate payment detection

5. **End of Year Spikes (5%)**
   - Concentrated in April, May, June (end of fiscal year)
   - All from "End Year Specialists" vendor
   - Will trigger end of year spike detection

6. **Anomalies (5%)**
   - Transactions 5x above average for department/category
   - All from "Anomaly Industries" vendor
   - Will trigger anomaly detection

## Demo Workflow

1. **Generate the data:**
   ```bash
   python manage.py generate_sample_data --transactions 500
   ```

2. **Visit the dashboard:**
   - Navigate to `/apps/fraud-detection/`
   - You should see statistics showing the generated data

3. **Run fraud detection analysis:**
   - Click "Run Full Analysis" button on the dashboard
   - Wait for the analysis to complete (may take a minute)

4. **Review fraud flags:**
   - Go to "Fraud Flags" page
   - You should see flags for:
     - Duplicate payments
     - Round number payments
     - Vendor patterns
     - End of year spikes
     - Anomalies
     - Contract discrepancies

5. **Explore the data:**
   - View transactions and see the patterns
   - Check vendor details to see suspicious patterns
   - Review fraud flag details to understand what was detected

## Tips

- Start with 500 transactions for a quick demo
- Use 1000+ transactions for more comprehensive patterns
- The `--clear` flag will remove all existing fraud detection data before generating
- Run the analysis multiple times to see how flags accumulate
- Check the vendor detail pages to see patterns specific to suspicious vendors

## Troubleshooting

**No fraud flags detected:**
- Make sure you ran "Run Full Analysis" after generating data
- Check that transactions were created successfully
- Verify suspicious vendors exist in the database

**Analysis takes too long:**
- Reduce the number of transactions
- The analysis processes all transactions, so more data = longer time

**Want to start fresh:**
```bash
python manage.py generate_sample_data --transactions 500 --clear
```
