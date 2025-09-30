"""
Security service for business logic
"""
import logging
from typing import List, Dict, Any, Optional
from repositories.security_repository import SecurityRepository
from core.exceptions import SecurityNotFoundError, InvalidInputError

logger = logging.getLogger(__name__)


class SecurityService:
    """Service layer for security business logic"""
    
    def __init__(self):
        self.repository = SecurityRepository()
    
    def get_security_by_identifier(self, identifier: str) -> Dict[str, Any]:
        """
        Get security by various identifiers (ISIN, NSE symbol, BSE code)
        
        Args:
            identifier: Security identifier (ISIN, NSE symbol, or BSE code)
            
        Returns:
            Dictionary containing security data
            
        Raises:
            SecurityNotFoundError: If security is not found
            InvalidInputError: If input format is invalid
        """
        if not identifier or not identifier.strip():
            raise InvalidInputError("Identifier cannot be empty", "identifier")
        
        identifier = identifier.strip()
        
        # Try different search methods
        security = None
        
        # 1. Try ISIN code (format: INE followed by 10 alphanumeric characters)
        if len(identifier) == 12 and identifier.startswith('INE'):
            security = self.repository.get_security_by_isin(identifier)
            if security:
                return security
        
        # 2. Try NSE symbol (usually 3-20 characters, alphanumeric)
        if len(identifier) >= 3 and len(identifier) <= 20 and identifier.isalnum():
            security = self.repository.get_security_by_nse_symbol(identifier)
            if security:
                return security
        
        # 3. Try BSE code (usually 6 digits)
        if identifier.isdigit() and len(identifier) == 6:
            security = self.repository.get_security_by_bse_code(identifier)
            if security:
                return security
        
        # If no security found, raise exception
        raise SecurityNotFoundError(identifier, "identifier")
    
    def get_security_by_company_name(self, company_name: str) -> List[Dict[str, Any]]:
        """
        Get securities by company name (partial matching)
        
        Args:
            company_name: Company name to search for
            
        Returns:
            List of dictionaries containing matching security data
            
        Raises:
            InvalidInputError: If input format is invalid
            SecurityNotFoundError: If no securities found
        """
        if not company_name or not company_name.strip():
            raise InvalidInputError("Company name cannot be empty", "company_name")
        
        # Remove quotes if present
        company_name = company_name.strip('"\'')
        
        if len(company_name) < 2:
            raise InvalidInputError("Company name must be at least 2 characters long", "company_name")
        
        securities = self.repository.search_securities_by_company_name(company_name)
        
        if not securities:
            raise SecurityNotFoundError(company_name, "company_name")
        
        return securities
    
    def get_securities_by_industry(self, industry: str) -> List[Dict[str, Any]]:
        """
        Get securities by industry (partial matching)
        
        Args:
            industry: Industry name to search for
            
        Returns:
            List of dictionaries containing matching security data
            
        Raises:
            InvalidInputError: If input format is invalid
            SecurityNotFoundError: If no securities found
        """
        if not industry or not industry.strip():
            raise InvalidInputError("Industry cannot be empty", "industry")
        
        industry = industry.strip()
        
        if len(industry) < 2:
            raise InvalidInputError("Industry must be at least 2 characters long", "industry")
        
        securities = self.repository.get_securities_by_industry(industry)
        
        if not securities:
            raise SecurityNotFoundError(industry, "industry")
        
        return securities
    
    def upsert_security(self, security_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Upsert security data
        
        Args:
            security_data: Dictionary containing security information
            
        Returns:
            Dictionary containing the result of the upsert operation
        """
        try:
            result = self.repository.upsert_security(security_data)
            logger.info(f"Successfully upserted security: {security_data.get('isin_code', 'unknown')}")
            return result
        except Exception as e:
            logger.error(f"Error upserting security: {e}")
            raise
    
    def get_all_securities(self, limit: int = 100, offset: int = 0) -> Dict[str, Any]:
        """
        Get all securities with pagination
        
        Args:
            limit: Maximum number of records to return
            offset: Number of records to skip
            
        Returns:
            Dictionary containing securities and metadata
        """
        try:
            securities = self.repository.get_all_securities(limit, offset)
            total_count = self.repository.count_securities()
            
            return {
                "securities": securities,
                "total_count": total_count,
                "limit": limit,
                "offset": offset,
                "has_more": (offset + limit) < total_count
            }
        except Exception as e:
            logger.error(f"Error getting all securities: {e}")
            raise
    
    def search_securities(self, search_term: str) -> List[Dict[str, Any]]:
        """
        Search securities by multiple criteria
        
        Args:
            search_term: Search term to look for in various fields
            
        Returns:
            List of dictionaries containing matching security data
        """
        if not search_term or not search_term.strip():
            raise InvalidInputError("Search term cannot be empty", "search_term")
        
        search_term = search_term.strip()
        results = []
        
        try:
            # Search by company name
            try:
                company_results = self.repository.search_securities_by_company_name(search_term)
                results.extend(company_results)
            except:
                pass
            
            # Search by industry
            try:
                industry_results = self.repository.get_securities_by_industry(search_term)
                results.extend(industry_results)
            except:
                pass
            
            # Remove duplicates based on ISIN code
            seen_isins = set()
            unique_results = []
            for result in results:
                isin = result.get('isin_code')
                if isin and isin not in seen_isins:
                    seen_isins.add(isin)
                    unique_results.append(result)
            
            return unique_results
            
        except Exception as e:
            logger.error(f"Error searching securities: {e}")
            raise
    
    def validate_security_data(self, security_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate security data before upserting
        
        Args:
            security_data: Dictionary containing security information
            
        Returns:
            Dictionary containing validation results
            
        Raises:
            InvalidInputError: If validation fails
        """
        errors = []
        
        # Check required fields
        required_fields = ['isin_code']
        for field in required_fields:
            if not security_data.get(field):
                errors.append(f"Field '{field}' is required")
        
        # Validate ISIN format
        isin_code = security_data.get('isin_code')
        if isin_code and (len(isin_code) != 12 or not isin_code.startswith('INE')):
            errors.append("ISIN code must be 12 characters long and start with 'INE'")
        
        # Validate numeric fields
        numeric_fields = [
            'shares_outstanding_1', 'market_capitalisation_1', 'face_value_1',
            'shares_traded_1', 'beta', 'shares_outstanding_2',
            'market_capitalisation_2', 'face_value_2', 'shares_traded_2'
        ]
        
        for field in numeric_fields:
            value = security_data.get(field)
            if value is not None:
                try:
                    float(value)
                except (ValueError, TypeError):
                    errors.append(f"Field '{field}' must be a valid number")
        
        if errors:
            raise InvalidInputError(f"Validation failed: {'; '.join(errors)}")
        
        return {"valid": True, "message": "Security data is valid"}
