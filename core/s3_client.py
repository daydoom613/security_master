"""
AWS S3 client for logging and file storage
"""
import json
import logging
from datetime import datetime
from typing import Optional, Dict, Any
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from config import get_s3_config

logger = logging.getLogger(__name__)


class S3Client:
    """S3 client for file operations and logging"""
    
    def __init__(self):
        self.config = get_s3_config()
        try:
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=self.config['aws_access_key_id'],
                aws_secret_access_key=self.config['aws_secret_access_key'],
                region_name=self.config['region_name']
            )
            self.bucket_name = self.config['bucket_name']
            logger.info("S3 client initialized successfully")
        except NoCredentialsError:
            logger.error("AWS credentials not found")
            raise
        except Exception as e:
            logger.error(f"Error initializing S3 client: {e}")
            raise
    
    def upload_file(self, file_path: str, s3_key: str) -> bool:
        """
        Upload a file to S3
        
        Args:
            file_path: Local file path
            s3_key: S3 object key
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.s3_client.upload_file(file_path, self.bucket_name, s3_key)
            logger.info(f"File uploaded successfully: {s3_key}")
            return True
        except ClientError as e:
            logger.error(f"Error uploading file {s3_key}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error uploading file {s3_key}: {e}")
            return False
    
    def upload_json(self, data: Dict[Any, Any], s3_key: str) -> bool:
        """
        Upload JSON data to S3
        
        Args:
            data: Dictionary to upload as JSON
            s3_key: S3 object key
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            json_data = json.dumps(data, indent=2, default=str)
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=json_data,
                ContentType='application/json'
            )
            logger.info(f"JSON data uploaded successfully: {s3_key}")
            return True
        except ClientError as e:
            logger.error(f"Error uploading JSON {s3_key}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error uploading JSON {s3_key}: {e}")
            return False
    
    def log_operation(self, operation: str, status: str, details: Dict[Any, Any]) -> bool:
        """
        Log an operation to S3
        
        Args:
            operation: Operation name (e.g., 'security_upsert')
            status: Operation status (e.g., 'success', 'error')
            details: Additional details
            
        Returns:
            bool: True if successful, False otherwise
        """
        timestamp = datetime.utcnow().isoformat()
        log_entry = {
            "timestamp": timestamp,
            "operation": operation,
            "status": status,
            "details": details
        }
        
        # Create log file key with date
        date_str = datetime.utcnow().strftime("%Y%m%d")
        s3_key = f"logs/{date_str}/{operation}_{timestamp.replace(':', '-')}.json"
        
        return self.upload_json(log_entry, s3_key)
    
    def store_raw_prowess_file(self, file_path: str, token: str) -> bool:
        """
        Store raw Prowess file in S3
        
        Args:
            file_path: Local file path
            token: Prowess token for naming
            
        Returns:
            bool: True if successful, False otherwise
        """
        date_str = datetime.utcnow().strftime("%Y%m%d")
        s3_key = f"raw_data/{date_str}/prowess_rawdata_{token}.json"
        
        return self.upload_file(file_path, s3_key)
    
    def test_connection(self) -> bool:
        """
        Test S3 connection
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            logger.info("S3 connection test successful")
            return True
        except ClientError as e:
            logger.error(f"S3 connection test failed: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error testing S3 connection: {e}")
            return False


# Global S3 client instance
s3_client = S3Client()
