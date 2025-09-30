"""
Pydantic schemas for request/response validation
"""
from typing import Optional, List, Any
from pydantic import BaseModel, Field
from datetime import date, datetime


class SecurityBase(BaseModel):
    """Base security schema"""
    company_code: Optional[str] = None
    company_name: Optional[str] = None
    prowess_company_code: Optional[str] = None
    cin_code: Optional[str] = None
    isin_code: Optional[str] = None
    nse_symbol: Optional[str] = None
    bse_scrip_code: Optional[str] = None
    industry_group: Optional[str] = None
    main_product_service_group: Optional[str] = None
    company_website_address: Optional[str] = None
    registered_office_pincode: Optional[str] = None
    date_1: Optional[date] = None
    shares_outstanding_1: Optional[int] = None
    market_capitalisation_1: Optional[float] = None
    face_value_1: Optional[float] = None
    shares_traded_1: Optional[int] = None
    beta: Optional[float] = None
    date_2: Optional[date] = None
    shares_outstanding_2: Optional[int] = None
    market_capitalisation_2: Optional[float] = None
    face_value_2: Optional[float] = None
    shares_traded_2: Optional[int] = None


class SecurityCreate(SecurityBase):
    """Schema for creating a security"""
    isin_code: str = Field(..., description="ISIN code is required")


class SecurityUpdate(SecurityBase):
    """Schema for updating a security"""
    pass


class SecurityRead(SecurityBase):
    """Schema for reading a security"""
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class SecurityResponse(BaseModel):
    """Response schema for security operations"""
    success: bool
    message: str
    data: Optional[SecurityRead] = None


class SecurityListResponse(BaseModel):
    """Response schema for security list operations"""
    success: bool
    message: str
    data: List[SecurityRead]
    total_count: Optional[int] = None
    limit: Optional[int] = None
    offset: Optional[int] = None
    has_more: Optional[bool] = None


class ErrorResponse(BaseModel):
    """Error response schema"""
    success: bool = False
    error: dict = Field(..., description="Error details")
    
    class Config:
        schema_extra = {
            "example": {
                "success": False,
                "error": {
                    "code": "not_found",
                    "message": "Security not found",
                    "details": {
                        "identifier": "INFY",
                        "search_type": "nse_symbol"
                    }
                }
            }
        }


class HealthCheckResponse(BaseModel):
    """Health check response schema"""
    status: str
    timestamp: datetime
    version: str
    database_status: str
    s3_status: str


class UpsertRequest(BaseModel):
    """Request schema for bulk upsert operations"""
    securities: List[SecurityCreate] = Field(..., description="List of securities to upsert")


class UpsertResponse(BaseModel):
    """Response schema for bulk upsert operations"""
    success: bool
    message: str
    upserted_count: int
    failed_count: int
    errors: List[str] = []
