# ABOUTME: FastAPI configuration settings using Pydantic settings management
# ABOUTME: Handles environment-specific configuration for the tennis booking API

from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    """Application settings"""
    
    # JWT Configuration
    jwt_secret_key: str = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24
    
    # API Configuration
    api_title: str = "Tennis Court Booking API"
    api_version: str = "1.0.0"
    debug: bool = False
    
    # Environment
    environment: str = os.getenv("TENNIS_ENVIRONMENT", "development")
    
    # Database
    dynamodb_endpoint: Optional[str] = os.getenv("DYNAMODB_ENDPOINT")
    aws_region: str = os.getenv("AWS_DEFAULT_REGION", "us-east-1")
    
    # Court Configuration
    court_availability_windows: dict = {
        "1": 10,  # Court 1: 10 days
        "2": 9    # Court 2: 9 days
    }
    
    # Tennis Site Configuration (for credential validation)
    tennis_site_url: str = os.getenv("TENNIS_WEBSITE_URL", "https://example.com")
    tennis_site_timeout: int = 30
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # Ignore extra fields from .env file

# Global settings instance
_settings = None

def get_settings() -> Settings:
    """Get application settings (singleton)"""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings