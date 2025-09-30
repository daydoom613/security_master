# 🚀 AlfaGrow Security Service - Deployment Guide

## 📋 Pre-Deployment Checklist

### 1. Update Configuration
Edit `config.py` with your actual credentials:

```python
# Database Configuration
db_host = "alfa-quest-db.cxm860qwqttk.ap-south-1.rds.amazonaws.com"
db_user = "alfaquestmaster"
db_password = "here_password"

# Prowess API
prowess_api_key = "YOUR_ACTUAL_PROWESS_API_KEY"

# AWS S3
aws_access_key_id = "YOUR_ACTUAL_AWS_ACCESS_KEY"
aws_secret_access_key = "YOUR_ACTUAL_AWS_SECRET_KEY"
aws_s3_bucket = "alfago-security-logs"  # Create this bucket in S3

# Gemini AI
gemini_api_key = "AIzaSyD7VA8KY9KpyiEOKMtqRAOmKeQVkVVd3SA"
```

### 2. Create S3 Bucket
```bash
# Create S3 bucket for logs and raw data
aws s3 mb s3://alfago-security-logs --region ap-south-1
```

## 🖥️ EC2 Deployment Steps

### Step 1: Connect to EC2
```bash
chmod 400 alfago-ec2-key-pair.pem
ssh -i alfago-ec2-key-pair.pem ubuntu@3.111.246.81
```

### Step 2: Upload Application
```bash
# From your local machine, upload the app folder
scp -i alfago-ec2-key-pair.pem -r app/ ubuntu@3.111.246.81:~/
```

### Step 3: Run Deployment Script
```bash
# On EC2 machine
cd app
chmod +x deploy.sh
./deploy.sh
```

### Step 4: Verify Deployment
```bash
# Check service status
sudo systemctl status alfago-security
sudo systemctl status nginx

# Test API endpoints
curl http://localhost:8000/health
curl http://localhost:8000/alfagrow/security/get/infy
```

## 🔧 Manual Deployment (Alternative)

If the automated script fails, follow these manual steps:

### 1. Install Dependencies
```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-venv postgresql-client nginx
```

### 2. Setup Application
```bash
cd app
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Setup Database
```bash
python setup_database.py
```

### 4. Configure Nginx
```bash
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

sudo ln -sf /etc/nginx/sites-available/alfago-security /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx
```

### 5. Create Systemd Service
```bash
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

sudo systemctl daemon-reload
sudo systemctl enable alfago-security
sudo systemctl start alfago-security
```

### 6. Setup Cron Job
```bash
# Add daily data fetch at 2 AM
(crontab -l 2>/dev/null; echo "0 2 * * * cd /opt/alfago-security && source venv/bin/activate && python scripts/security_upsert.py >> /var/log/alfago-security-cron.log 2>&1") | crontab -
```

## 🧪 Testing the Deployment

### 1. Health Check
```bash
curl http://alfago.in/health
```

Expected response:
```json
{
  "status": "healthy",
  "timestamp": "2025-01-23T10:50:00.000Z",
  "version": "1.0.0",
  "database_status": "healthy",
  "s3_status": "healthy"
}
```

### 2. API Endpoints Test
```bash
# Test NSE symbol lookup
curl http://alfago.in/alfagrow/security/get/infy

# Test BSE code lookup
curl http://alfago.in/alfagrow/security/get/500209

# Test company name search
curl http://alfago.in/alfagrow/security/get/company/infosys

# Test industry search
curl http://alfago.in/alfagrow/security/get/industry/ITES
```

### 3. Manual Data Fetch Test
```bash
cd /opt/alfago-security
source venv/bin/activate
python scripts/security_upsert.py
```

## 📊 Monitoring & Logs

### Service Logs
```bash
# Check service status
sudo systemctl status alfago-security

# View service logs
sudo journalctl -u alfago-security -f

# Check cron job logs
tail -f /var/log/alfago-security-cron.log
```

### Application Logs
```bash
# Check application logs
tail -f /opt/alfago-security/logs/app.log
```

### S3 Logs
Check your S3 bucket `alfago-security-logs` for:
- `logs/YYYYMMDD/` - Operation logs
- `raw_data/YYYYMMDD/` - Raw Prowess files

## 🔧 Troubleshooting

### Common Issues

1. **Database Connection Failed**
   ```bash
   # Test database connection
   psql -h alfa-quest-db.cxm860qwqttk.ap-south-1.rds.amazonaws.com -p 5432 -U alfaquestmaster -d postgres
   ```

2. **S3 Connection Failed**
   ```bash
   # Check AWS credentials
   aws s3 ls s3://alfago-security-logs
   ```

3. **Service Not Starting**
   ```bash
   # Check service logs
   sudo journalctl -u alfago-security -n 50
   
   # Restart service
   sudo systemctl restart alfago-security
   ```

4. **Nginx Issues**
   ```bash
   # Test Nginx configuration
   sudo nginx -t
   
   # Restart Nginx
   sudo systemctl restart nginx
   ```

### Performance Monitoring

```bash
# Check system resources
htop
df -h
free -h

# Check service performance
curl -w "@curl-format.txt" -o /dev/null -s http://alfago.in/health
```

## 🔄 Updates & Maintenance

### Update Application
```bash
# Stop service
sudo systemctl stop alfago-security

# Update code
cd /opt/alfago-security
git pull  # or upload new files

# Restart service
sudo systemctl start alfago-security
```

### Database Maintenance
```bash
# Backup database
pg_dump -h alfa-quest-db.cxm860qwqttk.ap-south-1.rds.amazonaws.com -U alfaquestmaster postgres > backup.sql

# Restore database
psql -h alfa-quest-db.cxm860qwqttk.ap-south-1.rds.amazonaws.com -U alfaquestmaster postgres < backup.sql
```

## 🎯 Production Checklist

- [ ] Update all API keys and credentials
- [ ] Create S3 bucket with proper permissions
- [ ] Test database connectivity
- [ ] Verify all API endpoints work
- [ ] Setup monitoring and alerting
- [ ] Configure SSL certificates (if needed)
- [ ] Setup backup procedures
- [ ] Test cron job execution
- [ ] Verify log rotation
- [ ] Setup security groups and firewall rules

## 📞 Support

For deployment issues:
1. Check logs first
2. Verify configuration
3. Test individual components
4. Contact development team

**Deployment completed successfully! 🎉**
