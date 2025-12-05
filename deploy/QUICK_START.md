# Quick Start Deployment Guide

## Prerequisites Checklist

- [ ] DigitalOcean droplet created (Ubuntu 22.04)
- [ ] Domain erickvale.com pointing to droplet IP
- [ ] SSH access to server

## Quick Deployment Steps

### 1. Initial Server Setup (Run as root)

```bash
# On your server
wget https://raw.githubusercontent.com/your-repo/erickvale/main/deploy/setup.sh
chmod +x setup.sh
sudo ./setup.sh
```

Or manually:
```bash
sudo apt update && apt upgrade -y
sudo apt install -y python3 python3-pip python3-venv python3-dev postgresql postgresql-contrib nginx build-essential libpq-dev certbot python3-certbot-nginx git
sudo adduser erickvale
sudo usermod -aG sudo erickvale
```

### 2. Set Up Database

```bash
sudo -u postgres psql
```

```sql
CREATE DATABASE erickvale;
CREATE USER erickvale_user WITH PASSWORD 'your_secure_password';
ALTER ROLE erickvale_user SET client_encoding TO 'utf8';
ALTER ROLE erickvale_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE erickvale_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE erickvale TO erickvale_user;
\q
```

### 3. Deploy Code

```bash
su - erickvale
cd /home/erickvale
git clone your_repo_url erickvale
# OR upload via SCP
cd erickvale
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 4. Configure Environment

```bash
cp deploy/env.example .env
nano .env
# Fill in: SECRET_KEY, DEBUG=False, ALLOWED_HOSTS, DB credentials
```

Generate SECRET_KEY:
```bash
python manage.py shell -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### 5. Initialize Database

```bash
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py createsuperuser
```

### 6. Set Up Gunicorn Service

```bash
sudo cp deploy/erickvale.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable erickvale
sudo systemctl start erickvale
sudo systemctl status erickvale
```

### 7. Configure Nginx

```bash
sudo cp deploy/nginx.conf /etc/nginx/sites-available/erickvale
sudo ln -s /etc/nginx/sites-available/erickvale /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default  # Optional
sudo nginx -t
sudo systemctl restart nginx
```

### 8. Set Up SSL

```bash
sudo certbot --nginx -d erickvale.com -d www.erickvale.com
```

### 9. Configure Firewall

```bash
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'
sudo ufw enable
```

### 10. Test

Visit `https://erickvale.com` in your browser!

## Common Commands

```bash
# Restart app
sudo systemctl restart erickvale

# View logs
sudo journalctl -u erickvale -f
tail -f /home/erickvale/logs/gunicorn_error.log

# Update code
cd /home/erickvale/erickvale
source venv/bin/activate
git pull
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
sudo systemctl restart erickvale
```

## Troubleshooting

**502 Bad Gateway**: Check if Gunicorn is running
```bash
sudo systemctl status erickvale
```

**Static files not loading**: Run collectstatic
```bash
python manage.py collectstatic --noinput
```

**Permission errors**: Fix ownership
```bash
sudo chown -R erickvale:erickvale /home/erickvale
```

For detailed information, see `DEPLOYMENT.md`.

