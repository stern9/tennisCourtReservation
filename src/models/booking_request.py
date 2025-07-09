# ABOUTME: BookingRequest Pydantic model with validation for tennis booking requests
# ABOUTME: Handles booking dates, times, courts, and status with business logic validation

from typing import Optional, Dict, Any
from enum import Enum
from pydantic import Field, validator
from .base import DynamoDBModel, ValidationMixin
from .validators import validate_date_format, validate_future_date, validate_time_slot, validate_court_id


class BookingStatus(str, Enum):
    """Booking request status enumeration"""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    FAILED = "failed"
    EXPIRED = "expired"


class BookingPriority(str, Enum):
    """Booking priority enumeration"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class BookingRequest(DynamoDBModel, ValidationMixin):
    """Booking request model with validation"""
    
    class Config(DynamoDBModel.Config):
        schema_extra = {
            "example": {
                "request_id": "req_123456",
                "user_id": "user123",
                "booking_date": "2025-07-15",
                "time_slot": "De 08:00 AM a 09:00 AM",
                "court_id": 1,
                "status": "pending",
                "priority": "medium",
                "auto_retry": True,
                "max_retries": 3,
                "retry_count": 0
            }
        }
    
    # Primary key
    request_id: str = Field(..., description="Unique request identifier", min_length=1, max_length=50)
    
    # User and booking details
    user_id: str = Field(..., description="User ID who made the request", min_length=1, max_length=50)
    booking_date: str = Field(..., description="Date for the booking (YYYY-MM-DD)")
    time_slot: str = Field(..., description="Time slot in format 'De HH:MM AM/PM a HH:MM AM/PM'")
    court_id: int = Field(..., description="Court ID to book")
    
    # Status and metadata
    status: BookingStatus = Field(default=BookingStatus.PENDING, description="Current booking status")
    priority: BookingPriority = Field(default=BookingPriority.MEDIUM, description="Booking priority")
    
    # Retry logic
    auto_retry: bool = Field(default=True, description="Whether to automatically retry failed bookings")
    max_retries: int = Field(default=3, description="Maximum number of retry attempts", ge=0, le=10)
    retry_count: int = Field(default=0, description="Current retry count", ge=0)
    
    # Optional fields
    notes: Optional[str] = Field(None, description="Additional notes for the booking", max_length=500)
    confirmation_code: Optional[str] = Field(None, description="Booking confirmation code")
    error_message: Optional[str] = Field(None, description="Error message if booking failed")
    
    # Timestamps
    requested_at: Optional[str] = Field(None, description="When the booking was requested")
    confirmed_at: Optional[str] = Field(None, description="When the booking was confirmed")
    expires_at: Optional[str] = Field(None, description="When the booking request expires")
    
    # External system references
    external_booking_id: Optional[str] = Field(None, description="ID from external booking system")
    
    # Validators
    @validator('booking_date')
    def validate_booking_date(cls, v):
        return validate_future_date(cls, v)
    
    @validator('time_slot')
    def validate_time_slot_field(cls, v):
        return validate_time_slot(cls, v)
    
    @validator('court_id')
    def validate_court_id_field(cls, v):
        return validate_court_id(cls, v)
    
    @validator('request_id')
    def validate_request_id(cls, v):
        if not isinstance(v, str):
            raise ValueError("Request ID must be a string")
        
        if len(v.strip()) == 0:
            raise ValueError("Request ID cannot be empty")
        
        import re
        pattern = r'^[a-zA-Z0-9_-]+$'
        if not re.match(pattern, v):
            raise ValueError("Request ID can only contain letters, numbers, underscores, and hyphens")
        
        return v.strip()
    
    @validator('user_id')
    def validate_user_id(cls, v):
        if not isinstance(v, str):
            raise ValueError("User ID must be a string")
        
        if len(v.strip()) == 0:
            raise ValueError("User ID cannot be empty")
        
        return v.strip()
    
    @validator('retry_count')
    def validate_retry_count(cls, v, values):
        if 'max_retries' in values and v > values['max_retries']:
            raise ValueError("Retry count cannot exceed max retries")
        return v
    
    @validator('notes')
    def validate_notes(cls, v):
        if v is None:
            return v
        
        if not isinstance(v, str):
            raise ValueError("Notes must be a string")
        
        if len(v.strip()) == 0:
            return None
        
        return v.strip()
    
    @validator('confirmation_code')
    def validate_confirmation_code(cls, v):
        if v is None:
            return v
        
        if not isinstance(v, str):
            raise ValueError("Confirmation code must be a string")
        
        if len(v.strip()) == 0:
            return None
        
        return v.strip()
    
    def get_primary_key(self) -> Dict[str, Any]:
        """Get primary key for DynamoDB operations"""
        return {"request_id": self.request_id}
    
    def get_table_name(self) -> str:
        """Get DynamoDB table name"""
        return "BookingRequests"
    
    def get_global_secondary_index_keys(self) -> Dict[str, Dict[str, Any]]:
        """Get GSI keys for different query patterns"""
        return {
            "UserIdIndex": {"user_id": self.user_id},
            "StatusIndex": {"status": self.status.value},
            "DateIndex": {"booking_date": self.booking_date}
        }
    
    def is_pending(self) -> bool:
        """Check if booking is pending"""
        return self.status == BookingStatus.PENDING
    
    def is_confirmed(self) -> bool:
        """Check if booking is confirmed"""
        return self.status == BookingStatus.CONFIRMED
    
    def is_cancelled(self) -> bool:
        """Check if booking is cancelled"""
        return self.status == BookingStatus.CANCELLED
    
    def is_failed(self) -> bool:
        """Check if booking failed"""
        return self.status == BookingStatus.FAILED
    
    def is_expired(self) -> bool:
        """Check if booking is expired"""
        return self.status == BookingStatus.EXPIRED
    
    def can_retry(self) -> bool:
        """Check if booking can be retried"""
        return (
            self.auto_retry and 
            self.retry_count < self.max_retries and 
            self.status in [BookingStatus.FAILED, BookingStatus.PENDING]
        )
    
    def increment_retry_count(self) -> None:
        """Increment retry count"""
        self.retry_count += 1
    
    def mark_as_confirmed(self, confirmation_code: str = None) -> None:
        """Mark booking as confirmed"""
        self.status = BookingStatus.CONFIRMED
        if confirmation_code:
            self.confirmation_code = confirmation_code
        
        from datetime import datetime
        self.confirmed_at = datetime.utcnow().isoformat()
    
    def mark_as_failed(self, error_message: str = None) -> None:
        """Mark booking as failed"""
        self.status = BookingStatus.FAILED
        if error_message:
            self.error_message = error_message
    
    def mark_as_cancelled(self) -> None:
        """Mark booking as cancelled"""
        self.status = BookingStatus.CANCELLED
    
    def mark_as_expired(self) -> None:
        """Mark booking as expired"""
        self.status = BookingStatus.EXPIRED
    
    def set_expiration(self, days: int = 1) -> None:
        """Set expiration date"""
        from datetime import datetime, timedelta
        expiration_date = datetime.utcnow() + timedelta(days=days)
        self.expires_at = expiration_date.isoformat()
    
    def is_expired_now(self) -> bool:
        """Check if booking has expired"""
        if not self.expires_at:
            return False
        
        from datetime import datetime
        try:
            expiration_date = datetime.fromisoformat(self.expires_at.replace('Z', '+00:00'))
            return datetime.utcnow() > expiration_date
        except ValueError:
            return False
    
    def get_booking_summary(self) -> str:
        """Get human-readable booking summary"""
        return f"Court {self.court_id} on {self.booking_date} at {self.time_slot}"
    
    def get_status_display(self) -> str:
        """Get formatted status display"""
        status_display = {
            BookingStatus.PENDING: "Pending",
            BookingStatus.CONFIRMED: "Confirmed",
            BookingStatus.CANCELLED: "Cancelled",
            BookingStatus.FAILED: "Failed",
            BookingStatus.EXPIRED: "Expired"
        }
        return status_display.get(self.status, str(self.status))
    
    def get_priority_display(self) -> str:
        """Get formatted priority display"""
        priority_display = {
            BookingPriority.LOW: "Low",
            BookingPriority.MEDIUM: "Medium",
            BookingPriority.HIGH: "High",
            BookingPriority.URGENT: "Urgent"
        }
        return priority_display.get(self.priority, str(self.priority))
    
    def to_dict_for_display(self) -> Dict[str, Any]:
        """Convert to dictionary for display purposes"""
        return {
            "request_id": self.request_id,
            "user_id": self.user_id,
            "booking_summary": self.get_booking_summary(),
            "status": self.get_status_display(),
            "priority": self.get_priority_display(),
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "confirmation_code": self.confirmation_code,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "confirmed_at": self.confirmed_at,
            "expires_at": self.expires_at
        }