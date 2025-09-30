"""
Configuration management for AlfaGrow Security Service
"""
import os
from typing import Optional
from pydantic import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Database Configuration
    db_host: str = "alfa-quest-db.cxm860qwqttk.ap-south-1.rds.amazonaws.com"
    db_port: int = 5432
    db_name: str = "postgres"
    db_user: str = "alfaquestmaster"
    db_password: str = "here_password"
    
    # Prowess API
    prowess_api_key: str = "your_api_key_here"
    prowess_batch_file: str = "Security_Master_Test.bt"
    
    # AWS S3
    aws_access_key_id: str = "your_access_key"
    aws_secret_access_key: str = "your_secret_key"
    aws_s3_bucket: str = "alfago-security-logs"
    aws_region: str = "ap-south-1"
    
    # Application
    app_name: str = "AlfaGrow Security Service"
    app_version: str = "1.0.0"
    log_level: str = "INFO"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    
    # Gemini AI for abbreviation expansion
    gemini_api_key: str = "AIzaSyD7VA8KY9KpyiEOKMtqRAOmKeQVkVVd3SA"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()


def get_database_url() -> str:
    """Get PostgreSQL database URL"""
    return f"postgresql://{settings.db_user}:{settings.db_password}@{settings.db_host}:{settings.db_port}/{settings.db_name}"


def get_s3_config() -> dict:
    """Get S3 configuration"""
    return {
        "aws_access_key_id": settings.aws_access_key_id,
        "aws_secret_access_key": settings.aws_secret_access_key,
        "region_name": settings.aws_region,
        "bucket_name": settings.aws_s3_bucket
    }
