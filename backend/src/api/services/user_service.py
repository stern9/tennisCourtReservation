# ABOUTME: User management service with enhanced authentication and session management
# ABOUTME: Handles user registration, password validation, session isolation, and security monitoring

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import logging
import uuid
from enum import Enum

from ..config import get_settings
from ..models import UserProfile, UserConfigUpdate, LoginResponse, TokenData
from ..auth import auth_service
from ...dao import EncryptedUserConfigDAO, SystemConfigDAO
from ...models import EncryptedUserConfig

logger = logging.getLogger(__name__)

class UserRole(str, Enum):
    """User role enumeration"""
    USER = "user"
    ADMIN = "admin"
    MODERATOR = "moderator"

class SessionStatus(str, Enum):
    """Session status enumeration"""
    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"

class UserSession:
    """User session management"""
    def __init__(self, user_id: str, token: str, expires_at: datetime, ip_address: str = None):
        self.session_id = str(uuid.uuid4())
        self.user_id = user_id
        self.token = token
        self.created_at = datetime.now()
        self.expires_at = expires_at
        self.last_accessed = datetime.now()
        self.ip_address = ip_address
        self.status = SessionStatus.ACTIVE
        self.access_count = 1

class UserService:
    """Enhanced user management service"""
    
    def __init__(self):
        self.settings = get_settings()
        self.user_dao = EncryptedUserConfigDAO()
        self.system_config_dao = SystemConfigDAO()
        self.active_sessions: Dict[str, UserSession] = {}  # In production, use Redis
        
    def register_user(self, username: str, password: str, email: str = None, 
                     first_name: str = None, last_name: str = None) -> Optional[EncryptedUserConfig]:
        """
        Register a new user with tennis site validation
        
        This method:
        1. Validates credentials against tennis site
        2. Checks if user already exists
        3. Creates new user with proper defaults
        4. Performs initial security validation
        """
        try:
            # First validate credentials against tennis site
            if not auth_service.verify_tennis_site_credentials(username, password):
                logger.warning(f"Tennis site registration failed for user: {username}")
                return None
            
            # Check if user already exists
            existing_user = self.user_dao.get_user_by_username(username)
            if existing_user:
                logger.warning(f"User registration failed - user already exists: {username}")
                return None
            
            # Create new user with enhanced defaults
            user_id = f"user_{username}_{int(datetime.now().timestamp())}"
            
            new_user = EncryptedUserConfig(
                user_id=user_id,
                username=username,
                password=password,
                email=email or f"{username}@tennis.local",
                first_name=first_name or username.title(),
                last_name=last_name or "User",
                is_active=True,
                preferred_courts=[1, 2],  # Default to both courts
                preferred_times=["De 08:00 AM a 09:00 AM"],  # Default morning slot
                max_bookings_per_day=1,
                auto_booking_enabled=False,
                role="user",
                failed_login_attempts=0,
                last_login=datetime.now(),
                account_locked_until=None
            )
            
            # Validate user data
            if not self.validate_user_data(new_user):
                logger.error(f"User data validation failed for: {username}")
                return None
            
            # Create user in database
            created_user = self.user_dao.create_user(new_user)
            
            # Log successful registration
            logger.info(f"User registered successfully: {username}")
            
            return created_user
            
        except Exception as e:
            logger.error(f"User registration error for {username}: {e}")
            return None
    
    def authenticate_user_enhanced(self, username: str, password: str, 
                                 ip_address: str = None) -> Optional[Dict[str, Any]]:
        """
        Enhanced user authentication with session management
        
        Returns authentication result with user info and session data
        """
        try:
            # Check for account lockout
            user = self.user_dao.get_user_by_username(username)
            if user and self.is_account_locked(user):
                logger.warning(f"Authentication failed - account locked: {username}")
                return None
            
            # Authenticate user
            authenticated_user = auth_service.authenticate_user(username, password)
            
            if not authenticated_user:
                # Handle failed login attempt
                if user:
                    self.handle_failed_login(user)
                return None
            
            # Reset failed login attempts on successful login
            self.reset_failed_login_attempts(authenticated_user)
            
            # Create JWT token
            access_token_expires = timedelta(hours=self.settings.jwt_expiration_hours)
            access_token = auth_service.create_access_token(
                data={"sub": authenticated_user.username, "user_id": authenticated_user.user_id},
                expires_delta=access_token_expires
            )
            
            # Create user session
            expires_at = datetime.now() + access_token_expires
            session = UserSession(
                user_id=authenticated_user.user_id,
                token=access_token,
                expires_at=expires_at,
                ip_address=ip_address
            )
            
            # Store session (in production, use Redis)
            self.active_sessions[session.session_id] = session
            
            # Update last login
            authenticated_user.last_login = datetime.now()
            self.user_dao.update_user(authenticated_user)
            
            return {
                "user": authenticated_user,
                "access_token": access_token,
                "token_type": "bearer",
                "expires_in": self.settings.jwt_expiration_hours * 3600,
                "session_id": session.session_id
            }
            
        except Exception as e:
            logger.error(f"Enhanced authentication error for {username}: {e}")
            return None
    
    def validate_user_data(self, user: EncryptedUserConfig) -> bool:
        """
        Comprehensive user data validation
        
        Validates:
        - Username format and uniqueness
        - Password strength
        - Email format
        - Court preferences
        - Business rules
        """
        try:
            # Username validation
            if not user.username or len(user.username) < 3:
                return False
            
            # Password strength validation
            if not self.validate_password_strength(user.password):
                return False
            
            # Email validation
            if not user.email or "@" not in user.email:
                return False
            
            # Court preferences validation
            valid_courts = [1, 2]
            if not all(court in valid_courts for court in user.preferred_courts):
                return False
            
            # Business rule validation
            if user.max_bookings_per_day < 1 or user.max_bookings_per_day > 5:
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"User data validation error: {e}")
            return False
    
    def validate_password_strength(self, password: str) -> bool:
        """
        Enhanced password strength validation
        
        Requirements:
        - At least 8 characters
        - Contains uppercase and lowercase letters
        - Contains at least one number
        - Contains at least one special character
        """
        if not password or len(password) < 8:
            return False
        
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password)
        
        return has_upper and has_lower and has_digit and has_special
    
    def is_account_locked(self, user: EncryptedUserConfig) -> bool:
        """Check if user account is locked"""
        if not user.account_locked_until:
            return False
        
        return datetime.now() < user.account_locked_until
    
    def handle_failed_login(self, user: EncryptedUserConfig):
        """Handle failed login attempt"""
        user.failed_login_attempts += 1
        
        # Lock account after 5 failed attempts
        if user.failed_login_attempts >= 5:
            user.account_locked_until = datetime.now() + timedelta(minutes=30)
            logger.warning(f"Account locked due to failed login attempts: {user.username}")
        
        self.user_dao.update_user(user)
    
    def reset_failed_login_attempts(self, user: EncryptedUserConfig):
        """Reset failed login attempts after successful login"""
        if user.failed_login_attempts > 0:
            user.failed_login_attempts = 0
            user.account_locked_until = None
            self.user_dao.update_user(user)
    
    def get_user_sessions(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all active sessions for a user"""
        user_sessions = []
        
        for session in self.active_sessions.values():
            if session.user_id == user_id and session.status == SessionStatus.ACTIVE:
                user_sessions.append({
                    "session_id": session.session_id,
                    "created_at": session.created_at,
                    "expires_at": session.expires_at,
                    "last_accessed": session.last_accessed,
                    "ip_address": session.ip_address,
                    "access_count": session.access_count
                })
        
        return user_sessions
    
    def revoke_session(self, session_id: str, user_id: str) -> bool:
        """Revoke a specific user session"""
        try:
            session = self.active_sessions.get(session_id)
            
            if not session or session.user_id != user_id:
                return False
            
            session.status = SessionStatus.REVOKED
            del self.active_sessions[session_id]
            
            logger.info(f"Session revoked: {session_id} for user: {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error revoking session {session_id}: {e}")
            return False
    
    def revoke_all_sessions(self, user_id: str) -> int:
        """Revoke all sessions for a user"""
        revoked_count = 0
        
        sessions_to_revoke = [
            session_id for session_id, session in self.active_sessions.items()
            if session.user_id == user_id
        ]
        
        for session_id in sessions_to_revoke:
            if self.revoke_session(session_id, user_id):
                revoked_count += 1
        
        logger.info(f"Revoked {revoked_count} sessions for user: {user_id}")
        return revoked_count
    
    def update_user_profile(self, user_id: str, updates: UserConfigUpdate) -> Optional[UserProfile]:
        """
        Update user profile with validation and security checks
        """
        try:
            # Get current user
            user = self.user_dao.get_user(user_id)
            if not user:
                return None
            
            # Apply updates with validation
            update_data = updates.dict(exclude_unset=True)
            
            # Validate updates
            for field, value in update_data.items():
                if field == "preferred_courts":
                    valid_courts = [1, 2]
                    if not all(court in valid_courts for court in value):
                        raise ValueError(f"Invalid court selection: {value}")
                
                elif field == "max_bookings_per_day":
                    if value < 1 or value > 5:
                        raise ValueError(f"Invalid max bookings per day: {value}")
                
                elif field == "email":
                    if not value or "@" not in value:
                        raise ValueError(f"Invalid email format: {value}")
            
            # Apply validated updates
            for field, value in update_data.items():
                if hasattr(user, field):
                    setattr(user, field, value)
            
            # Update user in database
            updated_user = self.user_dao.update_user(user)
            
            # Return updated profile
            return UserProfile(
                user_id=updated_user.user_id,
                username=updated_user.username,
                email=updated_user.email,
                first_name=updated_user.first_name,
                last_name=updated_user.last_name,
                is_active=updated_user.is_active,
                preferred_courts=updated_user.preferred_courts,
                preferred_times=updated_user.preferred_times,
                max_bookings_per_day=updated_user.max_bookings_per_day,
                auto_booking_enabled=updated_user.auto_booking_enabled,
                created_at=updated_user.created_at,
                updated_at=updated_user.updated_at
            )
            
        except Exception as e:
            logger.error(f"Error updating user profile {user_id}: {e}")
            return None
    
    def get_user_security_summary(self, user_id: str) -> Dict[str, Any]:
        """
        Get comprehensive security summary for user
        """
        try:
            user = self.user_dao.get_user(user_id)
            if not user:
                return {}
            
            # Get basic security summary from DAO
            basic_summary = self.user_dao.get_user_security_summary(user_id)
            
            # Enhance with session information
            active_sessions = self.get_user_sessions(user_id)
            
            # Password strength analysis
            password_strength = self.analyze_password_strength(user.password)
            
            # Account status
            account_status = {
                "is_active": user.is_active,
                "is_locked": self.is_account_locked(user),
                "failed_login_attempts": user.failed_login_attempts,
                "last_login": user.last_login,
                "account_locked_until": user.account_locked_until
            }
            
            # Security recommendations
            recommendations = self.generate_security_recommendations(user, password_strength)
            
            return {
                **basic_summary,
                "active_sessions": len(active_sessions),
                "session_details": active_sessions,
                "password_strength": password_strength,
                "account_status": account_status,
                "recommendations": recommendations
            }
            
        except Exception as e:
            logger.error(f"Error getting security summary for {user_id}: {e}")
            return {}
    
    def analyze_password_strength(self, password: str) -> Dict[str, Any]:
        """Analyze password strength and provide score"""
        if not password:
            return {"score": 0, "level": "very_weak"}
        
        score = 0
        criteria = {
            "length": len(password) >= 8,
            "uppercase": any(c.isupper() for c in password),
            "lowercase": any(c.islower() for c in password),
            "numbers": any(c.isdigit() for c in password),
            "special_chars": any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password)
        }
        
        score = sum(criteria.values())
        
        if score == 5:
            level = "very_strong"
        elif score == 4:
            level = "strong"
        elif score == 3:
            level = "medium"
        elif score == 2:
            level = "weak"
        else:
            level = "very_weak"
        
        return {
            "score": score,
            "level": level,
            "criteria": criteria,
            "max_score": 5
        }
    
    def generate_security_recommendations(self, user: EncryptedUserConfig, 
                                        password_strength: Dict[str, Any]) -> List[str]:
        """Generate security recommendations for user"""
        recommendations = []
        
        # Password recommendations
        if password_strength["score"] < 4:
            recommendations.append("Consider using a stronger password with uppercase, lowercase, numbers, and special characters")
        
        # Account security
        if user.failed_login_attempts > 0:
            recommendations.append("Recent failed login attempts detected. Consider changing your password if this wasn't you")
        
        # Session management
        active_sessions = self.get_user_sessions(user.user_id)
        if len(active_sessions) > 3:
            recommendations.append("You have multiple active sessions. Consider revoking unused sessions")
        
        # Email verification
        if user.email.endswith("@tennis.local"):
            recommendations.append("Update your email address to receive important security notifications")
        
        # Auto-booking security
        if user.auto_booking_enabled:
            recommendations.append("Auto-booking is enabled. Ensure your account is secure and monitor booking activity")
        
        return recommendations
    
    def cleanup_expired_sessions(self):
        """Clean up expired sessions (should be run periodically)"""
        current_time = datetime.now()
        expired_sessions = []
        
        for session_id, session in self.active_sessions.items():
            if session.expires_at < current_time:
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            self.active_sessions[session_id].status = SessionStatus.EXPIRED
            del self.active_sessions[session_id]
        
        logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")
        return len(expired_sessions)

# Global user service instance
user_service = UserService()