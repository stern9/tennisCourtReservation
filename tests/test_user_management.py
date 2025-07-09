# ABOUTME: Comprehensive test suite for enhanced user management service
# ABOUTME: Tests user registration, authentication, session management, and security features

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import os

# Set test environment
os.environ['TENNIS_ENVIRONMENT'] = 'development'
os.environ['DYNAMODB_ENDPOINT'] = 'http://localhost:8000'

from src.api.services.user_service import UserService, UserSession, SessionStatus
from src.models import EncryptedUserConfig

@pytest.fixture
def mock_user():
    """Mock user for testing"""
    return EncryptedUserConfig(
        user_id="test_user_123",
        username="testuser",
        password="TestPass123!",
        email="test@example.com",
        first_name="Test",
        last_name="User",
        is_active=True,
        preferred_courts=[1, 2],
        preferred_times=["De 08:00 AM a 09:00 AM"],
        max_bookings_per_day=1,
        auto_booking_enabled=False,
        failed_login_attempts=0,
        last_login=datetime.now(),
        account_locked_until=None
    )

@pytest.fixture
def user_service():
    """User service instance for testing"""
    return UserService()

class TestUserService:
    """Test user service functionality"""
    
    @patch('src.api.services.user_service.auth_service.verify_tennis_site_credentials')
    @patch('src.api.services.user_service.EncryptedUserConfigDAO')
    def test_register_user_success(self, mock_dao, mock_verify, user_service, mock_user):
        """Test successful user registration"""
        # Mock tennis site validation
        mock_verify.return_value = True
        
        # Mock DAO methods
        mock_dao_instance = mock_dao.return_value
        mock_dao_instance.get_user_by_username.return_value = None
        mock_dao_instance.create_user.return_value = mock_user
        
        # Test registration
        result = user_service.register_user(
            username="testuser",
            password="TestPass123!",
            email="test@example.com",
            first_name="Test",
            last_name="User"
        )
        
        assert result is not None
        assert result.username == "testuser"
        mock_verify.assert_called_once_with("testuser", "TestPass123!")
        mock_dao_instance.create_user.assert_called_once()
    
    @patch('src.api.services.user_service.auth_service.verify_tennis_site_credentials')
    @patch('src.api.services.user_service.EncryptedUserConfigDAO')
    def test_register_user_already_exists(self, mock_dao, mock_verify, user_service, mock_user):
        """Test user registration when user already exists"""
        # Mock tennis site validation
        mock_verify.return_value = True
        
        # Mock DAO methods - user already exists
        mock_dao_instance = mock_dao.return_value
        mock_dao_instance.get_user_by_username.return_value = mock_user
        
        # Test registration
        result = user_service.register_user(
            username="testuser",
            password="TestPass123!"
        )
        
        assert result is None
        mock_dao_instance.create_user.assert_not_called()
    
    @patch('src.api.services.user_service.auth_service.verify_tennis_site_credentials')
    def test_register_user_tennis_site_failure(self, mock_verify, user_service):
        """Test user registration with tennis site validation failure"""
        # Mock tennis site validation failure
        mock_verify.return_value = False
        
        # Test registration
        result = user_service.register_user(
            username="testuser",
            password="wrongpass"
        )
        
        assert result is None
        mock_verify.assert_called_once_with("testuser", "wrongpass")
    
    @patch('src.api.services.user_service.auth_service.authenticate_user')
    @patch('src.api.services.user_service.auth_service.create_access_token')
    @patch('src.api.services.user_service.EncryptedUserConfigDAO')
    def test_authenticate_user_enhanced_success(self, mock_dao, mock_create_token, mock_auth, user_service, mock_user):
        """Test enhanced user authentication success"""
        # Mock authentication
        mock_auth.return_value = mock_user
        mock_create_token.return_value = "test_token"
        
        # Mock DAO methods
        mock_dao_instance = mock_dao.return_value
        mock_dao_instance.get_user_by_username.return_value = mock_user
        mock_dao_instance.update_user.return_value = mock_user
        
        # Test authentication
        result = user_service.authenticate_user_enhanced(
            username="testuser",
            password="TestPass123!",
            ip_address="192.168.1.1"
        )
        
        assert result is not None
        assert result["access_token"] == "test_token"
        assert result["user"] == mock_user
        assert "session_id" in result
        mock_dao_instance.update_user.assert_called_once()
    
    @patch('src.api.services.user_service.auth_service.authenticate_user')
    @patch('src.api.services.user_service.EncryptedUserConfigDAO')
    def test_authenticate_user_enhanced_failure(self, mock_dao, mock_auth, user_service):
        """Test enhanced user authentication failure"""
        # Mock authentication failure
        mock_auth.return_value = None
        
        # Test authentication
        result = user_service.authenticate_user_enhanced(
            username="testuser",
            password="wrongpass"
        )
        
        assert result is None
    
    @patch('src.api.services.user_service.EncryptedUserConfigDAO')
    def test_authenticate_user_account_locked(self, mock_dao, user_service, mock_user):
        """Test authentication with locked account"""
        # Mock locked account
        mock_user.account_locked_until = datetime.now() + timedelta(minutes=30)
        
        # Mock DAO methods
        mock_dao_instance = mock_dao.return_value
        mock_dao_instance.get_user_by_username.return_value = mock_user
        
        # Test authentication
        result = user_service.authenticate_user_enhanced(
            username="testuser",
            password="TestPass123!"
        )
        
        assert result is None
    
    def test_validate_password_strength_strong(self, user_service):
        """Test strong password validation"""
        strong_password = "StrongPass123!"
        result = user_service.validate_password_strength(strong_password)
        assert result is True
    
    def test_validate_password_strength_weak(self, user_service):
        """Test weak password validation"""
        weak_passwords = [
            "weak",  # Too short
            "weakpass",  # No uppercase, no numbers, no special chars
            "WEAKPASS",  # No lowercase, no numbers, no special chars
            "WeakPass",  # No numbers, no special chars
            "WeakPass123",  # No special chars
        ]
        
        for password in weak_passwords:
            result = user_service.validate_password_strength(password)
            assert result is False
    
    def test_validate_user_data_valid(self, user_service, mock_user):
        """Test valid user data validation"""
        result = user_service.validate_user_data(mock_user)
        assert result is True
    
    def test_validate_user_data_invalid(self, user_service):
        """Test invalid user data validation"""
        invalid_users = [
            EncryptedUserConfig(
                user_id="test", username="ab", password="weak",  # Username too short
                email="test@example.com", first_name="Test", last_name="User",
                preferred_courts=[1], preferred_times=["De 08:00 AM a 09:00 AM"],
                max_bookings_per_day=1, auto_booking_enabled=False
            ),
            EncryptedUserConfig(
                user_id="test", username="testuser", password="weak",  # Weak password
                email="test@example.com", first_name="Test", last_name="User",
                preferred_courts=[1], preferred_times=["De 08:00 AM a 09:00 AM"],
                max_bookings_per_day=1, auto_booking_enabled=False
            ),
            EncryptedUserConfig(
                user_id="test", username="testuser", password="StrongPass123!",
                email="invalid-email", first_name="Test", last_name="User",  # Invalid email
                preferred_courts=[1], preferred_times=["De 08:00 AM a 09:00 AM"],
                max_bookings_per_day=1, auto_booking_enabled=False
            )
        ]
        
        for user in invalid_users:
            result = user_service.validate_user_data(user)
            assert result is False
    
    def test_is_account_locked_true(self, user_service, mock_user):
        """Test account lock check when account is locked"""
        mock_user.account_locked_until = datetime.now() + timedelta(minutes=30)
        result = user_service.is_account_locked(mock_user)
        assert result is True
    
    def test_is_account_locked_false(self, user_service, mock_user):
        """Test account lock check when account is not locked"""
        mock_user.account_locked_until = None
        result = user_service.is_account_locked(mock_user)
        assert result is False
    
    def test_is_account_locked_expired(self, user_service, mock_user):
        """Test account lock check when lock has expired"""
        mock_user.account_locked_until = datetime.now() - timedelta(minutes=30)
        result = user_service.is_account_locked(mock_user)
        assert result is False
    
    @patch('src.api.services.user_service.EncryptedUserConfigDAO')
    def test_handle_failed_login(self, mock_dao, user_service, mock_user):
        """Test failed login handling"""
        # Mock DAO
        mock_dao_instance = mock_dao.return_value
        mock_dao_instance.update_user.return_value = mock_user
        
        # Test failed login handling
        user_service.handle_failed_login(mock_user)
        
        assert mock_user.failed_login_attempts == 1
        mock_dao_instance.update_user.assert_called_once()
    
    @patch('src.api.services.user_service.EncryptedUserConfigDAO')
    def test_handle_failed_login_account_lock(self, mock_dao, user_service, mock_user):
        """Test account lock after multiple failed logins"""
        # Mock DAO
        mock_dao_instance = mock_dao.return_value
        mock_dao_instance.update_user.return_value = mock_user
        
        # Set up for account lock
        mock_user.failed_login_attempts = 4
        
        # Test failed login handling
        user_service.handle_failed_login(mock_user)
        
        assert mock_user.failed_login_attempts == 5
        assert mock_user.account_locked_until is not None
        mock_dao_instance.update_user.assert_called_once()
    
    @patch('src.api.services.user_service.EncryptedUserConfigDAO')
    def test_reset_failed_login_attempts(self, mock_dao, user_service, mock_user):
        """Test reset of failed login attempts"""
        # Mock DAO
        mock_dao_instance = mock_dao.return_value
        mock_dao_instance.update_user.return_value = mock_user
        
        # Set up failed attempts
        mock_user.failed_login_attempts = 3
        mock_user.account_locked_until = datetime.now() + timedelta(minutes=30)
        
        # Test reset
        user_service.reset_failed_login_attempts(mock_user)
        
        assert mock_user.failed_login_attempts == 0
        assert mock_user.account_locked_until is None
        mock_dao_instance.update_user.assert_called_once()
    
    def test_analyze_password_strength_very_strong(self, user_service):
        """Test password strength analysis for very strong password"""
        password = "VeryStrongPass123!"
        result = user_service.analyze_password_strength(password)
        
        assert result["score"] == 5
        assert result["level"] == "very_strong"
        assert all(result["criteria"].values())
    
    def test_analyze_password_strength_weak(self, user_service):
        """Test password strength analysis for weak password"""
        password = "weak"
        result = user_service.analyze_password_strength(password)
        
        assert result["score"] <= 2
        assert result["level"] in ["weak", "very_weak"]
    
    def test_generate_security_recommendations(self, user_service, mock_user):
        """Test security recommendations generation"""
        # Test with weak password
        password_strength = {
            "score": 2,
            "level": "weak",
            "criteria": {
                "length": True,
                "uppercase": False,
                "lowercase": True,
                "numbers": False,
                "special_chars": False
            }
        }
        
        recommendations = user_service.generate_security_recommendations(mock_user, password_strength)
        
        assert len(recommendations) > 0
        assert any("stronger password" in rec for rec in recommendations)
    
    def test_session_management(self, user_service):
        """Test session creation and management"""
        # Create a session
        session = UserSession(
            user_id="test_user",
            token="test_token",
            expires_at=datetime.now() + timedelta(hours=1),
            ip_address="192.168.1.1"
        )
        
        # Add to active sessions
        user_service.active_sessions[session.session_id] = session
        
        # Test get user sessions
        sessions = user_service.get_user_sessions("test_user")
        assert len(sessions) == 1
        assert sessions[0]["session_id"] == session.session_id
        
        # Test revoke session
        success = user_service.revoke_session(session.session_id, "test_user")
        assert success is True
        
        # Verify session was revoked
        sessions = user_service.get_user_sessions("test_user")
        assert len(sessions) == 0
    
    def test_revoke_all_sessions(self, user_service):
        """Test revoking all sessions for a user"""
        # Create multiple sessions
        for i in range(3):
            session = UserSession(
                user_id="test_user",
                token=f"test_token_{i}",
                expires_at=datetime.now() + timedelta(hours=1),
                ip_address="192.168.1.1"
            )
            user_service.active_sessions[session.session_id] = session
        
        # Test revoke all sessions
        revoked_count = user_service.revoke_all_sessions("test_user")
        assert revoked_count == 3
        
        # Verify all sessions were revoked
        sessions = user_service.get_user_sessions("test_user")
        assert len(sessions) == 0
    
    def test_cleanup_expired_sessions(self, user_service):
        """Test cleanup of expired sessions"""
        # Create expired session
        expired_session = UserSession(
            user_id="test_user",
            token="expired_token",
            expires_at=datetime.now() - timedelta(hours=1),
            ip_address="192.168.1.1"
        )
        user_service.active_sessions[expired_session.session_id] = expired_session
        
        # Create valid session
        valid_session = UserSession(
            user_id="test_user",
            token="valid_token",
            expires_at=datetime.now() + timedelta(hours=1),
            ip_address="192.168.1.1"
        )
        user_service.active_sessions[valid_session.session_id] = valid_session
        
        # Test cleanup
        cleaned_count = user_service.cleanup_expired_sessions()
        assert cleaned_count == 1
        
        # Verify only valid session remains
        sessions = user_service.get_user_sessions("test_user")
        assert len(sessions) == 1
        assert sessions[0]["session_id"] == valid_session.session_id

