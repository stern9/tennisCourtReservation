# ABOUTME: Booking service with court-specific availability validation and scheduling logic
# ABOUTME: Handles immediate vs scheduled bookings, court availability windows, and booking validation

from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, date, timedelta
import logging
import uuid

from ..models import (
    BookingRequest, BookingResponse, BookingStatus, BookingValidation,
    CourtAvailability, AvailabilityResponse
)
from ..config import get_settings
from ...dao import BookingRequestDAO, SystemConfigDAO, EncryptedUserConfigDAO
from ...models import BookingRequest as BookingRequestModel
from .scheduler_service import background_scheduler
from .tennis_booking_service import TennisBookingService

logger = logging.getLogger(__name__)

class BookingService:
    """Service for managing tennis court bookings with court-specific logic"""
    
    def __init__(self):
        self.settings = get_settings()
        self.booking_dao = BookingRequestDAO()
        self.system_config_dao = SystemConfigDAO()
        
        # Court-specific availability windows
        self.court_windows = self.settings.court_availability_windows
    
    def get_court_availability_window(self, court_id: int) -> int:
        """Get availability window for specific court"""
        return self.court_windows.get(str(court_id), 10)  # Default to 10 days
    
    def calculate_available_dates(self, court_id: int, from_date: date = None) -> List[date]:
        """Calculate available dates for a court based on its booking window"""
        if from_date is None:
            from_date = date.today()
        
        window_days = self.get_court_availability_window(court_id)
        available_dates = []
        
        for i in range(window_days):
            available_date = from_date + timedelta(days=i)
            available_dates.append(available_date)
        
        return available_dates
    
    def validate_booking_request(self, booking_request: BookingRequest, user_id: str = None) -> BookingValidation:
        """
        Validate booking request against court-specific availability rules
        
        Returns validation result with availability information
        """
        court_id = booking_request.court_id
        requested_date = booking_request.booking_date
        today = date.today()
        
        # Get court's booking window
        window_days = self.get_court_availability_window(court_id)
        
        # Calculate available dates for this court
        available_dates = self.calculate_available_dates(court_id, today)
        
        # Check if requested date is in the available window
        is_available_now = requested_date in available_dates
        
        # Check if date is schedulable (will be available at midnight)
        tomorrow = today + timedelta(days=1)
        future_available_dates = self.calculate_available_dates(court_id, tomorrow)
        is_schedulable = requested_date in future_available_dates and not is_available_now
        
        # Check for conflicts with existing bookings
        conflicts = self.booking_dao.get_booking_conflicts(
            court_id, 
            requested_date.isoformat(), 
            booking_request.time_slot
        )
        
        has_conflicts = len(conflicts) > 0
        
        # Check user permissions if user_id provided
        user_permission_valid = True
        user_permission_message = ""
        
        if user_id:
            # Check if user has exceeded daily booking limit
            user_bookings_today = self.booking_dao.get_user_bookings_for_date(
                user_id, 
                requested_date.isoformat()
            )
            
            # Default max bookings per day is 2
            max_bookings_per_day = 2
            if len(user_bookings_today) >= max_bookings_per_day:
                user_permission_valid = False
                user_permission_message = f"You have reached the maximum of {max_bookings_per_day} bookings per day"
        
        # Calculate when booking becomes available
        available_at = None
        if is_schedulable:
            # Calculate how many days ahead the booking becomes available
            days_ahead = (requested_date - today).days
            # If the booking is for tomorrow's availability window, it becomes available at midnight
            if days_ahead == window_days:
                available_at = datetime.combine(tomorrow, datetime.min.time())
        
        # Generate user-friendly message
        if not user_permission_valid:
            message = user_permission_message
        elif has_conflicts:
            message = f"Court {court_id} is already booked at {booking_request.time_slot} on {requested_date.strftime('%B %d, %Y')}"
        elif is_available_now:
            message = f"Court {court_id} is available for booking on {requested_date.strftime('%B %d, %Y')}"
        elif is_schedulable:
            available_date = available_at.strftime('%B %d, %Y')
            message = f"Court {court_id} bookings for {requested_date.strftime('%B %d, %Y')} aren't open yet. Don't worry — we've scheduled your request and will confirm once it's successfully reserved after midnight on {available_date}."
        else:
            message = f"Court {court_id} only allows bookings {window_days} days in advance. Please choose a date within the next {window_days} days."
        
        return BookingValidation(
            is_valid=(is_available_now or is_schedulable) and not has_conflicts and user_permission_valid,
            is_available_now=is_available_now,
            is_schedulable=is_schedulable,
            message=message,
            available_at=available_at,
            court_booking_window=window_days
        )
    
    def create_booking_request(self, booking_request: BookingRequest, user_id: str) -> BookingResponse:
        """
        Create a new booking request with validation
        
        Returns booking response with status and scheduling information
        """
        try:
            # Validate booking request with user context
            validation = self.validate_booking_request(booking_request, user_id)
            
            if not validation.is_valid:
                # Return failed booking with validation message
                return BookingResponse(
                    booking_id="",
                    user_id=user_id,
                    court_id=booking_request.court_id,
                    booking_date=booking_request.booking_date,
                    time_slot=booking_request.time_slot,
                    status=BookingStatus.FAILED,
                    message=validation.message,
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
            
            # Generate booking ID
            booking_id = str(uuid.uuid4())
            
            # Determine booking status
            if validation.is_available_now:
                # Booking can be made immediately
                status = BookingStatus.PENDING
                message = f"Booking request created for Court {booking_request.court_id} on {booking_request.booking_date.strftime('%B %d, %Y')}"
                scheduled_for = None
            else:
                # Booking needs to be scheduled
                status = BookingStatus.SCHEDULED
                message = validation.message
                scheduled_for = validation.available_at
            
            # Create booking request in database
            booking_model = BookingRequestModel(
                request_id=booking_id,
                user_id=user_id,
                court_id=booking_request.court_id,
                booking_date=booking_request.booking_date.isoformat(),
                time_slot=booking_request.time_slot,
                status=status.value,
                retry_count=0,
                max_retries=3,
                created_at=datetime.now().isoformat(),
                updated_at=datetime.now().isoformat()
            )
            
            # Save to database
            created_booking = self.booking_dao.create_booking_request(booking_model)
            
            # Return response
            return BookingResponse(
                booking_id=created_booking.request_id,
                user_id=created_booking.user_id,
                court_id=created_booking.court_id,
                booking_date=date.fromisoformat(created_booking.booking_date),
                time_slot=created_booking.time_slot,
                status=BookingStatus(created_booking.status),
                message=message,
                created_at=datetime.fromisoformat(created_booking.created_at),
                updated_at=datetime.fromisoformat(created_booking.updated_at),
                scheduled_for=scheduled_for
            )
            
        except Exception as e:
            logger.error(f"Error creating booking request: {e}")
            raise
    
    def get_user_bookings(self, user_id: str, limit: int = 10, offset: int = 0) -> List[BookingResponse]:
        """Get user's booking history"""
        try:
            bookings = self.booking_dao.get_user_bookings(user_id)
            
            # Convert to response format
            booking_responses = []
            for booking in bookings[offset:offset + limit]:
                booking_responses.append(BookingResponse(
                    booking_id=booking.request_id,
                    user_id=booking.user_id,
                    court_id=booking.court_id,
                    booking_date=date.fromisoformat(booking.booking_date),
                    time_slot=booking.time_slot,
                    status=BookingStatus(booking.status),
                    message=f"Booking for Court {booking.court_id}",
                    created_at=datetime.fromisoformat(booking.created_at),
                    updated_at=datetime.fromisoformat(booking.updated_at)
                ))
            
            return booking_responses
            
        except Exception as e:
            logger.error(f"Error getting user bookings: {e}")
            raise
    
    def get_booking_by_id(self, booking_id: str, user_id: str) -> Optional[BookingResponse]:
        """Get specific booking by ID"""
        try:
            booking = self.booking_dao.get_booking_request(booking_id)
            
            if not booking or booking.user_id != user_id:
                return None
            
            return BookingResponse(
                booking_id=booking.request_id,
                user_id=booking.user_id,
                court_id=booking.court_id,
                booking_date=date.fromisoformat(booking.booking_date),
                time_slot=booking.time_slot,
                status=BookingStatus(booking.status),
                message=f"Booking for Court {booking.court_id}",
                created_at=datetime.fromisoformat(booking.created_at),
                updated_at=datetime.fromisoformat(booking.updated_at)
            )
            
        except Exception as e:
            logger.error(f"Error getting booking by ID: {e}")
            raise
    
    def get_court_availability(self) -> AvailabilityResponse:
        """Get availability information for all courts"""
        try:
            courts = []
            today = date.today()
            
            for court_id, window_days in self.court_windows.items():
                available_dates = self.calculate_available_dates(int(court_id), today)
                
                # Calculate next available date (tomorrow's first available date)
                tomorrow = today + timedelta(days=1)
                tomorrow_available = self.calculate_available_dates(int(court_id), tomorrow)
                next_available = tomorrow_available[0] if tomorrow_available else None
                
                courts.append(CourtAvailability(
                    court_id=int(court_id),
                    available_dates=available_dates,
                    booking_window_days=window_days,
                    next_available_date=next_available
                ))
            
            return AvailabilityResponse(
                courts=courts,
                current_date=today
            )
            
        except Exception as e:
            logger.error(f"Error getting court availability: {e}")
            raise
    
    def _validate_status_transition(self, current_status: BookingStatus, new_status: BookingStatus) -> bool:
        """Validate if status transition is allowed"""
        valid_transitions = {
            BookingStatus.PENDING: [BookingStatus.PROCESSING, BookingStatus.CANCELLED, BookingStatus.FAILED],
            BookingStatus.PROCESSING: [BookingStatus.CONFIRMED, BookingStatus.FAILED, BookingStatus.CANCELLED],
            BookingStatus.SCHEDULED: [BookingStatus.PROCESSING, BookingStatus.CANCELLED, BookingStatus.EXPIRED],
            BookingStatus.CONFIRMED: [BookingStatus.CANCELLED],
            BookingStatus.FAILED: [BookingStatus.PROCESSING],  # Allow retry
            BookingStatus.CANCELLED: [],  # Final state
            BookingStatus.EXPIRED: []  # Final state
        }
        
        return new_status in valid_transitions.get(current_status, [])
    
    def update_booking_status(self, booking_id: str, new_status: BookingStatus, message: str = None) -> BookingResponse:
        """Update booking status with validation"""
        try:
            booking = self.booking_dao.get_booking_request(booking_id)
            
            if not booking:
                raise ValueError(f"Booking {booking_id} not found")
            
            current_status = BookingStatus(booking.status)
            
            # Validate status transition
            if not self._validate_status_transition(current_status, new_status):
                raise ValueError(f"Invalid status transition from {current_status.value} to {new_status.value}")
            
            # Update the booking
            booking.status = new_status.value
            booking.updated_at = datetime.now().isoformat()
            
            # Update in database
            updated_booking = self.booking_dao.update_booking_request(booking)
            
            logger.info(f"Booking {booking_id} status updated from {current_status.value} to {new_status.value}")
            
            return BookingResponse(
                booking_id=updated_booking.request_id,
                user_id=updated_booking.user_id,
                court_id=updated_booking.court_id,
                booking_date=date.fromisoformat(updated_booking.booking_date),
                time_slot=updated_booking.time_slot,
                status=BookingStatus(updated_booking.status),
                message=message or f"Status updated to {new_status.value}",
                created_at=datetime.fromisoformat(updated_booking.created_at),
                updated_at=datetime.fromisoformat(updated_booking.updated_at)
            )
            
        except Exception as e:
            logger.error(f"Error updating booking status: {e}")
            raise
    
    def cancel_booking(self, booking_id: str, user_id: str) -> bool:
        """Cancel a booking request"""
        try:
            booking = self.booking_dao.get_booking_request(booking_id)
            
            if not booking or booking.user_id != user_id:
                return False
            
            # Update status to cancelled
            booking.status = BookingStatus.CANCELLED.value
            booking.updated_at = datetime.now().isoformat()
            
            # Update in database
            self.booking_dao.update_booking_request(booking)
            return True
            
        except Exception as e:
            logger.error(f"Error cancelling booking: {e}")
            return False
    
    def process_booking(self, booking_id: str) -> BookingResponse:
        """Process a booking request (move to processing state)"""
        try:
            booking = self.booking_dao.get_booking_request(booking_id)
            
            if not booking:
                raise ValueError(f"Booking {booking_id} not found")
            
            return self.update_booking_status(booking_id, BookingStatus.PROCESSING, "Processing booking request")
            
        except Exception as e:
            logger.error(f"Error processing booking: {e}")
            raise
    
    def confirm_booking(self, booking_id: str, confirmation_code: str = None) -> BookingResponse:
        """Confirm a booking request"""
        try:
            message = "Booking confirmed successfully"
            if confirmation_code:
                message += f" (Confirmation: {confirmation_code})"
            
            return self.update_booking_status(booking_id, BookingStatus.CONFIRMED, message)
            
        except Exception as e:
            logger.error(f"Error confirming booking: {e}")
            raise
    
    def fail_booking(self, booking_id: str, error_message: str = None) -> BookingResponse:
        """Fail a booking request"""
        try:
            message = error_message or "Booking failed"
            return self.update_booking_status(booking_id, BookingStatus.FAILED, message)
            
        except Exception as e:
            logger.error(f"Error failing booking: {e}")
            raise
    
    def expire_booking(self, booking_id: str) -> BookingResponse:
        """Expire a booking request"""
        try:
            return self.update_booking_status(booking_id, BookingStatus.EXPIRED, "Booking expired")
            
        except Exception as e:
            logger.error(f"Error expiring booking: {e}")
            raise
    
    def get_bookings_by_status(self, status: BookingStatus, limit: int = 50) -> List[BookingResponse]:
        """Get bookings by status for processing"""
        try:
            bookings = self.booking_dao.get_requests_by_status(status, limit)
            
            booking_responses = []
            for booking in bookings:
                booking_responses.append(BookingResponse(
                    booking_id=booking.request_id,
                    user_id=booking.user_id,
                    court_id=booking.court_id,
                    booking_date=date.fromisoformat(booking.booking_date),
                    time_slot=booking.time_slot,
                    status=BookingStatus(booking.status),
                    message=f"Booking for Court {booking.court_id}",
                    created_at=datetime.fromisoformat(booking.created_at),
                    updated_at=datetime.fromisoformat(booking.updated_at)
                ))
            
            return booking_responses
            
        except Exception as e:
            logger.error(f"Error getting bookings by status: {e}")
            raise
    
    def cleanup_old_bookings(self, days_old: int = 30) -> int:
        """Clean up old completed, cancelled, and failed bookings"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days_old)
            cutoff_date_str = cutoff_date.isoformat()
            
            # Get all bookings older than cutoff date
            old_bookings = self.booking_dao.get_old_bookings(cutoff_date_str)
            
            cleanup_count = 0
            for booking in old_bookings:
                status = BookingStatus(booking.status)
                
                # Only clean up final states (not pending or processing)
                if status in [BookingStatus.CONFIRMED, BookingStatus.CANCELLED, BookingStatus.FAILED, BookingStatus.EXPIRED]:
                    try:
                        self.booking_dao.delete_booking_request(booking.request_id)
                        cleanup_count += 1
                        logger.debug(f"Cleaned up old booking {booking.request_id} with status {status.value}")
                    except Exception as e:
                        logger.error(f"Error cleaning up booking {booking.request_id}: {e}")
            
            logger.info(f"Cleaned up {cleanup_count} old bookings older than {days_old} days")
            return cleanup_count
            
        except Exception as e:
            logger.error(f"Error during cleanup of old bookings: {e}")
            raise
    
    def expire_old_requests(self, hours_old: int = 24) -> int:
        """Expire old pending and scheduled requests"""
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours_old)
            cutoff_time_str = cutoff_time.isoformat()
            
            # Get pending and scheduled requests older than cutoff
            old_requests = self.booking_dao.get_old_requests_by_status(
                [BookingStatus.PENDING, BookingStatus.SCHEDULED], 
                cutoff_time_str
            )
            
            expired_count = 0
            for request in old_requests:
                try:
                    self.expire_booking(request.request_id)
                    expired_count += 1
                    logger.debug(f"Expired old request {request.request_id}")
                except Exception as e:
                    logger.error(f"Error expiring request {request.request_id}: {e}")
            
            logger.info(f"Expired {expired_count} old requests older than {hours_old} hours")
            return expired_count
            
        except Exception as e:
            logger.error(f"Error during expiration of old requests: {e}")
            raise

# Global booking service instance
booking_service = BookingService()