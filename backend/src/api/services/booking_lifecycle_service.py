# ABOUTME: Booking lifecycle management service for complete request workflow
# ABOUTME: Handles booking state transitions, scheduling, and automatic processing

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import logging
from enum import Enum

from ..models import BookingStatus, BookingResponse
from .booking_service import booking_service
from .scheduler_service import background_scheduler, JobType
from ...dao import BookingRequestDAO
from ...models import BookingRequest as BookingRequestModel

logger = logging.getLogger(__name__)

class BookingLifecycleEvent(str, Enum):
    """Booking lifecycle events"""
    CREATED = "created"
    VALIDATED = "validated"
    SCHEDULED = "scheduled"
    PROCESSING_STARTED = "processing_started"
    PROCESSING_COMPLETED = "processing_completed"
    CONFIRMED = "confirmed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"

class BookingLifecycleService:
    """Service for managing booking request lifecycle"""
    
    def __init__(self):
        self.booking_dao = BookingRequestDAO()
        self.event_handlers = {
            BookingLifecycleEvent.CREATED: self._handle_created,
            BookingLifecycleEvent.VALIDATED: self._handle_validated,
            BookingLifecycleEvent.SCHEDULED: self._handle_scheduled,
            BookingLifecycleEvent.PROCESSING_STARTED: self._handle_processing_started,
            BookingLifecycleEvent.PROCESSING_COMPLETED: self._handle_processing_completed,
            BookingLifecycleEvent.CONFIRMED: self._handle_confirmed,
            BookingLifecycleEvent.FAILED: self._handle_failed,
            BookingLifecycleEvent.CANCELLED: self._handle_cancelled,
            BookingLifecycleEvent.EXPIRED: self._handle_expired
        }
    
    def process_booking_lifecycle(self, booking_id: str, event: BookingLifecycleEvent, context: Dict[str, Any] = None) -> bool:
        """Process a booking lifecycle event"""
        try:
            logger.info(f"Processing lifecycle event {event.value} for booking {booking_id}")
            
            # Get current booking
            booking = self.booking_dao.get_booking_request(booking_id)
            if not booking:
                logger.error(f"Booking {booking_id} not found")
                return False
            
            # Get event handler
            handler = self.event_handlers.get(event)
            if not handler:
                logger.error(f"No handler for event {event.value}")
                return False
            
            # Process the event
            success = handler(booking, context or {})
            
            if success:
                logger.info(f"Successfully processed {event.value} for booking {booking_id}")
            else:
                logger.error(f"Failed to process {event.value} for booking {booking_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error processing lifecycle event {event.value} for booking {booking_id}: {e}")
            return False
    
    def _handle_created(self, booking: BookingRequestModel, context: Dict[str, Any]) -> bool:
        """Handle booking creation event"""
        try:
            # Log creation
            logger.info(f"Booking {booking.request_id} created for user {booking.user_id}")
            
            # Trigger validation
            return self.process_booking_lifecycle(booking.request_id, BookingLifecycleEvent.VALIDATED, context)
            
        except Exception as e:
            logger.error(f"Error handling booking creation: {e}")
            return False
    
    def _handle_validated(self, booking: BookingRequestModel, context: Dict[str, Any]) -> bool:
        """Handle booking validation event"""
        try:
            current_status = BookingStatus(booking.status)
            
            if current_status == BookingStatus.PENDING:
                # Move to processing immediately
                booking_service.process_booking(booking.request_id)
                return self.process_booking_lifecycle(booking.request_id, BookingLifecycleEvent.PROCESSING_STARTED, context)
            
            elif current_status == BookingStatus.SCHEDULED:
                # Schedule for future processing
                return self.process_booking_lifecycle(booking.request_id, BookingLifecycleEvent.SCHEDULED, context)
            
            return True
            
        except Exception as e:
            logger.error(f"Error handling booking validation: {e}")
            return False
    
    def _handle_scheduled(self, booking: BookingRequestModel, context: Dict[str, Any]) -> bool:
        """Handle booking scheduling event"""
        try:
            # Schedule midnight booking job
            scheduled_time = context.get('scheduled_time')
            if scheduled_time:
                job_id = background_scheduler.schedule_midnight_booking(
                    booking.request_id,
                    booking.user_id,
                    scheduled_time
                )
                
                logger.info(f"Scheduled midnight booking job {job_id} for booking {booking.request_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error handling booking scheduling: {e}")
            return False
    
    def _handle_processing_started(self, booking: BookingRequestModel, context: Dict[str, Any]) -> bool:
        """Handle booking processing start event"""
        try:
            logger.info(f"Processing started for booking {booking.request_id}")
            
            # In a real implementation, this would trigger the tennis booking script
            # For now, we'll simulate processing completion
            
            # Schedule processing completion (simulate async processing)
            processing_time = datetime.now() + timedelta(seconds=30)
            
            # This would normally be handled by the actual tennis booking service
            # For now, we'll just log and continue
            
            return True
            
        except Exception as e:
            logger.error(f"Error handling processing start: {e}")
            return False
    
    def _handle_processing_completed(self, booking: BookingRequestModel, context: Dict[str, Any]) -> bool:
        """Handle booking processing completion event"""
        try:
            success = context.get('success', False)
            confirmation_code = context.get('confirmation_code')
            error_message = context.get('error_message')
            
            if success:
                # Confirm booking
                booking_service.confirm_booking(booking.request_id, confirmation_code)
                return self.process_booking_lifecycle(booking.request_id, BookingLifecycleEvent.CONFIRMED, context)
            else:
                # Fail booking
                booking_service.fail_booking(booking.request_id, error_message)
                return self.process_booking_lifecycle(booking.request_id, BookingLifecycleEvent.FAILED, context)
            
        except Exception as e:
            logger.error(f"Error handling processing completion: {e}")
            return False
    
    def _handle_confirmed(self, booking: BookingRequestModel, context: Dict[str, Any]) -> bool:
        """Handle booking confirmation event"""
        try:
            logger.info(f"Booking {booking.request_id} confirmed successfully")
            
            # Send notification (if notification service is available)
            self._send_notification(booking, "confirmed", context)
            
            return True
            
        except Exception as e:
            logger.error(f"Error handling booking confirmation: {e}")
            return False
    
    def _handle_failed(self, booking: BookingRequestModel, context: Dict[str, Any]) -> bool:
        """Handle booking failure event"""
        try:
            logger.warning(f"Booking {booking.request_id} failed")
            
            # Check if retry is possible
            if booking.retry_count < booking.max_retries:
                # Schedule retry
                retry_delay = context.get('retry_delay_minutes', 30)
                job_id = background_scheduler.schedule_retry_booking(booking.request_id, retry_delay)
                logger.info(f"Scheduled retry job {job_id} for booking {booking.request_id}")
            else:
                # Max retries reached, send failure notification
                self._send_notification(booking, "failed", context)
            
            return True
            
        except Exception as e:
            logger.error(f"Error handling booking failure: {e}")
            return False
    
    def _handle_cancelled(self, booking: BookingRequestModel, context: Dict[str, Any]) -> bool:
        """Handle booking cancellation event"""
        try:
            logger.info(f"Booking {booking.request_id} cancelled")
            
            # Send notification
            self._send_notification(booking, "cancelled", context)
            
            return True
            
        except Exception as e:
            logger.error(f"Error handling booking cancellation: {e}")
            return False
    
    def _handle_expired(self, booking: BookingRequestModel, context: Dict[str, Any]) -> bool:
        """Handle booking expiration event"""
        try:
            logger.info(f"Booking {booking.request_id} expired")
            
            # Send notification
            self._send_notification(booking, "expired", context)
            
            return True
            
        except Exception as e:
            logger.error(f"Error handling booking expiration: {e}")
            return False
    
    def _send_notification(self, booking: BookingRequestModel, event_type: str, context: Dict[str, Any]):
        """Send notification about booking event"""
        try:
            # Placeholder for notification service
            # In a real implementation, this would send email/SMS/push notifications
            logger.info(f"Notification: Booking {booking.request_id} {event_type}")
            
        except Exception as e:
            logger.error(f"Error sending notification: {e}")
    
    def process_pending_bookings(self) -> int:
        """Process all pending bookings"""
        try:
            pending_bookings = booking_service.get_bookings_by_status(BookingStatus.PENDING)
            processed_count = 0
            
            for booking in pending_bookings:
                success = self.process_booking_lifecycle(
                    booking.booking_id, 
                    BookingLifecycleEvent.PROCESSING_STARTED
                )
                if success:
                    processed_count += 1
            
            logger.info(f"Processed {processed_count} pending bookings")
            return processed_count
            
        except Exception as e:
            logger.error(f"Error processing pending bookings: {e}")
            return 0
    
    def process_scheduled_bookings(self) -> int:
        """Process all scheduled bookings that are ready"""
        try:
            scheduled_bookings = booking_service.get_bookings_by_status(BookingStatus.SCHEDULED)
            processed_count = 0
            
            current_time = datetime.now()
            
            for booking in scheduled_bookings:
                # Check if booking is ready for processing (e.g., midnight has passed)
                if booking.scheduled_for and booking.scheduled_for <= current_time:
                    success = self.process_booking_lifecycle(
                        booking.booking_id,
                        BookingLifecycleEvent.PROCESSING_STARTED
                    )
                    if success:
                        processed_count += 1
            
            logger.info(f"Processed {processed_count} scheduled bookings")
            return processed_count
            
        except Exception as e:
            logger.error(f"Error processing scheduled bookings: {e}")
            return 0
    
    def get_booking_lifecycle_stats(self) -> Dict[str, Any]:
        """Get booking lifecycle statistics"""
        try:
            stats = self.booking_dao.get_booking_stats()
            
            # Add lifecycle-specific stats
            stats['lifecycle'] = {
                'total_processed': stats.get('total_requests', 0),
                'success_rate': self._calculate_success_rate(stats),
                'avg_processing_time': self._calculate_avg_processing_time(),
                'pending_count': stats.get('status_counts', {}).get('pending', 0),
                'scheduled_count': stats.get('status_counts', {}).get('scheduled', 0),
                'processing_count': stats.get('status_counts', {}).get('processing', 0)
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting lifecycle stats: {e}")
            return {}
    
    def _calculate_success_rate(self, stats: Dict[str, Any]) -> float:
        """Calculate booking success rate"""
        try:
            status_counts = stats.get('status_counts', {})
            confirmed = status_counts.get('confirmed', 0)
            failed = status_counts.get('failed', 0)
            total = confirmed + failed
            
            if total == 0:
                return 0.0
            
            return (confirmed / total) * 100
            
        except Exception as e:
            logger.error(f"Error calculating success rate: {e}")
            return 0.0
    
    def _calculate_avg_processing_time(self) -> float:
        """Calculate average processing time"""
        try:
            # This would require storing processing times in the database
            # For now, return a placeholder
            return 0.0
            
        except Exception as e:
            logger.error(f"Error calculating average processing time: {e}")
            return 0.0

# Global lifecycle service instance
booking_lifecycle_service = BookingLifecycleService()