"""
Security upsert script - Fetches data from Prowess and upserts to PostgreSQL
"""
import os
import sys
import json
import time
import logging
import requests
import zipfile
from datetime import datetime
from typing import Dict, Any, List

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import settings
from core.s3_client import s3_client
from core.exceptions import ProwessAPIError, S3Error
from services.abbreviation_service import AbbreviationService

logger = logging.getLogger(__name__)


class ProwessDataFetcher:
    """Fetches data from Prowess API"""
    
    def __init__(self):
        self.api_key = settings.prowess_api_key
        self.batch_file = settings.prowess_batch_file
        self.session = requests.Session()
        self.poll_interval = 30  # seconds
        self.max_wait_minutes = 30
    
    def send_batch(self, output_format: str = "json") -> Dict[str, Any]:
        """
        Send batch file to Prowess API
        
        Args:
            output_format: Output format (json, txt, or None)
            
        Returns:
            Dictionary containing response data
        """
        try:
            url = 'https://prowess.cmie.com/api/sendbatch'
            data = {'apikey': self.api_key}
            
            if output_format:
                data['format'] = output_format
            
            if not os.path.isfile(self.batch_file):
                raise ProwessAPIError(f"Batch file not found: {self.batch_file}", "send_batch")
            
            with open(self.batch_file, 'rb') as f:
                files = {'batchfile': f}
                response = self.session.post(url, data=data, files=files, timeout=60)
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            raise ProwessAPIError(f"Failed to send batch: {str(e)}", "send_batch")
        except Exception as e:
            raise ProwessAPIError(f"Unexpected error sending batch: {str(e)}", "send_batch")
    
    def get_batch(self, token: str) -> requests.Response:
        """
        Get batch results from Prowess API
        
        Args:
            token: Batch token
            
        Returns:
            Response object
        """
        try:
            url = 'https://prowess.cmie.com/api/getbatch'
            data = {'apikey': self.api_key, 'token': token}
            response = self.session.post(url, data=data, timeout=60)
            response.raise_for_status()
            return response
            
        except requests.exceptions.RequestException as e:
            raise ProwessAPIError(f"Failed to get batch: {str(e)}", "get_batch")
        except Exception as e:
            raise ProwessAPIError(f"Unexpected error getting batch: {str(e)}", "get_batch")
    
    def is_zip_response(self, response: requests.Response) -> bool:
        """
        Check if response is a ZIP file
        
        Args:
            response: Response object
            
        Returns:
            True if response is ZIP, False otherwise
        """
        if response is None:
            return False
        
        content_type = response.headers.get('Content-Type', '').lower()
        content = response.content or b''
        
        # Check PK zip signature
        if len(content) >= 2 and content[:2] == b'PK':
            return True
        
        # Check content-type
        if 'application/zip' in content_type or 'application/octet-stream' in content_type:
            return True
        
        # If content starts with JSON markers -> definitely JSON
        head = content.lstrip()[:1]
        if head in (b'{', b'['):
            return False
        
        # Fallback: if content-type mentions json/text -> treat as JSON
        if 'json' in content_type or 'text' in content_type:
            return False
        
        # Otherwise assume non-json binary (likely the zip)
        return True
    
    def save_zip(self, response: requests.Response, zip_path: str):
        """
        Save ZIP response to file
        
        Args:
            response: Response object
            zip_path: Path to save ZIP file
        """
        try:
            with open(zip_path, 'wb') as f:
                f.write(response.content)
            logger.info(f"ZIP file saved: {zip_path}")
        except Exception as e:
            raise ProwessAPIError(f"Failed to save ZIP file: {str(e)}", "save_zip")
    
    def unzip_to_output(self, zip_path: str, output_dir: str = 'output', token: str = None) -> Dict[str, Any]:
        """
        Extract ZIP file to output directory
        
        Args:
            zip_path: Path to ZIP file
            output_dir: Output directory
            token: Token for expected file names
            
        Returns:
            Dictionary containing extraction info
        """
        try:
            os.makedirs(output_dir, exist_ok=True)
            
            with zipfile.ZipFile(zip_path, 'r') as z:
                z.extractall(output_dir)
            
            extracted = os.listdir(output_dir)
            expected_lst = f"{token}.lst" if token else None
            has_lst = expected_lst in extracted if expected_lst else None
            
            logger.info(f"Files extracted to {output_dir}: {extracted}")
            
            return {
                'extracted': extracted,
                'expected_lst': expected_lst,
                'has_lst': has_lst
            }
            
        except Exception as e:
            raise ProwessAPIError(f"Failed to extract ZIP file: {str(e)}", "unzip")
    
    def fetch_data(self) -> Dict[str, Any]:
        """
        Complete data fetching process from Prowess API
        
        Returns:
            Dictionary containing fetch results
        """
        try:
            # Step 1: Send batch
            logger.info("📤 Sending batch to Prowess API...")
            resp_json = self.send_batch(output_format="json")
            
            token = resp_json.get('token')
            if not token:
                raise ProwessAPIError("No token received from sendbatch", "send_batch")
            
            logger.info(f"✅ Received token: {token}")
            
            # Step 2: Poll for results
            zip_name = f"{token}.zip"
            max_attempts = max(1, int((self.max_wait_minutes * 60) / self.poll_interval))
            attempt = 0
            
            logger.info(f"⏱ Polling every {self.poll_interval}s for up to {self.max_wait_minutes} minutes")
            
            while attempt < max_attempts:
                attempt += 1
                logger.info(f"[{attempt}/{max_attempts}] Checking getbatch for token {token}...")
                
                try:
                    resp = self.get_batch(token)
                except Exception as e:
                    logger.warning(f"⚠️ get_batch request failed: {e}")
                    if attempt < max_attempts:
                        time.sleep(self.poll_interval)
                    continue
                
                # Check if response is ZIP
                if self.is_zip_response(resp):
                    logger.info("📥 ZIP stream detected — downloading...")
                    
                    # Save ZIP file
                    self.save_zip(resp, zip_name)
                    
                    # Extract files
                    info = self.unzip_to_output(zip_name, 'output', token=token)
                    
                    # Store raw file in S3
                    try:
                        raw_file_path = os.path.join('output', '1.json')
                        if os.path.exists(raw_file_path):
                            s3_client.store_raw_prowess_file(raw_file_path, token)
                            logger.info("✅ Raw file stored in S3")
                    except Exception as e:
                        logger.warning(f"⚠️ Failed to store raw file in S3: {e}")
                    
                    # Clean up ZIP file
                    try:
                        os.remove(zip_name)
                        logger.info(f"🗑️ Removed ZIP file: {zip_name}")
                    except Exception as e:
                        logger.warning(f"⚠️ Could not remove ZIP: {e}")
                    
                    logger.info("🎯 Data fetch completed successfully")
                    return {
                        'success': True,
                        'token': token,
                        'extracted_files': info['extracted'],
                        'output_dir': 'output'
                    }
                
                # Otherwise it's a JSON status response
                try:
                    j = resp.json()
                    msg = j.get('message') or j.get('errdesc') or j
                    logger.info(f"Status: {msg}")
                except Exception:
                    logger.info("Received non-zip, non-json response. Skipping.")
                
                # Wait before next attempt
                if attempt < max_attempts:
                    time.sleep(self.poll_interval)
            
            # Timed out
            raise ProwessAPIError(f"Timed out after {self.max_wait_minutes} minutes", "fetch_data")
            
        except Exception as e:
            logger.error(f"❌ Error fetching data from Prowess: {e}")
            raise


