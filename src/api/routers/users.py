# ABOUTME: User management router for profile and configuration operations
# ABOUTME: Handles user profile updates, preferences, and account management

from fastapi import APIRouter, HTTPException, status, Depends
from typing import Dict, Any
from datetime import datetime
import logging

from ..auth import get_current_user_profile, auth_service, get_current_user
from ..models import UserProfile, UserConfigUpdate, ErrorResponse, TokenData
from ..config import get_settings
from ..services.user_service import user_service
from ...dao import EncryptedUserConfigDAO

logger = logging.getLogger(__name__)

router = APIRouter()

# User DAO
user_dao = EncryptedUserConfigDAO()

@router.get("/me", response_model=UserProfile)
async def get_current_user(current_user: UserProfile = Depends(get_current_user_profile)):
    """
    Get current user profile information
    """
    return current_user

@router.put("/me/config", response_model=UserProfile)
async def update_user_config(
    config_update: UserConfigUpdate,
    current_user: UserProfile = Depends(get_current_user_profile)
):
    """
    Enhanced user configuration update with validation
    """
    try:
        # Use enhanced user service for validation and updates
        updated_profile = user_service.update_user_profile(
            current_user.user_id,
            config_update
        )
        
        if not updated_profile:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to update user configuration"
            )
        
        logger.info(f"User config updated successfully for: {current_user.username}")
        return updated_profile
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user config: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user configuration"
        )

@router.get("/me/security")
async def get_user_security_summary(current_user: UserProfile = Depends(get_current_user_profile)):
    """
    Get enhanced user security summary with session management and recommendations
    """
    try:
        # Use enhanced user service for comprehensive security analysis
        security_summary = user_service.get_user_security_summary(current_user.user_id)
        return security_summary
        
    except Exception as e:
        logger.error(f"Error getting security summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get security summary"
        )

@router.get("/me/password-strength")
async def check_password_strength(current_user: UserProfile = Depends(get_current_user_profile)):
    """
    Check current password strength and get recommendations
    """
    try:
        # Get user data
        user = user_dao.get_user(current_user.user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Analyze password strength
        strength_analysis = user_service.analyze_password_strength(user.password)
        
        return {
            "password_strength": strength_analysis,
            "recommendations": user_service.generate_security_recommendations(user, strength_analysis)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking password strength: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check password strength"
        )

@router.post("/me/change-password")
async def change_password(
    current_password: str,
    new_password: str,
    current_user: UserProfile = Depends(get_current_user_profile)
):
    """
    Change user password with validation
    """
    try:
        # Get current user
        user = user_dao.get_user(current_user.user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Verify current password
        if user.password != current_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect"
            )
        
        # Validate new password strength
        if not user_service.validate_password_strength(new_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="New password does not meet strength requirements"
            )
        
        # Update password
        user.password = new_password
        updated_user = user_dao.update_user(user)
        
        # Revoke all sessions to force re-authentication
        user_service.revoke_all_sessions(current_user.user_id)
        
        logger.info(f"Password changed successfully for user: {current_user.username}")
        
        return {
            "message": "Password changed successfully",
            "sessions_revoked": "All sessions revoked for security"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error changing password: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to change password"
        )

@router.post("/me/validate-data")
async def validate_user_data(current_user: UserProfile = Depends(get_current_user_profile)):
    """
    Validate current user data integrity
    """
    try:
        # Get current user
        user = user_dao.get_user(current_user.user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Validate user data
        is_valid = user_service.validate_user_data(user)
        
        if not is_valid:
            return {
                "is_valid": False,
                "message": "User data validation failed",
                "recommendations": [
                    "Check username format",
                    "Verify password strength",
                    "Validate email format",
                    "Check court preferences"
                ]
            }
        
        return {
            "is_valid": True,
            "message": "User data is valid",
            "last_validated": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error validating user data: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to validate user data"
        )

@router.delete("/me")
async def deactivate_user(current_user: UserProfile = Depends(get_current_user_profile)):
    """
    Deactivate current user account with session cleanup
    """
    try:
        # Revoke all sessions first
        revoked_count = user_service.revoke_all_sessions(current_user.user_id)
        
        # Deactivate user account
        user_dao.deactivate_user(current_user.user_id)
        
        logger.info(f"User {current_user.username} deactivated successfully")
        
        return {
            "message": "User account deactivated successfully",
            "sessions_revoked": revoked_count
        }
        
    except Exception as e:
        logger.error(f"Error deactivating user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to deactivate user account"
        )