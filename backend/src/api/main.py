# ABOUTME: FastAPI main application entry point with middleware and routing
# ABOUTME: Configures authentication, CORS, and API endpoint routing for tennis booking system

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
from typing import Optional

from .auth import AuthService, get_current_user
from .routers import auth, users, bookings
from .models import ErrorResponse
from .config import get_settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Security
security = HTTPBearer()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    logger.info("Starting Tennis Booking API")
    yield
    logger.info("Shutting down Tennis Booking API")

# FastAPI app instance
app = FastAPI(
    title="Tennis Court Booking API",
    description="API for managing tennis court reservations with encrypted user data",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8080"],  # Frontend origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/auth", tags=["authentication"])
app.include_router(users.router, prefix="/users", tags=["users"])
app.include_router(bookings.router, prefix="/bookings", tags=["bookings"])

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Tennis Court Booking API",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    settings = get_settings()
    
    # Check database connectivity
    try:
        from ..database.connection import get_dynamodb_resource
        dynamodb = get_dynamodb_resource()
        # Simple connectivity test
        list(dynamodb.tables.limit(1))
        db_status = "healthy"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        db_status = "unhealthy"
    
    # Check encryption service
    try:
        from ..security import get_encryption_service
        encryption_service = get_encryption_service()
        encryption_health = encryption_service.health_check()
        encryption_status = encryption_health.get("status", "unknown")
    except Exception as e:
        logger.error(f"Encryption health check failed: {e}")
        encryption_status = "unhealthy"
    
    overall_status = "healthy" if db_status == "healthy" and encryption_status == "healthy" else "unhealthy"
    
    return {
        "status": overall_status,
        "database": db_status,
        "encryption": encryption_status,
        "environment": settings.environment
    }

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Custom HTTP exception handler"""
    return ErrorResponse(
        error=True,
        message=exc.detail,
        status_code=exc.status_code
    ).dict()

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """General exception handler"""
    logger.error(f"Unhandled exception: {exc}")
    return ErrorResponse(
        error=True,
        message="Internal server error",
        status_code=500
    ).dict()