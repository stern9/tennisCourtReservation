# ABOUTME: Unit tests for Pydantic models and validation logic
# ABOUTME: Tests UserConfig, BookingRequest, SystemConfig validation and business logic

import pytest
import uuid
from datetime import datetime, timedelta
from pydantic import ValidationError

from src.models.user_config import UserConfig
from src.models.booking_request import BookingRequest, BookingStatus, BookingPriority
from src.models.system_config import SystemConfig, ConfigCategory, ConfigValueType
from src.models.validators import (
    ValidationError as CustomValidationError,
    DateValidator,
    TimeValidator,
    CourtValidator,
    CredentialValidator,
    EmailValidator
)
from src.factories.test_factories import (
    UserConfigFactory,
    BookingRequestFactory,
    SystemConfigFactory
)


class TestDateValidator:
    """Test date validation functionality"""
    
    def test_valid_date_format(self):
        """Test valid date format validation"""
        valid_dates = ["2025-01-15", "2025-12-31", "2026-06-15"]
        for date in valid_dates:
            result = DateValidator.validate_date_format(date)
            assert result == date
    
    def test_invalid_date_format(self):
        """Test invalid date format validation"""
        invalid_dates = [
            "25-01-15",  # Wrong year format
            "2025/01/15",  # Wrong separators
            "2025-1-15",  # Missing zero padding
            "2025-13-01",  # Invalid month
            "2025-02-30",  # Invalid day
            "not-a-date",  # Not a date
            123,  # Not a string
            None  # None value
        ]
        
        for date in invalid_dates:
            with pytest.raises(CustomValidationError):
                DateValidator.validate_date_format(date)
    
    def test_future_date_validation(self):
        """Test future date validation"""
        # Valid future date
        future_date = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        result = DateValidator.validate_future_date(future_date)
        assert result == future_date
        
        # Invalid past date
        past_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        with pytest.raises(CustomValidationError, match="Date must be in the future"):
            DateValidator.validate_future_date(past_date)
        
        # Invalid today's date
        today = datetime.now().strftime('%Y-%m-%d')
        with pytest.raises(CustomValidationError, match="Date must be in the future"):
            DateValidator.validate_future_date(today)


class TestTimeValidator:
    """Test time validation functionality"""
    
    def test_valid_time_slot(self):
        """Test valid time slot validation"""
        valid_slots = [
            "De 08:00 AM a 09:00 AM",
            "De 12:00 PM a 01:00 PM",
            "De 07:00 PM a 08:00 PM",
            "De 11:30 AM a 12:30 PM"
        ]
        
        for slot in valid_slots:
            result = TimeValidator.validate_time_slot(slot)
            assert result == slot
    
    def test_invalid_time_slot_format(self):
        """Test invalid time slot format validation"""
        invalid_slots = [
            "8:00 AM to 9:00 AM",  # Wrong format
            "De 08:00 a 09:00",  # Missing AM/PM
            "De 25:00 AM a 09:00 AM",  # Invalid hour
            "De 08:60 AM a 09:00 AM",  # Invalid minute
            "From 08:00 AM to 09:00 AM",  # Wrong prefix
            123,  # Not a string
            None  # None value
        ]
        
        for slot in invalid_slots:
            with pytest.raises(CustomValidationError):
                TimeValidator.validate_time_slot(slot)
    
    def test_invalid_time_order(self):
        """Test that end time must be after start time"""
        invalid_slots = [
            "De 09:00 AM a 08:00 AM",  # End before start
            "De 08:00 AM a 08:00 AM",  # Same time
        ]
        
        for slot in invalid_slots:
            with pytest.raises(CustomValidationError, match="End time must be after start time"):
                TimeValidator.validate_time_slot(slot)


