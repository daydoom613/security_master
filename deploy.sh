#!/bin/bash

# Deployment script for AlfaGrow Security Service on EC2

echo "🚀 Starting deployment of AlfaGrow Security Service..."

# Update system packages
echo "📦 Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install Python 3.9+ and pip
echo "🐍 Installing Python and pip..."
sudo apt install -y python3 python3-pip python3-venv

# Install PostgreSQL client
echo "🗄️ Installing PostgreSQL client..."
sudo apt install -y postgresql-client

# Install Nginx
echo "🌐 Installing Nginx..."
sudo apt install -y nginx

# Create application directory
echo "📁 Creating application directory..."
sudo mkdir -p /opt/alfago-security
sudo chown ubuntu:ubuntu /opt/alfago-security

# Copy application files
echo "📋 Copying application files..."
cp -r . /opt/alfago-security/

# Create virtual environment
echo "🔧 Creating virtual environment..."
cd /opt/alfago-security
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Setup database
echo "🗄️ Setting up database..."
python setup_database.py

# Create systemd service file
echo "⚙️ Creating systemd service..."
sudo tee /etc/systemd/system/alfago-security.service > /dev/null <<EOF
[Unit]
Description=AlfaGrow Security Service
After=network.target

[Service]
Type=exec
User=ubuntu
Group=ubuntu
WorkingDirectory=/opt/alfago-security
Environment=PATH=/opt/alfago-security/venv/bin
ExecStart=/opt/alfago-security/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Configure Nginx
echo "🌐 Configuring Nginx..."
sudo tee /etc/nginx/sites-available/alfago-security > /dev/null <<EOF
server {
    listen 80;
    server_name alfago.in;

    location /alfagrow/security/ {
        proxy_pass http://127.0.0.1:8000/alfagrow/security/;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    location /health {
        proxy_pass http://127.0.0.1:8000/health;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    location /docs {
        proxy_pass http://127.0.0.1:8000/docs;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

# Enable Nginx site
sudo ln -sf /etc/nginx/sites-available/alfago-security /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Test Nginx configuration
sudo nginx -t

# Start and enable services
echo "🔄 Starting services..."
sudo systemctl daemon-reload
sudo systemctl enable alfago-security
sudo systemctl start alfago-security
sudo systemctl enable nginx
sudo systemctl restart nginx

# Check service status
echo "📊 Checking service status..."
sudo systemctl status alfago-security --no-pager
sudo systemctl status nginx --no-pager

# Create cron job for daily data fetch
echo "⏰ Setting up daily data fetch cron job..."
(crontab -l 2>/dev/null; echo "0 2 * * * cd /opt/alfago-security && source venv/bin/activate && python scripts/security_upsert.py >> /var/log/alfago-security-cron.log 2>&1") | crontab -

echo "✅ Deployment completed successfully!"
echo "🌐 Service available at: http://alfago.in/alfagrow/security/"
echo "📚 API docs available at: http://alfago.in/docs"
echo "❤️ Health check available at: http://alfago.in/health"
