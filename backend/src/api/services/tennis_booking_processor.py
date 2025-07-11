# ABOUTME: Tennis booking processor that monitors BookingRequests table and executes tennis script
# ABOUTME: Handles real-time booking processing, status updates, and error handling with retry logic

import logging
import time
import threading
import sys
import os
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from enum import Enum

# Add project root to path for tennis script import
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from ..models import BookingStatus
from ...dao import BookingRequestDAO
from ...models import BookingRequest as BookingRequestModel
from .booking_service import booking_service

logger = logging.getLogger(__name__)

class ProcessingStatus(str, Enum):
    """Processing status for booking requests"""
    SUCCESS = "success"
    FAILURE = "failure"
    RETRY = "retry"
    EXPIRED = "expired"

class TennisBookingProcessor:
    """Service for processing tennis booking requests"""
    
    def __init__(self):
        self.booking_dao = BookingRequestDAO()
        self.running = False
        self.processor_thread = None
        self.poll_interval = 30  # seconds
        self.max_concurrent_bookings = 3
        self.processing_bookings = {}  # Track currently processing bookings
        
    def start(self):
        """Start the booking processor"""
        if self.running:
            logger.warning("Booking processor is already running")
            return
            
        self.running = True
        self.processor_thread = threading.Thread(target=self._process_loop, daemon=True)
        self.processor_thread.start()
        logger.info("Tennis booking processor started")
        
    def stop(self):
        """Stop the booking processor"""
        if not self.running:
            return
            
        self.running = False
        if self.processor_thread:
            self.processor_thread.join(timeout=10)
        logger.info("Tennis booking processor stopped")
        
    def _process_loop(self):
        """Main processing loop"""
        while self.running:
            try:
                # Process pending bookings
                self._process_pending_bookings()
                
                # Process scheduled bookings that are ready
                self._process_scheduled_bookings()
                
                # Clean up expired bookings
                self._cleanup_expired_bookings()
                
                # Sleep before next iteration
                time.sleep(self.poll_interval)
                
            except Exception as e:
                logger.error(f"Error in booking processor loop: {e}")
                time.sleep(60)  # Wait longer on error
                
    def _process_pending_bookings(self):
        """Process all pending booking requests"""
        try:
            # Get pending bookings
            pending_bookings = self.booking_dao.get_requests_by_status(BookingStatus.PENDING)
            
            if not pending_bookings:
                return
                
            logger.info(f"Found {len(pending_bookings)} pending bookings to process")
            
            # Process up to max_concurrent_bookings
            for booking in pending_bookings[:self.max_concurrent_bookings]:
                if booking.request_id not in self.processing_bookings:
                    self._process_booking_request(booking)
                    
        except Exception as e:
            logger.error(f"Error processing pending bookings: {e}")
            
    def _process_scheduled_bookings(self):
        """Process scheduled bookings that are ready"""
        try:
            # Get scheduled bookings
            scheduled_bookings = self.booking_dao.get_requests_by_status(BookingStatus.SCHEDULED)
            
            if not scheduled_bookings:
                return
                
            current_time = datetime.now()
            ready_bookings = []
            
            for booking in scheduled_bookings:
                # Check if booking is ready (this logic depends on your scheduling system)
                # For now, we'll process all scheduled bookings
                ready_bookings.append(booking)
                
            if ready_bookings:
                logger.info(f"Found {len(ready_bookings)} scheduled bookings ready for processing")
                
                for booking in ready_bookings[:self.max_concurrent_bookings]:
                    if booking.request_id not in self.processing_bookings:
                        self._process_booking_request(booking)
                        
        except Exception as e:
            logger.error(f"Error processing scheduled bookings: {e}")
            
    def _process_booking_request(self, booking: BookingRequestModel):
        """Process a single booking request"""
        try:
            # Mark as processing
            self.processing_bookings[booking.request_id] = datetime.now()
            
            # Update status to processing
            booking_service.update_booking_status(
                booking.request_id, 
                BookingStatus.PROCESSING, 
                "Processing booking request"
            )
            
            # Start processing in separate thread
            processing_thread = threading.Thread(
                target=self._execute_booking,
                args=(booking,),
                daemon=True
            )
            processing_thread.start()
            
        except Exception as e:
            logger.error(f"Error starting booking processing for {booking.request_id}: {e}")
            self._handle_booking_failure(booking, str(e))
            
    def _execute_booking(self, booking: BookingRequestModel):
        """Execute the actual booking using tennis script"""
        try:
            logger.info(f"Executing booking {booking.request_id} for user {booking.user_id}")
            
            # Import tennis script
            try:
                import tennis
                success = tennis.make_reservation(booking.user_id, booking)
                
                if success:
                    self._handle_booking_success(booking)
                else:
                    self._handle_booking_failure(booking, "Tennis script returned failure")
                    
            except ImportError:
                logger.error("Tennis script module not available")
                self._handle_booking_failure(booking, "Tennis script module not available")
                
        except Exception as e:
            logger.error(f"Error executing booking {booking.request_id}: {e}")
            self._handle_booking_failure(booking, str(e))
            
        finally:
            # Remove from processing dict
            if booking.request_id in self.processing_bookings:
                del self.processing_bookings[booking.request_id]
                
    def _handle_booking_success(self, booking: BookingRequestModel):
        """Handle successful booking"""
        try:
            # Generate confirmation code
            confirmation_code = f"CONF_{booking.request_id[:8].upper()}_{datetime.now().strftime('%Y%m%d')}"
            
            # Update booking status
            booking_service.confirm_booking(booking.request_id, confirmation_code)
            
            logger.info(f"Booking {booking.request_id} confirmed with code {confirmation_code}")
            
        except Exception as e:
            logger.error(f"Error handling booking success for {booking.request_id}: {e}")
            
    def _handle_booking_failure(self, booking: BookingRequestModel, error_message: str):
        """Handle failed booking with retry logic"""
        try:
            # Check if retry is possible
            if booking.retry_count < booking.max_retries:
                # Increment retry count
                booking.retry_count += 1
                updated_booking = self.booking_dao.update_booking_request(booking)
                
                # Schedule retry (exponential backoff)
                retry_delay = min(300 * (2 ** booking.retry_count), 3600)  # Max 1 hour
                logger.info(f"Scheduling retry for booking {booking.request_id} in {retry_delay} seconds")
                
                # For now, just log. In production, you'd use a proper job scheduler
                # TODO: Integrate with background_scheduler for retry scheduling
                
            else:
                # Max retries reached, mark as failed
                booking_service.fail_booking(booking.request_id, error_message)
                logger.error(f"Booking {booking.request_id} failed after {booking.max_retries} retries: {error_message}")
                
        except Exception as e:
            logger.error(f"Error handling booking failure for {booking.request_id}: {e}")
            
    def _cleanup_expired_bookings(self):
        """Clean up expired booking requests"""
        try:
            # Get expired bookings
            expired_bookings = self.booking_dao.get_expired_requests()
            
            if not expired_bookings:
                return
                
            logger.info(f"Found {len(expired_bookings)} expired bookings to clean up")
            
            for booking in expired_bookings:
                try:
                    booking_service.expire_booking(booking.request_id)
                    logger.debug(f"Expired booking {booking.request_id}")
                except Exception as e:
                    logger.error(f"Error expiring booking {booking.request_id}: {e}")
                    
        except Exception as e:
            logger.error(f"Error cleaning up expired bookings: {e}")
            
    def process_booking_manually(self, booking_id: str) -> bool:
        """Manually process a specific booking request"""
        try:
            booking = self.booking_dao.get_booking_request(booking_id)
            if not booking:
                logger.error(f"Booking {booking_id} not found")
                return False
                
            logger.info(f"Manually processing booking {booking_id}")
            self._process_booking_request(booking)
            return True
            
        except Exception as e:
            logger.error(f"Error manually processing booking {booking_id}: {e}")
            return False
            
    def get_processing_status(self) -> Dict[str, Any]:
        """Get current processing status"""
        try:
            return {
                "running": self.running,
                "currently_processing": len(self.processing_bookings),
                "processing_bookings": list(self.processing_bookings.keys()),
                "max_concurrent": self.max_concurrent_bookings,
                "poll_interval": self.poll_interval
            }
        except Exception as e:
            logger.error(f"Error getting processing status: {e}")
            return {"error": str(e)}
            
    def get_processing_statistics(self) -> Dict[str, Any]:
        """Get processing statistics"""
        try:
            # Get booking stats from DAO
            stats = self.booking_dao.get_booking_stats()
            
            # Add processing-specific stats
            processing_stats = {
                "total_bookings": stats.get("total_requests", 0),
                "status_breakdown": stats.get("status_counts", {}),
                "currently_processing": len(self.processing_bookings),
                "processor_uptime": self._get_uptime(),
                "success_rate": self._calculate_success_rate(stats)
            }
            
            return processing_stats
            
        except Exception as e:
            logger.error(f"Error getting processing statistics: {e}")
            return {"error": str(e)}
            
    def _get_uptime(self) -> str:
        """Get processor uptime"""
        if not self.running:
            return "Not running"
        # This would need to track start time
        return "Running"
        
    def _calculate_success_rate(self, stats: Dict[str, Any]) -> float:
        """Calculate booking success rate"""
        try:
            status_counts = stats.get("status_counts", {})
            confirmed = status_counts.get("confirmed", 0)
            failed = status_counts.get("failed", 0)
            total = confirmed + failed
            
            if total == 0:
                return 0.0
                
            return (confirmed / total) * 100
            
        except Exception as e:
            logger.error(f"Error calculating success rate: {e}")
            return 0.0

# Global booking processor instance
tennis_booking_processor = TennisBookingProcessor()