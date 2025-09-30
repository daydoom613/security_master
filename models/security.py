"""
Security model and class with all table fields
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import Column, Integer, String, Date, Numeric, Text, DateTime
from sqlalchemy.sql import func
from core.database import Base


class SecurityModel(Base):
    """SQLAlchemy model for securities table"""
    
    __tablename__ = "securities"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Company information
    company_code = Column(String(50), nullable=True)
    company_name = Column(String(500), nullable=True)
    prowess_company_code = Column(String(50), nullable=True)
    cin_code = Column(String(50), nullable=True)
    isin_code = Column(String(50), unique=True, nullable=True, index=True)
    nse_symbol = Column(String(50), nullable=True, index=True)
    bse_scrip_code = Column(String(50), nullable=True, index=True)
    
    # Business information
    industry_group = Column(String(200), nullable=True, index=True)
    main_product_service_group = Column(String(200), nullable=True)
    company_website_address = Column(Text, nullable=True)
    registered_office_pincode = Column(String(10), nullable=True)
    
    # Financial data - First set
    date_1 = Column(Date, nullable=True)
    shares_outstanding_1 = Column(Numeric(20, 0), nullable=True)
    market_capitalisation_1 = Column(Numeric(20, 2), nullable=True)
    face_value_1 = Column(Numeric(10, 2), nullable=True)
    shares_traded_1 = Column(Numeric(20, 0), nullable=True)
    beta = Column(Numeric(10, 6), nullable=True)
    
    # Financial data - Second set (duplicate columns from MVP)
    date_2 = Column(Date, nullable=True)
    shares_outstanding_2 = Column(Numeric(20, 0), nullable=True)
    market_capitalisation_2 = Column(Numeric(20, 2), nullable=True)
    face_value_2 = Column(Numeric(10, 2), nullable=True)
    shares_traded_2 = Column(Numeric(20, 0), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=func.current_timestamp())
    updated_at = Column(DateTime, default=func.current_timestamp(), onupdate=func.current_timestamp())


class Security:
    """
    Security class with all table fields as class variables and methods
    """
    
    # Field constants matching the database columns
    COMPANY_CODE = "company_code"
    COMPANY_NAME = "company_name"
    PROWESS_COMPANY_CODE = "prowess_company_code"
    CIN_CODE = "cin_code"
    ISIN_CODE = "isin_code"
    NSE_SYMBOL = "nse_symbol"
    BSE_SCRIP_CODE = "bse_scrip_code"
    INDUSTRY_GROUP = "industry_group"
    MAIN_PRODUCT_SERVICE_GROUP = "main_product_service_group"
    COMPANY_WEBSITE_ADDRESS = "company_website_address"
    REGISTERED_OFFICE_PINCODE = "registered_office_pincode"
    DATE_1 = "date_1"
    SHARES_OUTSTANDING_1 = "shares_outstanding_1"
    MARKET_CAPITALISATION_1 = "market_capitalisation_1"
    FACE_VALUE_1 = "face_value_1"
    SHARES_TRADED_1 = "shares_traded_1"
    BETA = "beta"
    DATE_2 = "date_2"
    SHARES_OUTSTANDING_2 = "shares_outstanding_2"
    MARKET_CAPITALISATION_2 = "market_capitalisation_2"
    FACE_VALUE_2 = "face_value_2"
    SHARES_TRADED_2 = "shares_traded_2"
    
    # All field names as a list
    ALL_FIELDS = [
        COMPANY_CODE, COMPANY_NAME, PROWESS_COMPANY_CODE, CIN_CODE, ISIN_CODE,
        NSE_SYMBOL, BSE_SCRIP_CODE, INDUSTRY_GROUP, MAIN_PRODUCT_SERVICE_GROUP,
        COMPANY_WEBSITE_ADDRESS, REGISTERED_OFFICE_PINCODE, DATE_1,
        SHARES_OUTSTANDING_1, MARKET_CAPITALISATION_1, FACE_VALUE_1,
        SHARES_TRADED_1, BETA, DATE_2, SHARES_OUTSTANDING_2,
        MARKET_CAPITALISATION_2, FACE_VALUE_2, SHARES_TRADED_2
    ]
    
    @staticmethod
    def upsert(security_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Upsert security data into the database
        
        Args:
            security_data: Dictionary containing security information
            
        Returns:
            Dict containing the result of the upsert operation
        """
        from repositories.security_repository import SecurityRepository
        
        try:
            repository = SecurityRepository()
            result = repository.upsert_security(security_data)
            return {
                "success": True,
                "message": "Security upserted successfully",
                "data": result
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Error upserting security: {str(e)}",
                "data": None
            }
    
    @staticmethod
    def read(filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Read security data from the database with filters
        
        Args:
            filters: Dictionary containing filter criteria
            
        Returns:
            List of dictionaries containing security data
        """
        from repositories.security_repository import SecurityRepository
        
        try:
            repository = SecurityRepository()
            results = repository.get_securities(filters)
            return results
        except Exception as e:
            raise Exception(f"Error reading securities: {str(e)}")
    
    @staticmethod
    def get_by_isin(isin_code: str) -> Optional[Dict[str, Any]]:
        """
        Get security by ISIN code
        
        Args:
            isin_code: ISIN code to search for
            
        Returns:
            Dictionary containing security data or None if not found
        """
        from repositories.security_repository import SecurityRepository
        
        try:
            repository = SecurityRepository()
            result = repository.get_security_by_isin(isin_code)
            return result
        except Exception as e:
            raise Exception(f"Error getting security by ISIN: {str(e)}")
    
    @staticmethod
    def get_by_nse_symbol(nse_symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get security by NSE symbol
        
        Args:
            nse_symbol: NSE symbol to search for
            
        Returns:
            Dictionary containing security data or None if not found
        """
        from repositories.security_repository import SecurityRepository
        
        try:
            repository = SecurityRepository()
            result = repository.get_security_by_nse_symbol(nse_symbol)
            return result
        except Exception as e:
            raise Exception(f"Error getting security by NSE symbol: {str(e)}")
    
    @staticmethod
    def get_by_bse_code(bse_code: str) -> Optional[Dict[str, Any]]:
        """
        Get security by BSE scrip code
        
        Args:
            bse_code: BSE scrip code to search for
            
        Returns:
            Dictionary containing security data or None if not found
        """
        from repositories.security_repository import SecurityRepository
        
        try:
            repository = SecurityRepository()
            result = repository.get_security_by_bse_code(bse_code)
            return result
        except Exception as e:
            raise Exception(f"Error getting security by BSE code: {str(e)}")
    
    @staticmethod
    def search_by_company_name(company_name: str) -> List[Dict[str, Any]]:
        """
        Search securities by company name (partial matching)
        
        Args:
            company_name: Company name to search for
            
        Returns:
            List of dictionaries containing matching security data
        """
        from repositories.security_repository import SecurityRepository
        
        try:
            repository = SecurityRepository()
            results = repository.search_securities_by_company_name(company_name)
            return results
        except Exception as e:
            raise Exception(f"Error searching securities by company name: {str(e)}")
    
    @staticmethod
    def get_by_industry(industry: str) -> List[Dict[str, Any]]:
        """
        Get securities by industry (partial matching)
        
        Args:
            industry: Industry name to search for
            
        Returns:
            List of dictionaries containing matching security data
        """
        from repositories.security_repository import SecurityRepository
        
        try:
            repository = SecurityRepository()
            results = repository.get_securities_by_industry(industry)
            return results
        except Exception as e:
            raise Exception(f"Error getting securities by industry: {str(e)}")
