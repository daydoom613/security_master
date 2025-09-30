"""
Security API routes
"""
import logging
from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException, Query, Path
from fastapi.responses import JSONResponse

from services.security_service import SecurityService
from api.v1.schemas import (
    SecurityResponse, SecurityListResponse, ErrorResponse,
    SecurityRead, UpsertRequest, UpsertResponse
)
from core.exceptions import SecurityNotFoundError, InvalidInputError

logger = logging.getLogger(__name__)

router = APIRouter()
security_service = SecurityService()


@router.get("/get/{identifier}", response_model=SecurityResponse)
async def get_security_by_identifier(
    identifier: str = Path(..., description="Security identifier (ISIN, NSE symbol, or BSE code)")
):
    """
    Get security by identifier (ISIN, NSE symbol, or BSE code)
    
    Examples:
    - /alfagrow/security/get/infy (NSE symbol)
    - /alfagrow/security/get/500209 (BSE code)
    - /alfagrow/security/get/INE009A01021 (ISIN code)
    """
    try:
        security_data = security_service.get_security_by_identifier(identifier)
        
        return SecurityResponse(
            success=True,
            message="Security found successfully",
            data=SecurityRead(**security_data)
        )
        
    except SecurityNotFoundError as e:
        logger.warning(f"Security not found: {identifier}")
        raise HTTPException(
            status_code=404,
            detail={
                "success": False,
                "error": {
                    "code": "not_found",
                    "message": e.message,
                    "details": e.details
                }
            }
        )
    
    except InvalidInputError as e:
        logger.warning(f"Invalid input: {identifier}")
        raise HTTPException(
            status_code=400,
            detail={
                "success": False,
                "error": {
                    "code": "invalid_input",
                    "message": e.message,
                    "details": e.details
                }
            }
        )
    
    except Exception as e:
        logger.error(f"Unexpected error getting security {identifier}: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": {
                    "code": "internal_error",
                    "message": "Internal server error",
                    "details": {"identifier": identifier}
                }
            }
        )


@router.get("/get/company/{company_name}", response_model=SecurityListResponse)
async def get_security_by_company_name(
    company_name: str = Path(..., description="Company name to search for")
):
    """
    Get securities by company name (partial matching)
    
    Example:
    - /alfagrow/security/get/company/infosys
    """
    try:
        securities = security_service.get_security_by_company_name(company_name)
        
        return SecurityListResponse(
            success=True,
            message=f"Found {len(securities)} securities for company name: {company_name}",
            data=[SecurityRead(**security) for security in securities]
        )
        
    except SecurityNotFoundError as e:
        logger.warning(f"No securities found for company name: {company_name}")
        raise HTTPException(
            status_code=404,
            detail={
                "success": False,
                "error": {
                    "code": "not_found",
                    "message": e.message,
                    "details": e.details
                }
            }
        )
    
    except InvalidInputError as e:
        logger.warning(f"Invalid company name: {company_name}")
        raise HTTPException(
            status_code=400,
            detail={
                "success": False,
                "error": {
                    "code": "invalid_input",
                    "message": e.message,
                    "details": e.details
                }
            }
        )
    
    except Exception as e:
        logger.error(f"Unexpected error getting securities by company name {company_name}: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": {
                    "code": "internal_error",
                    "message": "Internal server error",
                    "details": {"company_name": company_name}
                }
            }
        )


@router.get("/get/industry/{industry}", response_model=SecurityListResponse)
async def get_securities_by_industry(
    industry: str = Path(..., description="Industry name to search for")
):
    """
    Get securities by industry (partial matching)
    
    Example:
    - /alfagrow/security/get/industry/ITES
    """
    try:
        securities = security_service.get_securities_by_industry(industry)
        
        return SecurityListResponse(
            success=True,
            message=f"Found {len(securities)} securities in industry: {industry}",
            data=[SecurityRead(**security) for security in securities]
        )
        
    except SecurityNotFoundError as e:
        logger.warning(f"No securities found for industry: {industry}")
        raise HTTPException(
            status_code=404,
            detail={
                "success": False,
                "error": {
                    "code": "not_found",
                    "message": e.message,
                    "details": e.details
                }
            }
        )
    
    except InvalidInputError as e:
        logger.warning(f"Invalid industry: {industry}")
        raise HTTPException(
            status_code=400,
            detail={
                "success": False,
                "error": {
                    "code": "invalid_input",
                    "message": e.message,
                    "details": e.details
                }
            }
        )
    
    except Exception as e:
        logger.error(f"Unexpected error getting securities by industry {industry}: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": {
                    "code": "internal_error",
                    "message": "Internal server error",
                    "details": {"industry": industry}
                }
            }
        )


