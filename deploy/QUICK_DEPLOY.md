# Quick Deployment Commands for Your Droplet

**Droplet IP:** 143.110.236.17  
**Location:** SFO3 (San Francisco)  
**OS:** Ubuntu 22.04 LTS

## Step 1: Connect to Your Server

```bash
ssh root@143.110.236.17
```

## Step 2: Initial Setup (Run as root)

```bash
# Update system
apt update && apt upgrade -y

# Install required packages
apt install -y python3 python3-pip python3-venv python3-dev \
    postgresql postgresql-contrib \
    nginx \
    build-essential libpq-dev \
    certbot python3-certbot-nginx \
    git

# Create application user
adduser erickvale
usermod -aG sudo erickvale

# Create directories
mkdir -p /home/erickvale/logs
mkdir -p /home/erickvale/backups
chown -R erickvale:erickvale /home/erickvale

# Configure firewall
ufw allow OpenSSH
ufw allow 'Nginx Full'
ufw --force enable
```

## Step 3: Switch to Application User

```bash
su - erickvale
```

## Step 4: Set Up PostgreSQL Database

```bash
sudo -u postgres psql
```

In PostgreSQL prompt:
```sql
CREATE DATABASE erickvale;
CREATE USER erickvale_user WITH PASSWORD 'CHANGE_THIS_TO_SECURE_PASSWORD';
ALTER ROLE erickvale_user SET client_encoding TO 'utf8';
ALTER ROLE erickvale_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE erickvale_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE erickvale TO erickvale_user;
\q
```

## Step 5: Deploy Your Code

**Option A: Using Git (if you have a repository)**
```bash
cd /home/erickvale
git clone YOUR_REPO_URL erickvale
cd erickvale
```

**Option B: Using SCP (from your local machine)**
```bash
# On your local Windows machine (PowerShell)
scp -r D:\erickvale erickvale@143.110.236.17:/home/erickvale/
```

Then on server:
```bash
cd /home/erickvale/erickvale
```

## Step 6: Set Up Python Environment

```bash
cd /home/erickvale/erickvale
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

## Step 7: Configure Environment Variables

```bash
cd /home/erickvale/erickvale
cp deploy/env.example .env
nano .env
```

Update the `.env` file with:
```
SECRET_KEY=GENERATE_THIS_BELOW
DEBUG=False
ALLOWED_HOSTS=erickvale.com,www.erickvale.com,143.110.236.17

DB_NAME=erickvale
DB_USER=erickvale_user
DB_PASSWORD=YOUR_DATABASE_PASSWORD_FROM_STEP_4
DB_HOST=localhost
DB_PORT=5432
```

Generate SECRET_KEY:
```bash
source venv/bin/activate
python manage.py shell -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Copy the output and paste it as SECRET_KEY in your `.env` file.

## Step 8: Initialize Database

```bash
cd /home/erickvale/erickvale
source venv/bin/activate
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py createsuperuser
```

## Step 9: Set Up Gunicorn Service

```bash
sudo cp /home/erickvale/erickvale/deploy/erickvale.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable erickvale
sudo systemctl start erickvale
sudo systemctl status erickvale
```

## Step 10: Configure Nginx

```bash
sudo cp /home/erickvale/erickvale/deploy/nginx.conf /etc/nginx/sites-available/erickvale
sudo ln -s /etc/nginx/sites-available/erickvale /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx
sudo systemctl enable nginx
```

## Step 11: Set Up SSL (After DNS is Configured)

**IMPORTANT:** Make sure your domain DNS is pointing to 143.110.236.17 first!

```bash
sudo certbot --nginx -d erickvale.com -d www.erickvale.com
```

## Step 12: Configure DNS

In your domain registrar (where you bought erickvale.com):

1. **A Record**: `erickvale.com` → `143.110.236.17`
2. **A Record**: `www.erickvale.com` → `143.110.236.17` (or CNAME to erickvale.com)

Wait for DNS propagation (usually 5-30 minutes, can take up to 48 hours).

## Step 13: Test

Visit `http://143.110.236.17` (before SSL) or `https://erickvale.com` (after SSL and DNS)

## Quick Status Checks

```bash
# Check all services
sudo systemctl status erickvale
sudo systemctl status nginx
sudo systemctl status postgresql

# View logs
sudo journalctl -u erickvale -f
tail -f /home/erickvale/logs/gunicorn_error.log
```

## Common Issues

**502 Bad Gateway:**
- Check Gunicorn: `sudo systemctl status erickvale`
- Check logs: `tail -f /home/erickvale/logs/gunicorn_error.log`

**Permission errors:**
```bash
sudo chown -R erickvale:erickvale /home/erickvale
```

**Static files not loading:**
```bash
cd /home/erickvale/erickvale
source venv/bin/activate
python manage.py collectstatic --noinput
```

