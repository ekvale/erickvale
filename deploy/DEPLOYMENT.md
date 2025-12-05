# Deployment Guide for erickvale.com

This guide will help you deploy the Django application to DigitalOcean and make it live at erickvale.com.

## Prerequisites

- A DigitalOcean account
- Domain name (erickvale.com) configured to point to your DigitalOcean droplet
- SSH access to your server

## Step 1: Create DigitalOcean Droplet

1. Log in to DigitalOcean
2. Click "Create" → "Droplets"
3. Choose:
   - **Image**: Ubuntu 22.04 LTS
   - **Plan**: Basic (at least 1GB RAM recommended)
   - **Datacenter**: Choose closest to your users
   - **Authentication**: SSH keys (recommended) or password
4. Click "Create Droplet"

## Step 2: Initial Server Setup

### Connect to your server

```bash
ssh root@your_droplet_ip
```

### Update system packages

```bash
apt update && apt upgrade -y
```

### Create a non-root user

```bash
adduser erickvale
usermod -aG sudo erickvale
su - erickvale
```

### Set up SSH keys (optional but recommended)

On your local machine, copy your SSH key:
```bash
ssh-copy-id erickvale@your_droplet_ip
```

## Step 3: Install Required Software

### Install Python and pip

```bash
sudo apt install -y python3 python3-pip python3-venv python3-dev
```

### Install PostgreSQL

```bash
sudo apt install -y postgresql postgresql-contrib
```

### Install Nginx

```bash
sudo apt install -y nginx
```

### Install other dependencies

```bash
sudo apt install -y build-essential libpq-dev
```

## Step 4: Set Up PostgreSQL Database

### Create database and user

```bash
sudo -u postgres psql
```

In PostgreSQL prompt:
```sql
CREATE DATABASE erickvale;
CREATE USER erickvale_user WITH PASSWORD 'your_secure_password_here';
ALTER ROLE erickvale_user SET client_encoding TO 'utf8';
ALTER ROLE erickvale_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE erickvale_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE erickvale TO erickvale_user;
\q
```

### Configure PostgreSQL for remote access (if needed)

Edit `/etc/postgresql/14/main/postgresql.conf`:
```
listen_addresses = 'localhost'
```

Edit `/etc/postgresql/14/main/pg_hba.conf`:
```
local   all             all                                     peer
host    all             all             127.0.0.1/32            md5
```

Restart PostgreSQL:
```bash
sudo systemctl restart postgresql
```

## Step 5: Deploy Application Code

### Clone or upload your code

Option 1: Using Git (recommended)
```bash
cd /home/erickvale
git clone your_repository_url erickvale
cd erickvale
```

Option 2: Using SCP from local machine
```bash
# On your local machine
scp -r /path/to/erickvale erickvale@your_droplet_ip:/home/erickvale/
```

### Create virtual environment

```bash
cd /home/erickvale/erickvale
python3 -m venv venv
source venv/bin/activate
```

### Install Python dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

## Step 6: Configure Environment Variables

### Create .env file

```bash
cd /home/erickvale/erickvale
nano .env
```

Add the following (update with your actual values):
```
SECRET_KEY=your-generated-secret-key-here
DEBUG=False
ALLOWED_HOSTS=erickvale.com,www.erickvale.com

DB_NAME=erickvale
DB_USER=erickvale_user
DB_PASSWORD=your_database_password_here
DB_HOST=localhost
DB_PORT=5432
```

### Generate a secure SECRET_KEY

