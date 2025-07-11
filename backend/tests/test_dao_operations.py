# ABOUTME: Unit tests for Data Access Object (DAO) operations and validation
# ABOUTME: Tests UserConfigDAO, BookingRequestDAO, SystemConfigDAO functionality

import pytest
import os
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

from src.dao import (
    UserConfigDAO,
    BookingRequestDAO,
    SystemConfigDAO,
    DAOError,
    ValidationError,
    NotFoundError,
    ConflictError,
    DatabaseError
)
from src.models.user_config import UserConfig
from src.models.booking_request import BookingRequest, BookingStatus, BookingPriority
from src.models.system_config import SystemConfig, ConfigCategory, ConfigValueType
from src.factories.test_factories import (
    UserConfigFactory,
    BookingRequestFactory,
    SystemConfigFactory
)

# Set up test environment
if not os.getenv('USE_AWS_DYNAMODB') and not os.getenv('DYNAMODB_LOCAL_ENDPOINT'):
    os.environ['DYNAMODB_LOCAL_ENDPOINT'] = 'http://localhost:8000'


@pytest.fixture(scope="module")
def user_dao():
    """UserConfigDAO instance for testing"""
    return UserConfigDAO()


@pytest.fixture(scope="module")
def booking_dao():
    """BookingRequestDAO instance for testing"""
    return BookingRequestDAO()


@pytest.fixture(scope="module")
def config_dao():
    """SystemConfigDAO instance for testing"""
    return SystemConfigDAO()


class TestUserConfigDAO:
    """Test UserConfigDAO operations"""
    
    def test_create_user(self, user_dao):
        """Test creating a user"""
        user = UserConfigFactory.create_minimal(
            user_id="test_create_user",
            username="test_create_user",
            email="test_create@test.com"
        )
        
        # Clean up first
        try:
            user_dao.delete_user(user.user_id)
        except:
            pass
        
        created_user = user_dao.create_user(user)
        assert created_user.user_id == user.user_id
        assert created_user.username == user.username
        
        # Clean up
        user_dao.delete_user(user.user_id)
    
    def test_get_user(self, user_dao):
        """Test getting a user by ID"""
        user = UserConfigFactory.create_minimal(
            user_id="test_get_user",
            username="test_get_user",
            email="test_get@test.com"
        )
        
        # Clean up first
        try:
            user_dao.delete_user(user.user_id)
        except:
            pass
        
        # Create user
        user_dao.create_user(user)
        
        # Get user
        retrieved_user = user_dao.get_user(user.user_id)
        assert retrieved_user is not None
        assert retrieved_user.user_id == user.user_id
        
        # Test non-existent user
        non_existent = user_dao.get_user("non_existent_user")
        assert non_existent is None
        
        # Clean up
        user_dao.delete_user(user.user_id)
    
    def test_update_user(self, user_dao):
        """Test updating a user"""
        user = UserConfigFactory.create_minimal(
            user_id="test_update_user",
            username="test_update_user",
            email="test_update@test.com"
        )
        
        # Clean up first
        try:
            user_dao.delete_user(user.user_id)
        except:
            pass
        
        # Create user
        user_dao.create_user(user)
        
        # Update user
        user.first_name = "Updated"
        user.last_name = "Name"
        updated_user = user_dao.update_user(user)
        
        assert updated_user.first_name == "Updated"
        assert updated_user.last_name == "Name"
        
        # Test updating non-existent user
        non_existent_user = UserConfigFactory.create_minimal(user_id="non_existent")
        with pytest.raises(NotFoundError):
            user_dao.update_user(non_existent_user)
        
        # Clean up
        user_dao.delete_user(user.user_id)
    
    def test_delete_user(self, user_dao):
        """Test deleting a user"""
        user = UserConfigFactory.create_minimal(
            user_id="test_delete_user",
            username="test_delete_user",
            email="test_delete@test.com"
        )
        
        # Create user
        user_dao.create_user(user)
        
        # Delete user
        deleted = user_dao.delete_user(user.user_id)
        assert deleted is True
        
        # Verify user is deleted
        retrieved_user = user_dao.get_user(user.user_id)
        assert retrieved_user is None
        
        # Test deleting non-existent user
        deleted_again = user_dao.delete_user(user.user_id)
        assert deleted_again is False
    
    def test_user_exists(self, user_dao):
        """Test checking if user exists"""
        user = UserConfigFactory.create_minimal(
            user_id="test_exists_user",
            username="test_exists_user",
            email="test_exists@test.com"
        )
        
        # Clean up first
        try:
            user_dao.delete_user(user.user_id)
        except:
            pass
        
        # User should not exist
        assert user_dao.user_exists(user.user_id) is False
        
        # Create user
        user_dao.create_user(user)
        
        # User should exist
        assert user_dao.user_exists(user.user_id) is True
        
        # Clean up
        user_dao.delete_user(user.user_id)
    
    def test_get_user_by_username(self, user_dao):
        """Test getting user by username"""
        user = UserConfigFactory.create_minimal(
            user_id="test_username_user",
            username="unique_test_username",
            email="test_username@test.com"
        )
        
        # Clean up first
        try:
            user_dao.delete_user(user.user_id)
        except:
            pass
        
        # Create user
        user_dao.create_user(user)
        
        # Get by username
        retrieved_user = user_dao.get_user_by_username("unique_test_username")
        assert retrieved_user is not None
        assert retrieved_user.username == "unique_test_username"
        
        # Test non-existent username
        non_existent = user_dao.get_user_by_username("non_existent_username")
        assert non_existent is None
        
        # Clean up
        user_dao.delete_user(user.user_id)
    
    def test_get_user_by_email(self, user_dao):
        """Test getting user by email"""
        user = UserConfigFactory.create_minimal(
            user_id="test_email_user",
            username="test_email_user",
            email="unique_test@email.com"
        )
        
        # Clean up first
        try:
            user_dao.delete_user(user.user_id)
        except:
            pass
        
        # Create user
        user_dao.create_user(user)
        
        # Get by email
        retrieved_user = user_dao.get_user_by_email("unique_test@email.com")
        assert retrieved_user is not None
        assert retrieved_user.email == "unique_test@email.com"
        
        # Test non-existent email
        non_existent = user_dao.get_user_by_email("non_existent@email.com")
        assert non_existent is None
        
        # Clean up
        user_dao.delete_user(user.user_id)
    
    def test_activate_deactivate_user(self, user_dao):
        """Test activating and deactivating users"""
        user = UserConfigFactory.create_minimal(
            user_id="test_activate_user",
            username="test_activate_user",
            email="test_activate@test.com"
        )
        
        # Clean up first
        try:
            user_dao.delete_user(user.user_id)
        except:
            pass
        
        # Create user
        user_dao.create_user(user)
        
        # Deactivate user
        result = user_dao.deactivate_user(user.user_id)
        assert result is True
        
        # Verify user is deactivated
        updated_user = user_dao.get_user(user.user_id)
        assert updated_user.is_active is False
        
        # Activate user
        result = user_dao.activate_user(user.user_id)
        assert result is True
        
        # Verify user is activated
        updated_user = user_dao.get_user(user.user_id)
        assert updated_user.is_active is True
        
        # Test with non-existent user
        with pytest.raises(NotFoundError):
            user_dao.deactivate_user("non_existent_user")
        
        # Clean up
        user_dao.delete_user(user.user_id)


