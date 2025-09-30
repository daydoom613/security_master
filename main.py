"""
Main FastAPI application for AlfaGrow Security Service
"""
import logging
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config import settings
from core.database import test_connection, create_tables
from core.s3_client import s3_client
from api.v1.routes.security import router as security_router
from api.v1.schemas import HealthCheckResponse

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Security data management service for AlfaGrow",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(
    security_router,
    prefix="/alfagrow/security",
    tags=["security"]
)


@app.on_event("startup")
async def startup_event():
    """Application startup event"""
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    
    # Test database connection
    if test_connection():
        logger.info("Database connection successful")
        # Create tables if they don't exist
        create_tables()
    else:
        logger.error("Database connection failed")
        raise Exception("Failed to connect to database")
    
    # Test S3 connection
    if s3_client.test_connection():
        logger.info("S3 connection successful")
    else:
        logger.warning("S3 connection failed - some features may not work")


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event"""
    logger.info("Shutting down AlfaGrow Security Service")


@app.get("/", response_class=JSONResponse)
async def root():
    """Root endpoint"""
    return {
        "message": f"Welcome to {settings.app_name}",
        "version": settings.app_version,
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """Health check endpoint"""
    try:
        # Test database connection
        db_status = "healthy" if test_connection() else "unhealthy"
        
        # Test S3 connection
        s3_status = "healthy" if s3_client.test_connection() else "unhealthy"
        
        overall_status = "healthy" if db_status == "healthy" else "unhealthy"
        
        return HealthCheckResponse(
            status=overall_status,
            timestamp=datetime.utcnow(),
            version=settings.app_version,
            database_status=db_status,
            s3_status=s3_status
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return HealthCheckResponse(
            status="unhealthy",
            timestamp=datetime.utcnow(),
            version=settings.app_version,
            database_status="unknown",
            s3_status="unknown"
        )


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Custom HTTP exception handler"""
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.detail
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """General exception handler"""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": {
                "code": "internal_error",
                "message": "Internal server error",
                "details": {}
            }
        }
    )


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True,
        log_level=settings.log_level.lower()
    )