```bash
python manage.py shell -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Copy the output and use it as your SECRET_KEY in the .env file.

## Step 7: Run Database Migrations

```bash
cd /home/erickvale/erickvale
source venv/bin/activate
python manage.py migrate
python manage.py collectstatic --noinput
```

### Create superuser

```bash
python manage.py createsuperuser
```

## Step 8: Configure Gunicorn

### Create directories for logs

```bash
mkdir -p /home/erickvale/logs
```

### Update gunicorn_config.py

The file is already created at `deploy/gunicorn_config.py`. Make sure the paths are correct for your setup.

### Test Gunicorn

```bash
cd /home/erickvale/erickvale
source venv/bin/activate
gunicorn --config deploy/gunicorn_config.py erickvale.wsgi:application
```

If it works, press Ctrl+C to stop it.

## Step 9: Set Up Systemd Service

### Copy service file

```bash
sudo cp /home/erickvale/erickvale/deploy/erickvale.service /etc/systemd/system/
```

### Reload systemd and start service

```bash
sudo systemctl daemon-reload
sudo systemctl enable erickvale
sudo systemctl start erickvale
```

### Check status

```bash
sudo systemctl status erickvale
```

## Step 10: Configure Nginx

### Copy nginx configuration

```bash
sudo cp /home/erickvale/erickvale/deploy/nginx.conf /etc/nginx/sites-available/erickvale
sudo ln -s /etc/nginx/sites-available/erickvale /etc/nginx/sites-enabled/
```

### Remove default nginx site (optional)

```bash
sudo rm /etc/nginx/sites-enabled/default
```

### Test nginx configuration

```bash
sudo nginx -t
```

### Start and enable nginx

```bash
sudo systemctl start nginx
sudo systemctl enable nginx
```

## Step 11: Set Up SSL with Let's Encrypt

### Install Certbot

```bash
sudo apt install -y certbot python3-certbot-nginx
```

### Obtain SSL certificate

```bash
sudo certbot --nginx -d erickvale.com -d www.erickvale.com
```

Follow the prompts. Certbot will automatically configure nginx.

### Auto-renewal (already set up by certbot)

Test renewal:
```bash
sudo certbot renew --dry-run
```

## Step 12: Configure Firewall

### Allow necessary ports

```bash
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'
sudo ufw enable
```

## Step 13: Final Checks

### Verify services are running

```bash
sudo systemctl status erickvale
sudo systemctl status nginx
sudo systemctl status postgresql
```

### Check logs if issues

```bash
# Gunicorn logs
tail -f /home/erickvale/logs/gunicorn_error.log
tail -f /home/erickvale/logs/gunicorn_access.log

# Nginx logs
sudo tail -f /var/log/nginx/error.log
sudo tail -f /var/log/nginx/access.log

# Django logs (if configured)
tail -f /home/erickvale/logs/django.log
```

### Test the website

Visit `https://erickvale.com` in your browser.

## Step 14: Domain Configuration

Make sure your domain DNS is configured:

1. **A Record**: Point `erickvale.com` to your droplet's IP address
2. **A Record**: Point `www.erickvale.com` to your droplet's IP address (or use CNAME)

Wait for DNS propagation (can take up to 48 hours, usually much faster).

## Maintenance Commands

### Restart services

```bash
# Restart Django app
sudo systemctl restart erickvale

# Restart Nginx
sudo systemctl restart nginx

# Restart PostgreSQL
sudo systemctl restart postgresql
```

### Update code

```bash
cd /home/erickvale/erickvale
source venv/bin/activate
git pull  # or upload new files
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
sudo systemctl restart erickvale
```

### View logs

```bash
# Application logs
sudo journalctl -u erickvale -f

# Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

## Security Checklist

- [ ] Changed default SSH port (optional but recommended)
- [ ] Set up firewall (ufw)
- [ ] Using strong database passwords
- [ ] SECRET_KEY is secure and in .env (not in code)
- [ ] DEBUG=False in production
- [ ] SSL certificate installed and auto-renewing
- [ ] Regular system updates enabled
- [ ] Backups configured (DigitalOcean snapshots or manual)

## Troubleshooting

### 502 Bad Gateway

- Check if Gunicorn is running: `sudo systemctl status erickvale`
- Check Gunicorn logs: `tail -f /home/erickvale/logs/gunicorn_error.log`
- Verify nginx can reach Gunicorn on port 8000

### Static files not loading

- Run `python manage.py collectstatic`
- Check nginx static file configuration
- Verify file permissions

### Database connection errors

- Check PostgreSQL is running: `sudo systemctl status postgresql`
- Verify .env file has correct database credentials
- Check PostgreSQL logs: `sudo tail -f /var/log/postgresql/postgresql-14-main.log`

### Permission errors

- Ensure erickvale user owns the project directory:
  ```bash
  sudo chown -R erickvale:erickvale /home/erickvale
  ```

## Backup Strategy

### Database backup

```bash
# Create backup
sudo -u postgres pg_dump erickvale > /home/erickvale/backups/db_backup_$(date +%Y%m%d).sql

# Restore backup
sudo -u postgres psql erickvale < /home/erickvale/backups/db_backup_YYYYMMDD.sql
```

### Automated backups (cron)

Add to crontab:
```bash
crontab -e
```

Add line:
```
0 2 * * * sudo -u postgres pg_dump erickvale > /home/erickvale/backups/db_backup_$(date +\%Y\%m\%d).sql
```

## Support

For issues, check:
- Django logs: `/home/erickvale/logs/`
- Nginx logs: `/var/log/nginx/`
- System logs: `sudo journalctl -u erickvale`

