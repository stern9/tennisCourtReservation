# ABOUTME: UserConfig Pydantic model with validation for tennis booking user data
# ABOUTME: Handles username, password, email, and preferences validation

from typing import Optional, List, Dict, Any
from pydantic import Field, validator
from .base import DynamoDBModel, ValidationMixin
from .validators import (
    validate_username, validate_password, validate_email,
    validate_court_list, CourtValidator
)


class UserConfig(DynamoDBModel, ValidationMixin):
    """User configuration model with validation"""
    
    class Config(DynamoDBModel.Config):
        schema_extra = {
            "example": {
                "user_id": "user123",
                "username": "john_doe",
                "password": "SecurePass123",
                "email": "john@example.com",
                "first_name": "John",
                "last_name": "Doe",
                "preferred_courts": [1, 2],
                "preferred_times": ["De 08:00 AM a 09:00 AM", "De 09:00 AM a 10:00 AM"],
                "auto_book": True,
                "max_bookings_per_day": 2,
                "booking_advance_days": 7
            }
        }
    
    # Primary key
    user_id: str = Field(..., description="Unique user identifier", min_length=1, max_length=50)
    
    # Authentication credentials
    username: str = Field(..., description="Username for tennis booking system")
    password: str = Field(..., description="Password for tennis booking system")
    email: str = Field(..., description="User email address")
    
    # Personal information
    first_name: str = Field(..., description="User's first name", min_length=1, max_length=50)
    last_name: str = Field(..., description="User's last name", min_length=1, max_length=50)
    
    # Booking preferences
    preferred_courts: List[int] = Field(
        default_factory=lambda: CourtValidator.VALID_COURTS,
        description="List of preferred court IDs"
    )
    preferred_times: List[str] = Field(
        default_factory=list,
        description="List of preferred time slots"
    )
    
    # Booking behavior settings
    auto_book: bool = Field(default=True, description="Whether to automatically book available slots")
    max_bookings_per_day: int = Field(
        default=2, 
        description="Maximum number of bookings per day",
        ge=1, le=10
    )
    booking_advance_days: int = Field(
        default=7,
        description="How many days in advance to book",
        ge=1, le=30
    )
    
    # Optional settings
    phone_number: Optional[str] = Field(None, description="Phone number for notifications")
    notifications_enabled: bool = Field(default=True, description="Enable booking notifications")
    
    # Metadata
    is_active: bool = Field(default=True, description="Whether user account is active")
    last_login: Optional[str] = Field(None, description="Last login timestamp")
    
    # Validators
    @validator('username')
    def validate_username_field(cls, v):
        return validate_username(cls, v)
    
    @validator('password')
    def validate_password_field(cls, v):
        return validate_password(cls, v)
    
    @validator('email')
    def validate_email_field(cls, v):
        return validate_email(cls, v)
    
    @validator('preferred_courts')
    def validate_preferred_courts(cls, v):
        return validate_court_list(cls, v)
    
    @validator('preferred_times')
    def validate_preferred_times(cls, v):
        from .validators import validate_time_slot
        if not isinstance(v, list):
            raise ValueError("Preferred times must be a list")
        
        validated_times = []
        for time_slot in v:
            validated_times.append(validate_time_slot(cls, time_slot))
        
        return validated_times
    
    @validator('first_name', 'last_name')
    def validate_names(cls, v):
        if not isinstance(v, str):
            raise ValueError("Name must be a string")
        
        if len(v.strip()) == 0:
            raise ValueError("Name cannot be empty")
        
        if len(v) > 50:
            raise ValueError("Name cannot be longer than 50 characters")
        
        # Allow letters, spaces, hyphens, and apostrophes
        import re
        pattern = r"^[a-zA-Z\s'-]+$"
        if not re.match(pattern, v):
            raise ValueError("Name can only contain letters, spaces, hyphens, and apostrophes")
        
        return v.strip()
    
    @validator('phone_number')
    def validate_phone_number(cls, v):
        if v is None:
            return v
        
        if not isinstance(v, str):
            raise ValueError("Phone number must be a string")
        
        # Remove all non-digit characters
        digits_only = ''.join(filter(str.isdigit, v))
        
        if len(digits_only) < 10:
            raise ValueError("Phone number must have at least 10 digits")
        
        if len(digits_only) > 15:
            raise ValueError("Phone number cannot have more than 15 digits")
        
        return v
    
    @validator('user_id')
    def validate_user_id(cls, v):
        if not isinstance(v, str):
            raise ValueError("User ID must be a string")
        
        if len(v.strip()) == 0:
            raise ValueError("User ID cannot be empty")
        
        import re
        pattern = r'^[a-zA-Z0-9_-]+$'
        if not re.match(pattern, v):
            raise ValueError("User ID can only contain letters, numbers, underscores, and hyphens")
        
        return v.strip()
    
    def get_primary_key(self) -> Dict[str, Any]:
        """Get primary key for DynamoDB operations"""
        return {"user_id": self.user_id}
    
    def get_table_name(self) -> str:
        """Get DynamoDB table name"""
        return "UserConfigs"
    
    def get_display_name(self) -> str:
        """Get formatted display name"""
        return f"{self.first_name} {self.last_name}"
    
    def get_full_name(self) -> str:
        """Get full name with email"""
        return f"{self.get_display_name()} ({self.email})"
    
    def is_court_preferred(self, court_id: int) -> bool:
        """Check if court is in preferred list"""
        return court_id in self.preferred_courts
    
    def is_time_preferred(self, time_slot: str) -> bool:
        """Check if time slot is in preferred list"""
        return time_slot in self.preferred_times
    
    def can_book_more_today(self, current_bookings: int) -> bool:
        """Check if user can book more slots today"""
        return current_bookings < self.max_bookings_per_day
    
    def get_booking_preferences(self) -> Dict[str, Any]:
        """Get booking preferences as dictionary"""
        return {
            "preferred_courts": self.preferred_courts,
            "preferred_times": self.preferred_times,
            "auto_book": self.auto_book,
            "max_bookings_per_day": self.max_bookings_per_day,
            "booking_advance_days": self.booking_advance_days
        }
    
    def update_last_login(self) -> None:
        """Update last login timestamp"""
        from datetime import datetime
        self.last_login = datetime.utcnow().isoformat()
    
    def deactivate(self) -> None:
        """Deactivate user account"""
        self.is_active = False
    
    def activate(self) -> None:
        """Activate user account"""
        self.is_active = True