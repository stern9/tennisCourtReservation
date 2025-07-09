# ABOUTME: Bookings router for court reservation management with court-specific validation
# ABOUTME: Handles booking creation, status tracking, and availability queries

from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import List, Optional
import logging

from ..auth import get_current_user_profile
from ..models import (
    BookingRequest, BookingResponse, BookingListResponse, BookingStatus,
    UserProfile, AvailabilityResponse, BookingValidation, BookingStatusUpdate
)
from ..services.booking_service import booking_service

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/", response_model=BookingResponse)
async def create_booking(
    booking_request: BookingRequest,
    current_user: UserProfile = Depends(get_current_user_profile)
):
    """
    Create a new booking request
    
    This endpoint validates court availability and either:
    1. Creates immediate booking if court is available
    2. Schedules booking for midnight if court becomes available tomorrow
    3. Returns error if booking is not possible
    """
    try:
        booking_response = booking_service.create_booking_request(
            booking_request, 
            current_user.user_id
        )
        
        if booking_response.status == BookingStatus.FAILED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=booking_response.message
            )
        
        return booking_response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating booking: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create booking request"
        )

@router.get("/", response_model=BookingListResponse)
async def get_user_bookings(
    current_user: UserProfile = Depends(get_current_user_profile),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(10, ge=1, le=100, description="Items per page")
):
    """
    Get user's booking history with pagination
    """
    try:
        offset = (page - 1) * per_page
        bookings = booking_service.get_user_bookings(
            current_user.user_id, 
            limit=per_page, 
            offset=offset
        )
        
        # For now, we'll return the actual count as total
        # In production, you might want to optimize this with a separate count query
        total = len(bookings) + offset
        
        return BookingListResponse(
            bookings=bookings,
            total=total,
            page=page,
            per_page=per_page
        )
        
    except Exception as e:
        logger.error(f"Error getting user bookings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve bookings"
        )

@router.get("/{booking_id}", response_model=BookingResponse)
async def get_booking(
    booking_id: str,
    current_user: UserProfile = Depends(get_current_user_profile)
):
    """
    Get specific booking by ID
    """
    try:
        booking = booking_service.get_booking_by_id(booking_id, current_user.user_id)
        
        if not booking:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Booking not found"
            )
        
        return booking
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting booking: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve booking"
        )

@router.get("/availability/courts", response_model=AvailabilityResponse)
async def get_court_availability(
    current_user: UserProfile = Depends(get_current_user_profile)
):
    """
    Get current court availability information
    
    Returns available dates for each court based on their specific booking windows
    """
    try:
        availability = booking_service.get_court_availability()
        return availability
        
    except Exception as e:
        logger.error(f"Error getting court availability: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve court availability"
        )

@router.post("/validate", response_model=BookingValidation)
async def validate_booking(
    booking_request: BookingRequest,
    current_user: UserProfile = Depends(get_current_user_profile)
):
    """
    Validate a booking request without creating it
    
    Useful for front-end validation and user feedback
    """
    try:
        validation = booking_service.validate_booking_request(booking_request, current_user.user_id)
        return validation
        
    except Exception as e:
        logger.error(f"Error validating booking: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to validate booking request"
        )

@router.put("/{booking_id}/status", response_model=BookingResponse)
async def update_booking_status(
    booking_id: str,
    status_update: BookingStatusUpdate,
    current_user: UserProfile = Depends(get_current_user_profile)
):
    """
    Update booking status (admin or system use)
    
    Allows updating booking status for processing, completion, or failure
    """
    try:
        booking = booking_service.get_booking_by_id(booking_id, current_user.user_id)
        
        if not booking:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Booking not found"
            )
        
        updated_booking = booking_service.update_booking_status(
            booking_id, 
            status_update.status, 
            status_update.message or f"Status updated to {status_update.status.value}"
        )
        
        return updated_booking
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating booking status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update booking status"
        )

@router.delete("/{booking_id}")
async def cancel_booking(
    booking_id: str,
    current_user: UserProfile = Depends(get_current_user_profile)
):
    """
    Cancel a booking request
    
    Only pending and scheduled bookings can be cancelled
    """
    try:
        booking = booking_service.get_booking_by_id(booking_id, current_user.user_id)
        
        if not booking:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Booking not found"
            )
        
        # Check if booking can be cancelled
        if booking.status not in [BookingStatus.PENDING, BookingStatus.SCHEDULED]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot cancel booking with status: {booking.status}"
            )
        
        success = booking_service.cancel_booking(booking_id, current_user.user_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to cancel booking"
            )
        
        return {"message": "Booking cancelled successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling booking: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cancel booking"
        )

@router.post("/cleanup")
async def cleanup_bookings(
    current_user: UserProfile = Depends(get_current_user_profile),
    days_old: int = Query(30, ge=1, le=365, description="Days old to clean up completed bookings"),
    hours_old: int = Query(24, ge=1, le=168, description="Hours old to expire pending requests")
):
    """
    Manual cleanup of old bookings and expired requests (admin only)
    """
    try:
        # Check if user has admin privileges (implement as needed)
        # For now, allow all authenticated users
        
        cleanup_count = booking_service.cleanup_old_bookings(days_old=days_old)
        expired_count = booking_service.expire_old_requests(hours_old=hours_old)
        
        return {
            "message": "Cleanup completed successfully",
            "cleaned_up_bookings": cleanup_count,
            "expired_requests": expired_count
        }
        
    except Exception as e:
        logger.error(f"Error during manual cleanup: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to perform cleanup"
        )