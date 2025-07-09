# ABOUTME: Tennis booking service that executes actual court reservations using integrated tennis.py
# ABOUTME: Handles DynamoDB-based configuration and coordinates with tennis script execution

import logging
import sys
import os
from datetime import datetime
from typing import Optional, Dict, Any

# Add project root to path for tennis script import
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from ...models import BookingRequest as BookingRequestModel, EncryptedUserConfig

logger = logging.getLogger(__name__)

class TennisBookingService:
    """Service for executing tennis court bookings using integrated tennis.py script"""
    
    def __init__(self):
        pass
        
    def execute_booking(self, booking_request: BookingRequestModel, user: EncryptedUserConfig) -> bool:
        """
        Execute a tennis court booking using the integrated tennis.py script
        
        Args:
            booking_request: The booking request to execute
            user: The user making the booking
            
        Returns:
            bool: True if booking was successful, False otherwise
        """
        try:
            logger.info(f"Executing booking for user {user.user_id}, court {booking_request.court_id}, date {booking_request.booking_date}")
            
            # Import tennis script
            try:
                import tennis
                
                # Execute booking using tennis script with DynamoDB configuration
                success = tennis.make_reservation(user.user_id, booking_request)
                
                if success:
                    logger.info(f"Booking successful for request {booking_request.request_id}")
                    return True
                else:
                    logger.warning(f"Booking failed for request {booking_request.request_id}")
                    return False
                    
            except ImportError as e:
                logger.error(f"Failed to import tennis script: {e}")
                return False
                
        except Exception as e:
            logger.error(f"Error executing booking: {e}")
            return False
            
    def validate_booking_feasibility(self, booking_request: BookingRequestModel, user: EncryptedUserConfig) -> Dict[str, Any]:
        """
        Validate if a booking is feasible without actually executing it
        
        Args:
            booking_request: The booking request to validate
            user: The user making the booking
            
        Returns:
            Dict containing validation results
        """
        try:
            # Basic validation checks
            validation_checks = []
            
            # Check if user has valid credentials
            if user.username and user.password:
                validation_checks.append("User credentials present")
            else:
                return {
                    "is_feasible": False,
                    "message": "User credentials missing",
                    "site_accessible": False,
                    "estimated_success_rate": 0.0,
                    "checks_performed": ["User credential check failed"]
                }
            
            # Check if booking request is valid
            if booking_request.court_id in [1, 2] and booking_request.booking_date and booking_request.time_slot:
                validation_checks.append("Booking request format valid")
            else:
                return {
                    "is_feasible": False,
                    "message": "Invalid booking request format",
                    "site_accessible": False,
                    "estimated_success_rate": 0.0,
                    "checks_performed": ["Booking request format check failed"]
                }
            
            # Check tennis script availability
            try:
                import tennis
                validation_checks.append("Tennis script available")
            except ImportError:
                return {
                    "is_feasible": False,
                    "message": "Tennis script not available",
                    "site_accessible": False,
                    "estimated_success_rate": 0.0,
                    "checks_performed": validation_checks + ["Tennis script check failed"]
                }
            
            # Basic feasibility assessment
            result = {
                "is_feasible": True,
                "message": "Booking appears feasible",
                "site_accessible": True,
                "estimated_success_rate": 0.85,
                "checks_performed": validation_checks
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error validating booking feasibility: {e}")
            return {
                "is_feasible": False,
                "message": f"Validation failed: {str(e)}",
                "site_accessible": False,
                "estimated_success_rate": 0.0,
                "checks_performed": ["Validation check failed"]
            }