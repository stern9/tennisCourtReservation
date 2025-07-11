# ABOUTME: Pydantic models for FastAPI request/response serialization
# ABOUTME: Defines API data structures for authentication, users, and booking operations

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from enum import Enum

# Error Response Models
class ErrorResponse(BaseModel):
    """Standard error response format"""
    error: bool = True
    message: str
    status_code: int
    details: Optional[Dict[str, Any]] = None

# Authentication Models
class LoginRequest(BaseModel):
    """User login request"""
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)

class LoginResponse(BaseModel):
    """User login response"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 86400  # 24 hours in seconds
    user_id: str

class TokenData(BaseModel):
    """JWT token data"""
    username: Optional[str] = None
    user_id: Optional[str] = None

# User Models
class UserProfile(BaseModel):
    """User profile information"""
    user_id: str
    username: str
    email: str
    first_name: str
    last_name: str
    is_active: bool = True
    preferred_courts: List[int] = []
    preferred_times: List[str] = []
    max_bookings_per_day: int = 1
    auto_booking_enabled: bool = False
    created_at: datetime
    updated_at: datetime

class UserConfigUpdate(BaseModel):
    """User configuration update request"""
    email: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    preferred_courts: Optional[List[int]] = None
    preferred_times: Optional[List[str]] = None
    max_bookings_per_day: Optional[int] = None
    auto_booking_enabled: Optional[bool] = None
    
    @validator('preferred_courts')
    def validate_preferred_courts(cls, v):
        if v is not None:
            valid_courts = [1, 2]  # Court 1 and Court 2
            for court in v:
                if court not in valid_courts:
                    raise ValueError(f"Invalid court number: {court}. Valid courts: {valid_courts}")
        return v

# Booking Models
class BookingStatus(str, Enum):
    """Booking status enumeration"""
    PENDING = "pending"
    PROCESSING = "processing"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    FAILED = "failed"
    EXPIRED = "expired"
    SCHEDULED = "scheduled"  # For future bookings

class BookingRequest(BaseModel):
    """Booking request from user"""
    court_id: int = Field(..., ge=1, le=2)  # Court 1 or 2
    booking_date: date = Field(..., description="Date in YYYY-MM-DD format")
    time_slot: str = Field(..., description="Time slot in format 'De HH:MM AM/PM a HH:MM AM/PM'")
    
    @validator('booking_date')
    def validate_future_date(cls, v):
        if v <= date.today():
            raise ValueError("Booking date must be in the future")
        return v
    
    @validator('time_slot')
    def validate_time_slot_format(cls, v):
        # Basic validation for time slot format
        if not v.startswith("De ") or " a " not in v:
            raise ValueError("Time slot must be in format 'De HH:MM AM/PM a HH:MM AM/PM'")
        return v

class BookingResponse(BaseModel):
    """Booking response"""
    booking_id: str
    user_id: str
    court_id: int
    booking_date: date
    time_slot: str
    status: BookingStatus
    message: str
    created_at: datetime
    updated_at: datetime
    scheduled_for: Optional[datetime] = None  # When booking will be attempted

class BookingListResponse(BaseModel):
    """List of bookings response"""
    bookings: List[BookingResponse]
    total: int
    page: int = 1
    per_page: int = 10

class BookingStatusUpdate(BaseModel):
    """Booking status update"""
    status: BookingStatus
    message: Optional[str] = None

# Court Availability Models
class CourtAvailability(BaseModel):
    """Court availability information"""
    court_id: int
    available_dates: List[date]
    booking_window_days: int
    next_available_date: Optional[date] = None

class AvailabilityResponse(BaseModel):
    """Court availability response"""
    courts: List[CourtAvailability]
    current_date: date

# Validation Models
class BookingValidation(BaseModel):
    """Booking validation result"""
    is_valid: bool
    is_available_now: bool
    is_schedulable: bool
    message: str
    available_at: Optional[datetime] = None  # When booking becomes available
    court_booking_window: int