class SecurityUpsertProcessor:
    """Processes and upserts security data"""
    
    def __init__(self):
        self.abbreviation_service = AbbreviationService()
    
    def process_prowess_data(self, json_file_path: str) -> List[Dict[str, Any]]:
        """
        Process Prowess JSON data and prepare for upsert
        
        Args:
            json_file_path: Path to Prowess JSON file
            
        Returns:
            List of processed security data
        """
        try:
            with open(json_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Extract headers and rows
            headers = data["head"][-1]
            rows = data["data"]
            
            # Convert to list of dicts
            data_list = [dict(zip(headers, row)) for row in rows]
            
            # Filter only listed companies (with NSE or BSE codes)
            listed_data = []
            for row in data_list:
                nse_code = row.get('NSE symbol', '')
                bse_code = row.get('BSE scrip code', '')
                if nse_code.strip() or bse_code.strip():
                    listed_data.append(row)
            
            logger.info(f"Filtered {len(listed_data)} listed companies from {len(data_list)} total companies")
            
            # Process company names with abbreviation expansion
            company_names = [row.get('Company Name', '') for row in listed_data if row.get('Company Name')]
            logger.info(f"Expanding abbreviations for {len(company_names)} company names...")
            
            expanded_names = self.abbreviation_service.expand_abbreviations_in_names(company_names)
            
            # Update company names with expanded versions
            for row in listed_data:
                original_name = row.get('Company Name', '')
                if original_name in expanded_names:
                    row['Company Name'] = expanded_names[original_name]
            
            # Map duplicate columns to unique names (as in MVP)
            processed_data = []
            for row in listed_data:
                processed_row = {}
                
                # Map all fields
                for key, value in row.items():
                    # Handle duplicate columns
                    if key == "Date":
                        processed_row["date_1"] = value
                    elif key == "Shares Outstanding":
                        processed_row["shares_outstanding_1"] = value
                    elif key == "Market Capitalisation":
                        processed_row["market_capitalisation_1"] = value
                    elif key == "Face Value":
                        processed_row["face_value_1"] = value
                    elif key == "Shares traded":
                        processed_row["shares_traded_1"] = value
                    else:
                        # Map other fields to snake_case
                        snake_key = key.lower().replace(' ', '_').replace('/', '_')
                        processed_row[snake_key] = value
                
                # Add duplicate columns with _2 suffix
                processed_row["date_2"] = row.get("Date")
                processed_row["shares_outstanding_2"] = row.get("Shares Outstanding")
                processed_row["market_capitalisation_2"] = row.get("Market Capitalisation")
                processed_row["face_value_2"] = row.get("Face Value")
                processed_row["shares_traded_2"] = row.get("Shares traded")
                
                processed_data.append(processed_row)
            
            logger.info(f"Processed {len(processed_data)} securities for upsert")
            return processed_data
            
        except Exception as e:
            logger.error(f"Error processing Prowess data: {e}")
            raise
    
    def upsert_to_database(self, securities_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Upsert securities data to database via API
        
        Args:
            securities_data: List of security data dictionaries
            
        Returns:
            Dictionary containing upsert results
        """
        try:
            # Import here to avoid circular imports
            from services.security_service import SecurityService
            
            security_service = SecurityService()
            upserted_count = 0
            failed_count = 0
            errors = []
            
            for security_data in securities_data:
                try:
                    security_service.upsert_security(security_data)
                    upserted_count += 1
                    
                    if upserted_count % 100 == 0:
                        logger.info(f"Upserted {upserted_count} securities...")
                        
                except Exception as e:
                    failed_count += 1
                    error_msg = f"Failed to upsert {security_data.get('isin_code', 'unknown')}: {str(e)}"
                    errors.append(error_msg)
                    logger.warning(error_msg)
            
            result = {
                'success': True,
                'upserted_count': upserted_count,
                'failed_count': failed_count,
                'total_processed': len(securities_data),
                'errors': errors
            }
            
            logger.info(f"Upsert completed: {upserted_count} successful, {failed_count} failed")
            return result
            
        except Exception as e:
            logger.error(f"Error upserting to database: {e}")
            raise


def main():
    """Main function to run the security upsert process"""
    try:
        logger.info("🚀 Starting security upsert process...")
        
        # Step 1: Fetch data from Prowess
        fetcher = ProwessDataFetcher()
        fetch_result = fetcher.fetch_data()
        
        if not fetch_result['success']:
            raise Exception("Failed to fetch data from Prowess")
        
        # Step 2: Process the data
        processor = SecurityUpsertProcessor()
        json_file_path = os.path.join(fetch_result['output_dir'], '1.json')
        
        if not os.path.exists(json_file_path):
            raise Exception(f"Processed JSON file not found: {json_file_path}")
        
        securities_data = processor.process_prowess_data(json_file_path)
        
        # Step 3: Upsert to database
        upsert_result = processor.upsert_to_database(securities_data)
        
        # Step 4: Log results to S3
        log_data = {
            'fetch_result': fetch_result,
            'upsert_result': upsert_result,
            'timestamp': datetime.utcnow().isoformat(),
            'total_securities_processed': len(securities_data)
        }
        
        s3_client.log_operation(
            operation='security_upsert',
            status='success' if upsert_result['success'] else 'partial_success',
            details=log_data
        )
        
        logger.info("✅ Security upsert process completed successfully")
        return upsert_result
        
    except Exception as e:
        logger.error(f"❌ Security upsert process failed: {e}")
        
        # Log error to S3
        try:
            s3_client.log_operation(
                operation='security_upsert',
                status='error',
                details={
                    'error': str(e),
                    'timestamp': datetime.utcnow().isoformat()
                }
            )
        except Exception as log_error:
            logger.error(f"Failed to log error to S3: {log_error}")
        
        raise


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        result = main()
        print(f"✅ Process completed successfully: {result}")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Process failed: {e}")
        sys.exit(1)
