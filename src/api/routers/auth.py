# ABOUTME: Authentication router for login and token management
# ABOUTME: Handles JWT token generation and user authentication via tennis site

from fastapi import APIRouter, HTTPException, status, Depends, Request
from fastapi.security import HTTPBearer
from datetime import timedelta
from typing import List, Dict, Any
import logging

from ..auth import auth_service, get_current_user
from ..models import LoginRequest, LoginResponse, ErrorResponse, UserProfile, TokenData
from ..config import get_settings
from ..services.user_service import user_service

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/login", response_model=LoginResponse)
async def login(login_request: LoginRequest, request: Request):
    """
    Enhanced authentication with session management and security monitoring
    
    This endpoint:
    1. Validates credentials against the tennis site
    2. Creates or updates user in our database
    3. Manages user sessions and security monitoring
    4. Returns JWT token for API access
    """
    try:
        # Get client IP address
        client_ip = request.client.host
        
        # Enhanced authentication with session management
        auth_result = user_service.authenticate_user_enhanced(
            login_request.username,
            login_request.password,
            ip_address=client_ip
        )
        
        if not auth_result:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials, account locked, or tennis site authentication failed",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        logger.info(f"User {auth_result['user'].username} logged in successfully from {client_ip}")
        
        return LoginResponse(
            access_token=auth_result["access_token"],
            token_type=auth_result["token_type"],
            expires_in=auth_result["expires_in"],
            user_id=auth_result["user"].user_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication service error"
        )

@router.post("/register")
async def register_user(
    login_request: LoginRequest,
    request: Request,
    email: str = None,
    first_name: str = None,
    last_name: str = None
):
    """
    Register new user with tennis site validation
    
    This endpoint:
    1. Validates credentials against tennis site
    2. Checks if user already exists
    3. Creates new user account
    4. Returns success confirmation
    """
    try:
        # Get client IP address
        client_ip = request.client.host
        
        # Register user
        new_user = user_service.register_user(
            username=login_request.username,
            password=login_request.password,
            email=email,
            first_name=first_name,
            last_name=last_name
        )
        
        if not new_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Registration failed. User may already exist or tennis site validation failed."
            )
        
        logger.info(f"User {new_user.username} registered successfully from {client_ip}")
        
        return {
            "message": "User registered successfully",
            "user_id": new_user.user_id,
            "username": new_user.username
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration service error"
        )

@router.post("/logout")
async def logout(current_user: TokenData = Depends(get_current_user)):
    """
    Enhanced logout with session revocation
    """
    try:
        # Revoke all user sessions
        revoked_count = user_service.revoke_all_sessions(current_user.user_id)
        
        logger.info(f"User {current_user.username} logged out, {revoked_count} sessions revoked")
        
        return {
            "message": "Logout successful",
            "sessions_revoked": revoked_count
        }
        
    except Exception as e:
        logger.error(f"Logout error: {e}")
        return {"message": "Logout completed"}

@router.get("/sessions")
async def get_user_sessions(current_user: TokenData = Depends(get_current_user)):
    """
    Get all active sessions for current user
    """
    try:
        sessions = user_service.get_user_sessions(current_user.user_id)
        
        return {
            "sessions": sessions,
            "total_sessions": len(sessions)
        }
        
    except Exception as e:
        logger.error(f"Error getting user sessions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user sessions"
        )

@router.delete("/sessions/{session_id}")
async def revoke_session(
    session_id: str,
    current_user: TokenData = Depends(get_current_user)
):
    """
    Revoke a specific session
    """
    try:
        success = user_service.revoke_session(session_id, current_user.user_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found or access denied"
            )
        
        return {"message": "Session revoked successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error revoking session: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to revoke session"
        )

@router.delete("/sessions")
async def revoke_all_sessions(current_user: TokenData = Depends(get_current_user)):
    """
    Revoke all sessions for current user
    """
    try:
        revoked_count = user_service.revoke_all_sessions(current_user.user_id)
        
        return {
            "message": "All sessions revoked successfully",
            "sessions_revoked": revoked_count
        }
        
    except Exception as e:
        logger.error(f"Error revoking all sessions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to revoke sessions"
        )

@router.get("/me")
async def get_current_user_info(current_user = Depends(auth_service.get_current_user_profile)):
    """
    Get current user information from JWT token
    """
    return current_user