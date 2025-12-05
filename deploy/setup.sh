#!/bin/bash
# Initial server setup script for erickvale.com deployment
# Run this script as root on a fresh Ubuntu 22.04 server

set -e

echo "Starting erickvale.com server setup..."

# Update system
echo "Updating system packages..."
apt update && apt upgrade -y

# Install required packages
echo "Installing required packages..."
apt install -y python3 python3-pip python3-venv python3-dev \
    postgresql postgresql-contrib \
    nginx \
    build-essential libpq-dev \
    certbot python3-certbot-nginx \
    git

# Create application user
if ! id "erickvale" &>/dev/null; then
    echo "Creating erickvale user..."
    adduser --disabled-password --gecos "" erickvale
    usermod -aG sudo erickvale
else
    echo "User erickvale already exists"
fi

# Create necessary directories
echo "Creating directories..."
mkdir -p /home/erickvale/logs
mkdir -p /home/erickvale/backups
chown -R erickvale:erickvale /home/erickvale

# Configure firewall
echo "Configuring firewall..."
ufw allow OpenSSH
ufw allow 'Nginx Full'
ufw --force enable

echo "Setup complete!"
echo ""
echo "Next steps:"
echo "1. Switch to erickvale user: su - erickvale"
echo "2. Clone/upload your code to /home/erickvale/erickvale"
echo "3. Follow the deployment guide in deploy/DEPLOYMENT.md"