class TestCourtValidator:
    """Test court validation functionality"""
    
    def test_valid_court_id(self):
        """Test valid court ID validation"""
        valid_courts = [5, 7, 17, 19, 23]
        for court in valid_courts:
            result = CourtValidator.validate_court_id(court)
            assert result == court
    
    def test_invalid_court_id(self):
        """Test invalid court ID validation"""
        invalid_courts = [1, 3, 10, 25, 100, "5", None]
        
        for court in invalid_courts:
            with pytest.raises(CustomValidationError):
                CourtValidator.validate_court_id(court)
    
    def test_valid_court_list(self):
        """Test valid court list validation"""
        valid_lists = [
            [5],
            [5, 7],
            [5, 7, 17, 19, 23],
            [23, 17, 5]  # Order doesn't matter
        ]
        
        for court_list in valid_lists:
            result = CourtValidator.validate_court_list(court_list)
            assert result == court_list
    
    def test_invalid_court_list(self):
        """Test invalid court list validation"""
        invalid_lists = [
            [],  # Empty list
            [1, 2, 3],  # Invalid court IDs
            [5, 1],  # Mix of valid and invalid
            "not a list",  # Not a list
            None  # None value
        ]
        
        for court_list in invalid_lists:
            with pytest.raises(CustomValidationError):
                CourtValidator.validate_court_list(court_list)


class TestCredentialValidator:
    """Test credential validation functionality"""
    
    def test_valid_username(self):
        """Test valid username validation"""
        valid_usernames = [
            "john_doe",
            "user123",
            "test-user",
            "a.b.c",
            "user_123_test"
        ]
        
        for username in valid_usernames:
            result = CredentialValidator.validate_username(username)
            assert result == username
    
    def test_invalid_username(self):
        """Test invalid username validation"""
        invalid_usernames = [
            "ab",  # Too short
            "a" * 51,  # Too long
            "user@domain",  # Invalid character
            "user space",  # Space not allowed
            "",  # Empty
            123,  # Not a string
            None  # None value
        ]
        
        for username in invalid_usernames:
            with pytest.raises(CustomValidationError):
                CredentialValidator.validate_username(username)
    
    def test_valid_password(self):
        """Test valid password validation"""
        valid_passwords = [
            "Password123",
            "SecurePass1!",
            "MyPassword1",
            "Abc123def"
        ]
        
        for password in valid_passwords:
            result = CredentialValidator.validate_password(password)
            assert result == password
    
    def test_invalid_password(self):
        """Test invalid password validation"""
        invalid_passwords = [
            "short",  # Too short
            "nouppercase123",  # No uppercase
            "NOLOWERCASE123",  # No lowercase
            "NoDigitsHere",  # No digits
            "a" * 129,  # Too long
            "",  # Empty
            123,  # Not a string
            None  # None value
        ]
        
        for password in invalid_passwords:
            with pytest.raises(CustomValidationError):
                CredentialValidator.validate_password(password)


class TestEmailValidator:
    """Test email validation functionality"""
    
    def test_valid_email(self):
        """Test valid email validation"""
        valid_emails = [
            "test@example.com",
            "user.name@domain.co.uk",
            "user+tag@test.org",
            "123@numbers.com"
        ]
        
        for email in valid_emails:
            result = EmailValidator.validate_email(email)
            assert result == email
    
    def test_invalid_email(self):
        """Test invalid email validation"""
        invalid_emails = [
            "notanemail",  # No @ symbol
            "@domain.com",  # No local part
            "user@",  # No domain
            "user@domain",  # No TLD
            "user space@domain.com",  # Space in local part
            "a" * 250 + "@domain.com",  # Too long
            "",  # Empty
            123,  # Not a string
            None  # None value
        ]
        
        for email in invalid_emails:
            with pytest.raises(CustomValidationError):
                EmailValidator.validate_email(email)


