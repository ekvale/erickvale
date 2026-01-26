# Fraud Detection App - Deployment Instructions

This guide covers deploying the new Fraud Detection app to your production server.

## Pre-Deployment Checklist

- [ ] Code committed and pushed to GitHub
- [ ] Database migrations created
- [ ] All dependencies in requirements.txt
- [ ] Environment variables configured

## Step 1: Push to GitHub

On your local machine:

```bash
cd /path/to/erickvale
git add .
git commit -m "Add fraud detection app with fraud detection algorithms and data import"
git push origin main
```

## Step 2: Deploy to Server

### SSH into your server

```bash
ssh erickvale@your_server_ip
```

### Navigate to project directory

```bash
cd /home/erickvale/erickvale
```

### Pull latest code

```bash
git pull origin main
```

### Activate virtual environment

```bash
source venv/bin/activate
```

### Install/update dependencies

```bash
pip install -r requirements.txt
```

### Run migrations

```bash
python manage.py migrate fraud_detection
```

This will create all the new tables for:
- Department
- BudgetCategory
- Vendor
- Transaction
- Contract
- BudgetRecord
- FraudFlag
- AnalysisResult

### Collect static files

```bash
python manage.py collectstatic --noinput
```

### Restart the application

```bash
sudo systemctl restart erickvale
```

### Verify the service is running

```bash
sudo systemctl status erickvale
```

## Step 3: Verify Deployment

### Check the app is accessible

1. Visit `https://erickvale.com/apps/fraud-detection/` in your browser
2. You should see the Fraud Detection Dashboard
3. If you're logged in as a staff user, you should see "Fraud Detection" in the navbar

### Test functionality

1. **Import Data**: Go to `/apps/fraud-detection/import/` and try importing a sample CSV
2. **Run Analysis**: Go to Dashboard and click "Run Full Analysis"
3. **View Flags**: Check `/apps/fraud-detection/flags/` for any detected fraud flags

## Step 4: Create Sample Data (Optional)

If you want to test with sample data, you can create a CSV file with the following structure:

```csv
transaction_id,date,amount,description,vendor_name,department_name,category_name,fiscal_year,status
TXN001,2024-01-15,5000.00,Office Supplies,Acme Corp,Finance,Supplies,2024,approved
TXN002,2024-01-16,5000.00,Office Supplies,Acme Corp,Finance,Supplies,2024,approved
TXN003,2024-01-20,10000.00,Consulting Services,Consulting Inc,IT,Services,2024,approved
```

Save this as `sample_transactions.csv` and import it through the web interface.

## Step 5: Set Up Staff User (If Needed)

To access the Fraud Detection app, users need staff status:

```bash
cd /home/erickvale/erickvale
source venv/bin/activate
python manage.py shell
```

In the Django shell:
```python
from django.contrib.auth.models import User
user = User.objects.get(username='your_username')
user.is_staff = True
user.save()
exit()
```

## Troubleshooting

### App not showing in navbar

- Verify user has `is_staff = True` in Django admin
- Check that the user is logged in
- Clear browser cache

### Migration errors

```bash
# If migrations fail, check for conflicts
python manage.py showmigrations fraud_detection

# Reset migrations if needed (WARNING: Only on development)
# python manage.py migrate fraud_detection zero
# python manage.py migrate fraud_detection
```

### Import errors

- Check CSV format matches expected columns
- Verify file encoding is UTF-8
- Check file size (max 50MB)
- Review error messages in Django logs

### Analysis not running

- Check that transactions exist in database
- Review error logs: `tail -f /home/erickvale/logs/gunicorn_error.log`
- Verify database has sufficient data for analysis

## Post-Deployment

### Monitor logs

```bash
# Application logs
sudo journalctl -u erickvale -f

# Error logs
tail -f /home/erickvale/logs/gunicorn_error.log
```

### Performance considerations

- The fraud detection analysis can be resource-intensive with large datasets
- Consider running analysis during off-peak hours
- Monitor database performance during analysis runs

### Security notes

- Fraud Detection app is only visible to staff users
- All data import requires authentication
- Sensitive financial data should be handled with care
- Consider additional access controls if needed

## Rollback (If Needed)

If you need to rollback:

```bash
cd /home/erickvale/erickvale
git log  # Find the commit before fraud_detection
git checkout <previous_commit_hash>
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate  # May need to handle migrations
python manage.py collectstatic --noinput
sudo systemctl restart erickvale
```

## Next Steps

After successful deployment:

1. Import real transaction data
2. Run initial analysis
3. Review and configure fraud detection thresholds if needed
4. Set up regular analysis schedule (via cron or management command)
5. Train users on how to use the app

## Support

For issues:
- Check Django logs: `/home/erickvale/logs/`
- Review nginx logs: `sudo tail -f /var/log/nginx/error.log`
- Check system logs: `sudo journalctl -u erickvale`