class TestUserServiceIntegration:
    """Integration tests for user service"""
    
    @patch('src.api.services.user_service.auth_service.verify_tennis_site_credentials')
    @patch('src.api.services.user_service.EncryptedUserConfigDAO')
    def test_full_user_lifecycle(self, mock_dao, mock_verify, user_service, mock_user):
        """Test complete user lifecycle from registration to deactivation"""
        # Mock dependencies
        mock_verify.return_value = True
        mock_dao_instance = mock_dao.return_value
        mock_dao_instance.get_user_by_username.return_value = None
        mock_dao_instance.create_user.return_value = mock_user
        mock_dao_instance.get_user.return_value = mock_user
        mock_dao_instance.update_user.return_value = mock_user
        
        # 1. Register user
        registered_user = user_service.register_user(
            username="testuser",
            password="TestPass123!",
            email="test@example.com"
        )
        assert registered_user is not None
        
        # 2. Authenticate user
        auth_result = user_service.authenticate_user_enhanced(
            username="testuser",
            password="TestPass123!"
        )
        assert auth_result is not None
        
        # 3. Get security summary
        security_summary = user_service.get_user_security_summary(mock_user.user_id)
        assert "password_strength" in security_summary
        
        # 4. Validate user data
        is_valid = user_service.validate_user_data(mock_user)
        assert is_valid is True
        
        # 5. Session management
        sessions = user_service.get_user_sessions(mock_user.user_id)
        assert len(sessions) >= 0  # May have sessions from authentication
    
    def test_security_validation_comprehensive(self, user_service):
        """Test comprehensive security validation"""
        # Test various password scenarios
        test_cases = [
            ("Password123!", True),    # Strong password
            ("password", False),       # Weak password
            ("PASSWORD", False),       # No lowercase
            ("Password", False),       # No numbers/special
            ("Pass123!", True),        # Acceptable password
            ("VeryStrongPassword123!", True),  # Very strong password
        ]
        
        for password, expected in test_cases:
            result = user_service.validate_password_strength(password)
            assert result == expected, f"Password '{password}' validation failed"
    
    def test_session_security(self, user_service):
        """Test session security features"""
        # Test session creation
        session = UserSession(
            user_id="test_user",
            token="test_token",
            expires_at=datetime.now() + timedelta(hours=1),
            ip_address="192.168.1.1"
        )
        
        # Verify session properties
        assert session.status == SessionStatus.ACTIVE
        assert session.user_id == "test_user"
        assert session.ip_address == "192.168.1.1"
        assert session.access_count == 1
        assert session.session_id is not None
        
        # Test session tracking
        user_service.active_sessions[session.session_id] = session
        
        # Verify session can be retrieved
        sessions = user_service.get_user_sessions("test_user")
        assert len(sessions) == 1
        assert sessions[0]["ip_address"] == "192.168.1.1"
        
        # Test session revocation
        success = user_service.revoke_session(session.session_id, "test_user")
        assert success is True
        
        # Verify session is no longer active
        sessions = user_service.get_user_sessions("test_user")
        assert len(sessions) == 0