class TestUserConfig:
    """Test UserConfig model validation and functionality"""
    
    def test_create_valid_user_config(self):
        """Test creating a valid UserConfig"""
        user = UserConfigFactory.create()
        assert user.user_id is not None
        assert user.username is not None
        assert user.email is not None
        assert isinstance(user.preferred_courts, list)
        assert len(user.preferred_courts) > 0
    
    def test_user_config_validation_errors(self):
        """Test UserConfig validation errors"""
        # Invalid username
        with pytest.raises(ValidationError):
            UserConfig(
                user_id="test",
                username="ab",  # Too short
                password="ValidPass123",
                email="test@test.com",
                first_name="Test",
                last_name="User"
            )
        
        # Invalid email
        with pytest.raises(ValidationError):
            UserConfig(
                user_id="test",
                username="testuser",
                password="ValidPass123",
                email="notanemail",  # Invalid email
                first_name="Test",
                last_name="User"
            )
        
        # Invalid password
        with pytest.raises(ValidationError):
            UserConfig(
                user_id="test",
                username="testuser",
                password="weak",  # Weak password
                email="test@test.com",
                first_name="Test",
                last_name="User"
            )
    
    def test_user_config_methods(self):
        """Test UserConfig methods"""
        user = UserConfigFactory.create(
            first_name="John",
            last_name="Doe",
            email="john@test.com",
            preferred_courts=[5, 7],
            max_bookings_per_day=3
        )
        
        # Test display methods
        assert user.get_display_name() == "John Doe"
        assert user.get_full_name() == "John Doe (john@test.com)"
        
        # Test preference methods
        assert user.is_court_preferred(5) is True
        assert user.is_court_preferred(17) is False
        
        # Test booking limit check
        assert user.can_book_more_today(2) is True
        assert user.can_book_more_today(3) is False
        
        # Test activation/deactivation
        user.deactivate()
        assert user.is_active is False
        
        user.activate()
        assert user.is_active is True
    
    def test_user_config_dynamodb_conversion(self):
        """Test UserConfig DynamoDB conversion"""
        user = UserConfigFactory.create()
        
        # Test to_dynamodb_item
        item = user.to_dynamodb_item()
        assert isinstance(item, dict)
        assert 'user_id' in item
        assert 'username' in item
        
        # Test get_primary_key
        primary_key = user.get_primary_key()
        assert primary_key == {"user_id": user.user_id}
        
        # Test get_table_name
        assert user.get_table_name() == "UserConfigs"


