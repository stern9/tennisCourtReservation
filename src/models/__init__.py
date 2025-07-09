# ABOUTME: Models package for Pydantic data validation and business logic
# ABOUTME: Contains UserConfig, BookingRequest, SystemConfig models with validation

from .base import DynamoDBModel, TimestampedModel, ValidationMixin
from .user_config import UserConfig
from .encrypted_user_config import EncryptedUserConfig
from .booking_request import BookingRequest, BookingStatus, BookingPriority
from .system_config import SystemConfig, ConfigCategory, ConfigValueType, DEFAULT_SYSTEM_CONFIGS
from .validators import (
    ValidationError,
    DateValidator,
    TimeValidator,
    CourtValidator,
    CredentialValidator,
    EmailValidator
)

__all__ = [
    # Base classes
    'DynamoDBModel',
    'TimestampedModel',
    'ValidationMixin',
    
    # Models
    'UserConfig',
    'EncryptedUserConfig',
    'BookingRequest',
    'SystemConfig',
    
    # Enums
    'BookingStatus',
    'BookingPriority',
    'ConfigCategory',
    'ConfigValueType',
    
    # Validators
    'ValidationError',
    'DateValidator',
    'TimeValidator',
    'CourtValidator',
    'CredentialValidator',
    'EmailValidator',
    
    # Constants
    'DEFAULT_SYSTEM_CONFIGS'
]