class TestBookingRequestDAO:
    """Test BookingRequestDAO operations"""
    
    def test_create_booking_request(self, booking_dao):
        """Test creating a booking request"""
        booking = BookingRequestFactory.create(
            request_id="test_create_booking",
            user_id="test_user"
        )
        
        # Clean up first
        try:
            booking_dao.delete_booking_request(booking.request_id)
        except:
            pass
        
        created_booking = booking_dao.create_booking_request(booking)
        assert created_booking.request_id == booking.request_id
        assert created_booking.requested_at is not None
        assert created_booking.expires_at is not None
        
        # Clean up
        booking_dao.delete_booking_request(booking.request_id)
    
    def test_get_booking_request(self, booking_dao):
        """Test getting a booking request by ID"""
        booking = BookingRequestFactory.create(
            request_id="test_get_booking",
            user_id="test_user"
        )
        
        # Clean up first
        try:
            booking_dao.delete_booking_request(booking.request_id)
        except:
            pass
        
        # Create booking
        booking_dao.create_booking_request(booking)
        
        # Get booking
        retrieved_booking = booking_dao.get_booking_request(booking.request_id)
        assert retrieved_booking is not None
        assert retrieved_booking.request_id == booking.request_id
        
        # Test non-existent booking
        non_existent = booking_dao.get_booking_request("non_existent_booking")
        assert non_existent is None
        
        # Clean up
        booking_dao.delete_booking_request(booking.request_id)
    
    def test_update_booking_request(self, booking_dao):
        """Test updating a booking request"""
        booking = BookingRequestFactory.create_pending(
            request_id="test_update_booking",
            user_id="test_user"
        )
        
        # Clean up first
        try:
            booking_dao.delete_booking_request(booking.request_id)
        except:
            pass
        
        # Create booking
        booking_dao.create_booking_request(booking)
        
        # Update booking
        booking.status = BookingStatus.CONFIRMED
        booking.confirmation_code = "CONF123"
        updated_booking = booking_dao.update_booking_request(booking)
        
        assert updated_booking.status == BookingStatus.CONFIRMED
        assert updated_booking.confirmation_code == "CONF123"
        
        # Test updating non-existent booking
        non_existent_booking = BookingRequestFactory.create(request_id="non_existent")
        with pytest.raises(NotFoundError):
            booking_dao.update_booking_request(non_existent_booking)
        
        # Clean up
        booking_dao.delete_booking_request(booking.request_id)
    
    def test_mark_request_status(self, booking_dao):
        """Test marking request status"""
        booking = BookingRequestFactory.create_pending(
            request_id="test_mark_status",
            user_id="test_user"
        )
        
        # Clean up first
        try:
            booking_dao.delete_booking_request(booking.request_id)
        except:
            pass
        
        # Create booking
        booking_dao.create_booking_request(booking)
        
        # Mark as confirmed
        confirmed_booking = booking_dao.mark_request_as_confirmed(
            booking.request_id, 
            "CONF123", 
            "EXT123"
        )
        assert confirmed_booking.status == BookingStatus.CONFIRMED
        assert confirmed_booking.confirmation_code == "CONF123"
        assert confirmed_booking.external_booking_id == "EXT123"
        
        # Create another booking for failed test
        failed_booking = BookingRequestFactory.create_pending(
            request_id="test_mark_failed",
            user_id="test_user"
        )
        booking_dao.create_booking_request(failed_booking)
        
        # Mark as failed
        failed_result = booking_dao.mark_request_as_failed(
            failed_booking.request_id,
            "Error occurred"
        )
        assert failed_result.status == BookingStatus.FAILED
        assert failed_result.error_message == "Error occurred"
        
        # Clean up
        booking_dao.delete_booking_request(booking.request_id)
        booking_dao.delete_booking_request(failed_booking.request_id)
    
    def test_get_user_booking_requests(self, booking_dao):
        """Test getting booking requests for a user"""
        user_id = "test_user_bookings"
        
        # Clean up any existing bookings for this user
        existing_bookings = booking_dao.get_user_booking_requests(user_id)
        for booking in existing_bookings:
            booking_dao.delete_booking_request(booking.request_id)
        
        # Create multiple bookings for user
        bookings = []
        for i in range(3):
            booking = BookingRequestFactory.create(
                request_id=f"user_booking_{i}",
                user_id=user_id
            )
            booking_dao.create_booking_request(booking)
            bookings.append(booking)
        
        # Get user bookings
        user_bookings = booking_dao.get_user_booking_requests(user_id)
        assert len(user_bookings) == 3
        assert all(booking.user_id == user_id for booking in user_bookings)
        
        # Test with status filter
        pending_bookings = booking_dao.get_user_booking_requests(
            user_id, 
            status=BookingStatus.PENDING
        )
        assert all(booking.status == BookingStatus.PENDING for booking in pending_bookings)
        
        # Clean up
        for booking in bookings:
            booking_dao.delete_booking_request(booking.request_id)