@router.get("/search", response_model=SecurityListResponse)
async def search_securities(
    q: str = Query(..., description="Search term"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of results")
):
    """
    Search securities by multiple criteria
    
    Example:
    - /alfagrow/security/search?q=infosys&limit=50
    """
    try:
        securities = security_service.search_securities(q)
        
        # Apply limit
        if len(securities) > limit:
            securities = securities[:limit]
        
        return SecurityListResponse(
            success=True,
            message=f"Found {len(securities)} securities for search term: {q}",
            data=[SecurityRead(**security) for security in securities]
        )
        
    except InvalidInputError as e:
        logger.warning(f"Invalid search term: {q}")
        raise HTTPException(
            status_code=400,
            detail={
                "success": False,
                "error": {
                    "code": "invalid_input",
                    "message": e.message,
                    "details": e.details
                }
            }
        )
    
    except Exception as e:
        logger.error(f"Unexpected error searching securities with term {q}: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": {
                    "code": "internal_error",
                    "message": "Internal server error",
                    "details": {"search_term": q}
                }
            }
        )


@router.get("/list", response_model=SecurityListResponse)
async def list_securities(
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Number of results to skip")
):
    """
    List all securities with pagination
    
    Example:
    - /alfagrow/security/list?limit=50&offset=100
    """
    try:
        result = security_service.get_all_securities(limit, offset)
        
        return SecurityListResponse(
            success=True,
            message=f"Retrieved {len(result['securities'])} securities",
            data=[SecurityRead(**security) for security in result['securities']],
            total_count=result['total_count'],
            limit=result['limit'],
            offset=result['offset'],
            has_more=result['has_more']
        )
        
    except Exception as e:
        logger.error(f"Unexpected error listing securities: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": {
                    "code": "internal_error",
                    "message": "Internal server error"
                }
            }
        )


@router.post("/upsert", response_model=SecurityResponse)
async def upsert_security(security_data: dict):
    """
    Upsert a single security
    
    Example:
    POST /alfagrow/security/upsert
    {
        "isin_code": "INE009A01021",
        "company_name": "Infosys Limited",
        "nse_symbol": "INFY",
        ...
    }
    """
    try:
        result = security_service.upsert_security(security_data)
        
        return SecurityResponse(
            success=True,
            message="Security upserted successfully",
            data=SecurityRead(**result)
        )
        
    except InvalidInputError as e:
        logger.warning(f"Invalid security data: {e}")
        raise HTTPException(
            status_code=400,
            detail={
                "success": False,
                "error": {
                    "code": "invalid_input",
                    "message": e.message,
                    "details": e.details
                }
            }
        )
    
    except Exception as e:
        logger.error(f"Unexpected error upserting security: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": {
                    "code": "internal_error",
                    "message": "Internal server error"
                }
            }
        )


@router.post("/bulk-upsert", response_model=UpsertResponse)
async def bulk_upsert_securities(request: UpsertRequest):
    """
    Bulk upsert multiple securities
    
    Example:
    POST /alfagrow/security/bulk-upsert
    {
        "securities": [
            {
                "isin_code": "INE009A01021",
                "company_name": "Infosys Limited",
                ...
            },
            ...
        ]
    }
    """
    try:
        upserted_count = 0
        failed_count = 0
        errors = []
        
        for security_data in request.securities:
            try:
                security_service.upsert_security(security_data.dict())
                upserted_count += 1
            except Exception as e:
                failed_count += 1
                errors.append(f"Failed to upsert {security_data.isin_code}: {str(e)}")
        
        return UpsertResponse(
            success=True,
            message=f"Bulk upsert completed: {upserted_count} successful, {failed_count} failed",
            upserted_count=upserted_count,
            failed_count=failed_count,
            errors=errors
        )
        
    except Exception as e:
        logger.error(f"Unexpected error in bulk upsert: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": {
                    "code": "internal_error",
                    "message": "Internal server error"
                }
            }
        )