class TestBookingRequest:
    """Test BookingRequest model validation and functionality"""
    
    def test_create_valid_booking_request(self):
        """Test creating a valid BookingRequest"""
        booking = BookingRequestFactory.create()
        assert booking.request_id is not None
        assert booking.user_id is not None
        assert booking.booking_date is not None
        assert booking.time_slot is not None
        assert booking.court_id in [5, 7, 17, 19, 23]
        assert booking.status in BookingStatus.__members__.values()
    
    def test_booking_request_validation_errors(self):
        """Test BookingRequest validation errors"""
        # Invalid date (past date)
        past_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        with pytest.raises(ValidationError):
            BookingRequest(
                request_id="test",
                user_id="user1",
                booking_date=past_date,
                time_slot="De 08:00 AM a 09:00 AM",
                court_id=5
            )
        
        # Invalid time slot
        with pytest.raises(ValidationError):
            BookingRequest(
                request_id="test",
                user_id="user1",
                booking_date=(datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d'),
                time_slot="8:00 AM to 9:00 AM",  # Wrong format
                court_id=5
            )
        
        # Invalid court ID
        with pytest.raises(ValidationError):
            BookingRequest(
                request_id="test",
                user_id="user1",
                booking_date=(datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d'),
                time_slot="De 08:00 AM a 09:00 AM",
                court_id=99  # Invalid court
            )
    
    def test_booking_request_status_methods(self):
        """Test BookingRequest status check methods"""
        # Test pending status
        pending_booking = BookingRequestFactory.create_pending()
        assert pending_booking.is_pending() is True
        assert pending_booking.is_confirmed() is False
        
        # Test confirmed status
        confirmed_booking = BookingRequestFactory.create_confirmed()
        assert confirmed_booking.is_confirmed() is True
        assert confirmed_booking.is_pending() is False
        
        # Test failed status
        failed_booking = BookingRequestFactory.create_failed()
        assert failed_booking.is_failed() is True
    
    def test_booking_request_retry_logic(self):
        """Test BookingRequest retry functionality"""
        booking = BookingRequestFactory.create(
            auto_retry=True,
            max_retries=3,
            retry_count=1,
            status=BookingStatus.FAILED
        )
        
        # Should be able to retry
        assert booking.can_retry() is True
        
        # Increment retry count
        booking.increment_retry_count()
        assert booking.retry_count == 2
        
        # Still can retry
        assert booking.can_retry() is True
        
        # Max out retries
        booking.retry_count = 3
        assert booking.can_retry() is False
    
    def test_booking_request_status_transitions(self):
        """Test BookingRequest status transition methods"""
        booking = BookingRequestFactory.create_pending()
        
        # Mark as confirmed
        booking.mark_as_confirmed("CONF123")
        assert booking.is_confirmed() is True
        assert booking.confirmation_code == "CONF123"
        assert booking.confirmed_at is not None
        
        # Mark as failed
        booking2 = BookingRequestFactory.create_pending()
        booking2.mark_as_failed("Error message")
        assert booking2.is_failed() is True
        assert booking2.error_message == "Error message"
        
        # Mark as cancelled
        booking3 = BookingRequestFactory.create_pending()
        booking3.mark_as_cancelled()
        assert booking3.is_cancelled() is True
    
    def test_booking_request_dynamodb_conversion(self):
        """Test BookingRequest DynamoDB conversion"""
        booking = BookingRequestFactory.create()
        
        # Test to_dynamodb_item
        item = booking.to_dynamodb_item()
        assert isinstance(item, dict)
        assert 'request_id' in item
        assert 'user_id' in item
        
        # Test get_primary_key
        primary_key = booking.get_primary_key()
        assert primary_key == {"request_id": booking.request_id}
        
        # Test get_table_name
        assert booking.get_table_name() == "BookingRequests"


class TestSystemConfig:
    """Test SystemConfig model validation and functionality"""
    
    def test_create_valid_system_config(self):
        """Test creating a valid SystemConfig"""
        config = SystemConfigFactory.create()
        assert config.config_key is not None
        assert config.config_value is not None
        assert config.value_type in ConfigValueType.__members__.values()
        assert config.category in ConfigCategory.__members__.values()
    
    def test_system_config_type_validation(self):
        """Test SystemConfig type validation"""
        # String config
        string_config = SystemConfigFactory.create_string_config("test_value")
        assert string_config.value_type == ConfigValueType.STRING
        assert string_config.get_typed_value() == "test_value"
        
        # Integer config
        int_config = SystemConfigFactory.create_integer_config(42)
        assert int_config.value_type == ConfigValueType.INTEGER
        assert int_config.get_typed_value() == 42
        
        # Boolean config
        bool_config = SystemConfigFactory.create_boolean_config(True)
        assert bool_config.value_type == ConfigValueType.BOOLEAN
        assert bool_config.get_typed_value() is True
    
    def test_system_config_validation_errors(self):
        """Test SystemConfig validation errors"""
        # Invalid config key
        with pytest.raises(ValidationError):
            SystemConfig(
                config_key="",  # Empty key
                config_value="test",
                value_type=ConfigValueType.STRING,
                category=ConfigCategory.SYSTEM,
                description="Test config"
            )
        
        # Type mismatch - this validation happens at runtime, not during creation
        config = SystemConfig(
            config_key="test_config",
            config_value="not_an_integer",  # String value
            value_type=ConfigValueType.INTEGER,  # But integer type
            category=ConfigCategory.SYSTEM,
            description="Test config"
        )
        # The type validation should fail when we try to use the typed value
        with pytest.raises(ValueError):
            config.get_typed_value()
    
    def test_system_config_constraints(self):
        """Test SystemConfig constraint validation"""
        config = SystemConfigFactory.create_integer_config(
            value=50,
            min_value=1,
            max_value=100
        )
        
        # Valid value within constraints
        assert config.validate_value_against_constraints(75) is True
        
        # Invalid value below minimum
        assert config.validate_value_against_constraints(0) is False
        
        # Invalid value above maximum
        assert config.validate_value_against_constraints(150) is False
    
    def test_system_config_update_value(self):
        """Test SystemConfig value updates"""
        config = SystemConfigFactory.create_integer_config(
            value=50,
            min_value=1,
            max_value=100
        )
        
        # Valid update
        config.update_value(75)
        assert config.config_value == 75
        
        # Invalid update
        with pytest.raises(ValueError):
            config.update_value(150)  # Above max
    
    def test_system_config_reset_to_default(self):
        """Test SystemConfig reset to default"""
        config = SystemConfigFactory.create_string_config("current_value")
        config.default_value = "default_value"
        
        config.reset_to_default()
        assert config.config_value == "default_value"
    
    def test_system_config_dynamodb_conversion(self):
        """Test SystemConfig DynamoDB conversion"""
        config = SystemConfigFactory.create()
        
        # Test to_dynamodb_item
        item = config.to_dynamodb_item()
        assert isinstance(item, dict)
        assert 'config_key' in item
        assert 'config_value' in item
        
        # Test get_primary_key
        primary_key = config.get_primary_key()
        assert primary_key == {"config_key": config.config_key}
        
        # Test get_table_name
        assert config.get_table_name() == "SystemConfig"


class TestFactories:
    """Test factory methods"""
    
    def test_user_config_factory(self):
        """Test UserConfigFactory methods"""
        # Test basic creation
        user = UserConfigFactory.create()
        assert user.user_id is not None
        assert user.is_active is True
        
        # Test minimal creation
        minimal_user = UserConfigFactory.create_minimal()
        assert minimal_user.first_name == "Test"
        assert minimal_user.last_name == "User"
        
        # Test admin creation
        admin = UserConfigFactory.create_admin()
        assert "admin" in admin.user_id
        assert len(admin.preferred_courts) == 5  # All courts
        
        # Test batch creation
        users = UserConfigFactory.create_batch(3)
        assert len(users) == 3
        assert all(isinstance(user, UserConfig) for user in users)
    
    def test_booking_request_factory(self):
        """Test BookingRequestFactory methods"""
        # Test basic creation
        booking = BookingRequestFactory.create()
        assert booking.request_id is not None
        
        # Test status-specific creation
        pending = BookingRequestFactory.create_pending()
        assert pending.status == BookingStatus.PENDING
        
        confirmed = BookingRequestFactory.create_confirmed()
        assert confirmed.status == BookingStatus.CONFIRMED
        assert confirmed.confirmation_code is not None
        
        failed = BookingRequestFactory.create_failed()
        assert failed.status == BookingStatus.FAILED
        assert failed.error_message is not None
        
        # Test batch creation
        bookings = BookingRequestFactory.create_batch(5)
        assert len(bookings) == 5
        assert all(isinstance(booking, BookingRequest) for booking in bookings)
    
    def test_system_config_factory(self):
        """Test SystemConfigFactory methods"""
        # Test basic creation
        config = SystemConfigFactory.create()
        assert config.config_key is not None
        
        # Test type-specific creation
        string_config = SystemConfigFactory.create_string_config()
        assert string_config.value_type == ConfigValueType.STRING
        
        int_config = SystemConfigFactory.create_integer_config()
        assert int_config.value_type == ConfigValueType.INTEGER
        
        # Test predefined configs
        courts_config = SystemConfigFactory.create_courts_config()
        assert courts_config.config_key == "available_courts"
        assert courts_config.config_value == [5, 7, 17, 19, 23]
        
        # Test batch creation
        configs = SystemConfigFactory.create_batch(3)
        assert len(configs) == 3
        assert all(isinstance(config, SystemConfig) for config in configs)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])