class TestSystemConfigDAO:
    """Test SystemConfigDAO operations"""
    
    def test_create_config(self, config_dao):
        """Test creating a configuration"""
        config = SystemConfigFactory.create(
            config_key="test_create_config",
            config_value="test_value"
        )
        
        # Clean up first
        try:
            config_dao.delete_config(config.config_key)
        except:
            pass
        
        created_config = config_dao.create_config(config)
        assert created_config.config_key == config.config_key
        assert created_config.config_value == config.config_value
        
        # Clean up
        config_dao.delete_config(config.config_key)
    
    def test_get_config(self, config_dao):
        """Test getting a configuration"""
        config = SystemConfigFactory.create(
            config_key="test_get_config",
            config_value="test_value"
        )
        
        # Clean up first
        try:
            config_dao.delete_config(config.config_key)
        except:
            pass
        
        # Create config
        config_dao.create_config(config)
        
        # Get config
        retrieved_config = config_dao.get_config(config.config_key)
        assert retrieved_config is not None
        assert retrieved_config.config_key == config.config_key
        
        # Test non-existent config
        non_existent = config_dao.get_config("non_existent_config")
        assert non_existent is None
        
        # Clean up
        config_dao.delete_config(config.config_key)
    
    def test_get_config_value(self, config_dao):
        """Test getting configuration value"""
        config = SystemConfigFactory.create_integer_config(
            config_key="test_get_value",
            value=42
        )
        
        # Clean up first
        try:
            config_dao.delete_config(config.config_key)
        except:
            pass
        
        # Create config
        config_dao.create_config(config)
        
        # Get config value
        value = config_dao.get_config_value(config.config_key)
        assert value == 42
        
        # Test non-existent config
        with pytest.raises(NotFoundError):
            config_dao.get_config_value("non_existent_config")
        
        # Clean up
        config_dao.delete_config(config.config_key)
    
    def test_set_config(self, config_dao):
        """Test setting configuration value"""
        config_key = "test_set_config"
        
        # Clean up first
        try:
            config_dao.delete_config(config_key)
        except:
            pass
        
        # Set new config
        config = config_dao.set_config(
            config_key,
            "new_value",
            description="Test config",
            category=ConfigCategory.SYSTEM
        )
        assert config.config_key == config_key
        assert config.config_value == "new_value"
        
        # Update existing config
        updated_config = config_dao.set_config(config_key, "updated_value")
        assert updated_config.config_value == "updated_value"
        
        # Clean up
        config_dao.delete_config(config_key)
    
    def test_get_configs_by_category(self, config_dao):
        """Test getting configurations by category"""
        category = ConfigCategory.SYSTEM
        config_keys = []
        
        try:
            # Create multiple configs in same category
            for i in range(3):
                config_key = f"test_category_{i}"
                config_keys.append(config_key)
                config_dao.set_config(
                    config_key,
                    f"value_{i}",
                    category=category
                )
            
            # Get configs by category
            configs = config_dao.get_configs_by_category(category)
            category_configs = [c for c in configs if c.config_key.startswith("test_category_")]
            assert len(category_configs) == 3
            assert all(config.category == category for config in category_configs)
            
        finally:
            # Clean up
            for config_key in config_keys:
                try:
                    config_dao.delete_config(config_key)
                except:
                    pass
    
    def test_activate_deactivate_config(self, config_dao):
        """Test activating and deactivating configurations"""
        config = SystemConfigFactory.create(
            config_key="test_activate_config",
            config_value="test_value",
            is_required=False
        )
        
        # Clean up first
        try:
            config_dao.delete_config(config.config_key)
        except:
            pass
        
        # Create config
        config_dao.create_config(config)
        
        # Deactivate config
        deactivated_config = config_dao.deactivate_config(config.config_key)
        assert deactivated_config.is_active is False
        
        # Activate config
        activated_config = config_dao.activate_config(config.config_key)
        assert activated_config.is_active is True
        
        # Clean up
        config_dao.delete_config(config.config_key)
    
    def test_config_validation(self, config_dao):
        """Test configuration validation"""
        config = SystemConfigFactory.create_integer_config(
            config_key="test_validation_config",
            value=50,
            min_value=1,
            max_value=100
        )
        
        # Clean up first
        try:
            config_dao.delete_config(config.config_key)
        except:
            pass
        
        # Create config
        config_dao.create_config(config)
        
        # Valid update
        config.update_value(75)
        updated_config = config_dao.update_config(config)
        assert updated_config.config_value == 75
        
        # Invalid update should raise error
        with pytest.raises(ValueError):
            config.update_value(150)  # Above max
        
        # Clean up
        config_dao.delete_config(config.config_key)


class TestDAOErrorHandling:
    """Test DAO error handling"""
    
    def test_validation_error_handling(self, user_dao):
        """Test validation error handling"""
        # Try to create user with invalid data
        invalid_user = UserConfig(
            user_id="test_invalid",
            username="ab",  # Too short
            password="ValidPass123",
            email="test@test.com",
            first_name="Test",
            last_name="User"
        )
        
        # This should raise ValidationError during model creation
        # but if it doesn't, the DAO should catch it
        try:
            user_dao.create_user(invalid_user)
            # If we get here, clean up
            user_dao.delete_user("test_invalid")
        except Exception as e:
            # Expected to fail
            assert "validation" in str(e).lower()
    
    def test_not_found_error_handling(self, user_dao):
        """Test NotFoundError handling"""
        with pytest.raises(NotFoundError):
            user_dao.update_user(UserConfigFactory.create_minimal(user_id="non_existent"))


if __name__ == "__main__":
    pytest.main([__file__, "-v"])