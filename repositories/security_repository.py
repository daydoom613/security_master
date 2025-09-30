"""
Security repository for database operations
"""
import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from models.security import SecurityModel
from core.exceptions import DatabaseError, SecurityNotFoundError

logger = logging.getLogger(__name__)


class SecurityRepository:
    """Repository for security database operations"""
    
    def __init__(self, db: Optional[Session] = None):
        self.db = db
    
    def _get_db_session(self) -> Session:
        """Get database session"""
        if self.db:
            return self.db
        from core.database import SessionLocal
        return SessionLocal()
    
    def upsert_security(self, security_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Insert or update security data
        
        Args:
            security_data: Dictionary containing security information
            
        Returns:
            Dictionary containing the upserted security data
        """
        db = self._get_db_session()
        try:
            # Check if security exists by ISIN code
            isin_code = security_data.get('isin_code')
            existing_security = None
            
            if isin_code:
                existing_security = db.query(SecurityModel).filter(
                    SecurityModel.isin_code == isin_code
                ).first()
            
            if existing_security:
                # Update existing security
                for key, value in security_data.items():
                    if hasattr(existing_security, key) and value is not None:
                        setattr(existing_security, key, value)
                
                db.commit()
                db.refresh(existing_security)
                logger.info(f"Updated security with ISIN: {isin_code}")
                return self._model_to_dict(existing_security)
            else:
                # Insert new security
                new_security = SecurityModel(**security_data)
                db.add(new_security)
                db.commit()
                db.refresh(new_security)
                logger.info(f"Inserted new security with ISIN: {isin_code}")
                return self._model_to_dict(new_security)
                
        except Exception as e:
            db.rollback()
            logger.error(f"Error upserting security: {e}")
            raise DatabaseError(f"Failed to upsert security: {str(e)}", "upsert")
        finally:
            if not self.db:  # Only close if we created the session
                db.close()
    
    def get_security_by_isin(self, isin_code: str) -> Optional[Dict[str, Any]]:
        """
        Get security by ISIN code
        
        Args:
            isin_code: ISIN code to search for
            
        Returns:
            Dictionary containing security data or None if not found
        """
        db = self._get_db_session()
        try:
            security = db.query(SecurityModel).filter(
                SecurityModel.isin_code == isin_code
            ).first()
            
            if security:
                return self._model_to_dict(security)
            return None
            
        except Exception as e:
            logger.error(f"Error getting security by ISIN: {e}")
            raise DatabaseError(f"Failed to get security by ISIN: {str(e)}", "get_by_isin")
        finally:
            if not self.db:
                db.close()
    
    def get_security_by_nse_symbol(self, nse_symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get security by NSE symbol
        
        Args:
            nse_symbol: NSE symbol to search for
            
        Returns:
            Dictionary containing security data or None if not found
        """
        db = self._get_db_session()
        try:
            security = db.query(SecurityModel).filter(
                func.upper(SecurityModel.nse_symbol) == nse_symbol.upper()
            ).first()
            
            if security:
                return self._model_to_dict(security)
            return None
            
        except Exception as e:
            logger.error(f"Error getting security by NSE symbol: {e}")
            raise DatabaseError(f"Failed to get security by NSE symbol: {str(e)}", "get_by_nse")
        finally:
            if not self.db:
                db.close()
    
    def get_security_by_bse_code(self, bse_code: str) -> Optional[Dict[str, Any]]:
        """
        Get security by BSE scrip code
        
        Args:
            bse_code: BSE scrip code to search for
            
        Returns:
            Dictionary containing security data or None if not found
        """
        db = self._get_db_session()
        try:
            security = db.query(SecurityModel).filter(
                SecurityModel.bse_scrip_code == bse_code
            ).first()
            
            if security:
                return self._model_to_dict(security)
            return None
            
        except Exception as e:
            logger.error(f"Error getting security by BSE code: {e}")
            raise DatabaseError(f"Failed to get security by BSE code: {str(e)}", "get_by_bse")
        finally:
            if not self.db:
                db.close()
    
    def search_securities_by_company_name(self, company_name: str) -> List[Dict[str, Any]]:
        """
        Search securities by company name (partial matching, case-insensitive)
        
        Args:
            company_name: Company name to search for
            
        Returns:
            List of dictionaries containing matching security data
        """
        db = self._get_db_session()
        try:
            # Remove quotes if present
            search_name = company_name.strip('"\'')
            
            securities = db.query(SecurityModel).filter(
                func.upper(SecurityModel.company_name).contains(search_name.upper())
            ).all()
            
            return [self._model_to_dict(security) for security in securities]
            
        except Exception as e:
            logger.error(f"Error searching securities by company name: {e}")
            raise DatabaseError(f"Failed to search securities by company name: {str(e)}", "search_by_name")
        finally:
            if not self.db:
                db.close()
    
    def get_securities_by_industry(self, industry: str) -> List[Dict[str, Any]]:
        """
        Get securities by industry (partial matching, case-insensitive)
        
        Args:
            industry: Industry name to search for
            
        Returns:
            List of dictionaries containing matching security data
        """
        db = self._get_db_session()
        try:
            securities = db.query(SecurityModel).filter(
                func.upper(SecurityModel.industry_group).contains(industry.upper())
            ).all()
            
            return [self._model_to_dict(security) for security in securities]
            
        except Exception as e:
            logger.error(f"Error getting securities by industry: {e}")
            raise DatabaseError(f"Failed to get securities by industry: {str(e)}", "get_by_industry")
        finally:
            if not self.db:
                db.close()
    
    def get_securities(self, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Get securities with multiple filters
        
        Args:
            filters: Dictionary containing filter criteria
            
        Returns:
            List of dictionaries containing security data
        """
        db = self._get_db_session()
        try:
            query = db.query(SecurityModel)
            
            # Apply filters
            for key, value in filters.items():
                if hasattr(SecurityModel, key) and value is not None:
                    if isinstance(value, str):
                        # Case-insensitive partial matching for string fields
                        query = query.filter(
                            func.upper(getattr(SecurityModel, key)).contains(value.upper())
                        )
                    else:
                        query = query.filter(getattr(SecurityModel, key) == value)
            
            securities = query.all()
            return [self._model_to_dict(security) for security in securities]
            
        except Exception as e:
            logger.error(f"Error getting securities with filters: {e}")
            raise DatabaseError(f"Failed to get securities: {str(e)}", "get_securities")
        finally:
            if not self.db:
                db.close()
    
    def _model_to_dict(self, security: SecurityModel) -> Dict[str, Any]:
        """
        Convert SecurityModel to dictionary
        
        Args:
            security: SecurityModel instance
            
        Returns:
            Dictionary representation of the security
        """
        result = {}
        for column in security.__table__.columns:
            value = getattr(security, column.name)
            if value is not None:
                # Convert datetime objects to ISO format strings
                if hasattr(value, 'isoformat'):
                    result[column.name] = value.isoformat()
                else:
                    result[column.name] = value
            else:
                result[column.name] = None
        return result
    
    def get_all_securities(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Get all securities with pagination
        
        Args:
            limit: Maximum number of records to return
            offset: Number of records to skip
            
        Returns:
            List of dictionaries containing security data
        """
        db = self._get_db_session()
        try:
            securities = db.query(SecurityModel).offset(offset).limit(limit).all()
            return [self._model_to_dict(security) for security in securities]
            
        except Exception as e:
            logger.error(f"Error getting all securities: {e}")
            raise DatabaseError(f"Failed to get all securities: {str(e)}", "get_all")
        finally:
            if not self.db:
                db.close()
    
    def count_securities(self) -> int:
        """
        Get total count of securities
        
        Returns:
            Total number of securities in the database
        """
        db = self._get_db_session()
        try:
            count = db.query(SecurityModel).count()
            return count
            
        except Exception as e:
            logger.error(f"Error counting securities: {e}")
            raise DatabaseError(f"Failed to count securities: {str(e)}", "count")
        finally:
            if not self.db:
                db.close()
