# AlfaGrow Security Service

A comprehensive security data management service that fetches, processes, and serves company security information from Prowess CMIE API.

## 🏗️ Architecture

The service follows a clean architecture pattern with the following components:

- **FastAPI**: RESTful API framework
- **PostgreSQL**: Primary database for security data
- **AWS S3**: Logging and raw data storage
- **Gemini AI**: Abbreviation expansion for company names

## 📁 Project Structure

```
app/
├── api/                    # API layer
│   └── v1/
│       ├── routes/         # API endpoints
│       └── schemas.py      # Request/response models
├── core/                   # Core functionality
│   ├── database.py         # Database connection
│   ├── s3_client.py        # AWS S3 integration
│   └── exceptions.py       # Custom exceptions
├── models/                 # Data models
│   └── security.py         # Security model and class
├── repositories/           # Data access layer
│   └── security_repository.py
├── services/               # Business logic
│   ├── security_service.py
│   └── abbreviation_service.py
├── scripts/                # Utility scripts
│   └── security_upsert.py  # Data fetch and upsert
├── tests/                  # Test files
├── migrations/             # Database migrations
├── main.py                 # FastAPI application
├── config.py               # Configuration management
└── requirements.txt        # Python dependencies
```

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- PostgreSQL 12+
- AWS S3 bucket
- Prowess CMIE API key
- Gemini AI API key

### Installation

1. **Clone and setup**:
   ```bash
   cd app
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Configure environment**:
   ```bash
   # Update config.py with your credentials
   # Database, AWS S3, Prowess API, Gemini AI
   ```

3. **Setup database**:
   ```bash
   python setup_database.py
   ```

4. **Run the service**:
   ```bash
   python main.py
   ```

## 🔧 Configuration

Update `config.py` with your credentials:

```python
# Database Configuration
db_host = "your-rds-endpoint"
db_user = "your-username"
db_password = "your-password"

# Prowess API
prowess_api_key = "your-prowess-api-key"

# AWS S3
aws_access_key_id = "your-access-key"
aws_secret_access_key = "your-secret-key"
aws_s3_bucket = "your-bucket-name"

# Gemini AI
gemini_api_key = "your-gemini-api-key"
```

## 📡 API Endpoints

### Get Security by Identifier
```http
GET /alfagrow/security/get/{identifier}
```

**Examples:**
- `GET /alfagrow/security/get/infy` (NSE symbol)
- `GET /alfagrow/security/get/500209` (BSE code)
- `GET /alfagrow/security/get/INE009A01021` (ISIN code)

### Get Securities by Company Name
```http
GET /alfagrow/security/get/company/{company_name}
```

**Example:**
- `GET /alfagrow/security/get/company/infosys`

### Get Securities by Industry
```http
GET /alfagrow/security/get/industry/{industry}
```

**Example:**
- `GET /alfagrow/security/get/industry/ITES`

### Search Securities
```http
GET /alfagrow/security/search?q={search_term}&limit={limit}
```

### List All Securities
```http
GET /alfagrow/security/list?limit={limit}&offset={offset}
```

### Upsert Security
```http
POST /alfagrow/security/upsert
Content-Type: application/json

{
  "isin_code": "INE009A01021",
  "company_name": "Infosys Limited",
  "nse_symbol": "INFY",
  ...
}
```

## 🔄 Data Processing Pipeline

1. **Daily Fetch**: Cron job runs `security_upsert.py` daily at 2 AM
2. **Prowess API**: Fetches latest security data from Prowess CMIE
3. **Data Processing**: 
   - Filters listed companies only
   - Expands abbreviations using Gemini AI
   - Handles duplicate columns
4. **Database Upsert**: Updates PostgreSQL with new data
5. **S3 Storage**: Stores raw files and logs operations

## 🧪 Testing

Run tests:
```bash
pytest tests/
```

## 🚀 Deployment

### EC2 Deployment

1. **Connect to EC2**:
   ```bash
   chmod 400 alfago-ec2-key-pair.pem
   ssh -i alfago-ec2-key-pair.pem ubuntu@3.111.246.81
   ```

2. **Run deployment script**:
   ```bash
   chmod +x deploy.sh
   ./deploy.sh
   ```

3. **Verify deployment**:
   ```bash
   curl http://alfago.in/health
   curl http://alfago.in/alfagrow/security/get/infy
   ```

### Manual Deployment

1. **Install dependencies**:
   ```bash
   sudo apt update
   sudo apt install python3 python3-pip nginx postgresql-client
   ```

2. **Setup application**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   python setup_database.py
   ```

3. **Configure Nginx**:
   ```bash
   sudo cp nginx.conf /etc/nginx/sites-available/alfago-security
   sudo ln -s /etc/nginx/sites-available/alfago-security /etc/nginx/sites-enabled/
   sudo systemctl restart nginx
   ```

4. **Start service**:
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8000
   ```

## 📊 Monitoring

- **Health Check**: `GET /health`
- **API Documentation**: `GET /docs`
- **Logs**: Check `/var/log/alfago-security-cron.log` for cron job logs
- **S3 Logs**: Check S3 bucket for operation logs

## 🔒 Security Considerations

- API endpoints are currently public (for development)
- Database credentials stored in configuration
- S3 bucket should have appropriate IAM policies
- Consider implementing API authentication for production

## 🛠️ Development

### Adding New Features

1. **Models**: Add new fields to `SecurityModel` in `models/security.py`
2. **Repository**: Add new methods to `SecurityRepository`
3. **Service**: Add business logic to `SecurityService`
4. **API**: Add new endpoints to `api/v1/routes/security.py`
5. **Tests**: Add test cases in `tests/`

### Database Migrations

1. Update `migrations/init_security_table.sql`
2. Run `python setup_database.py`

## 📝 Use Cases

### 1. Transaction Service
```python
# Get security ID by BSE symbol
response = requests.get("https://alfago.in/alfagrow/security/get/500209")
security_id = response.json()["data"]["isin_code"]
```

### 2. RSS Feed Processing
```python
# Get security ID by company name
response = requests.get("https://alfago.in/alfagrow/security/get/company/infosys")
security_id = response.json()["data"][0]["isin_code"]
```

### 3. Industry Analysis
```python
# Get all securities in energy sector
response = requests.get("https://alfago.in/alfagrow/security/get/industry/Energy")
securities = response.json()["data"]
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is proprietary to AlfaGrow Research.

## 🆘 Support

For support and questions, contact the development team.
