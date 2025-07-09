# ABOUTME: Comprehensive tests for tennis script integration with DynamoDB configuration loading
# ABOUTME: Tests configuration loading, court mapping, validation, and error handling scenarios

import pytest
import os
import sys
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import tennis
from src.models import BookingRequest as BookingRequestModel, EncryptedUserConfig
from src.api.models import BookingStatus

class TestTennisScriptConfiguration:
    """Test suite for tennis script configuration loading and validation"""
    
    def setup_method(self):
        """Set up test environment before each test"""
        self.test_user_id = "test_user_123"
        # Use a future date for booking_date validation
        self.future_date = (datetime.now() + timedelta(days=5)).strftime("%Y-%m-%d")
        self.test_booking_request = BookingRequestModel(
            request_id="req_123",
            user_id=self.test_user_id,
            court_id=1,
            booking_date=self.future_date,
            time_slot="De 09:00 AM a 10:00 AM",
            status=BookingStatus.PENDING,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # Create a mock user config instead of actual EncryptedUserConfig
        self.test_user_config = Mock()
        self.test_user_config.user_id = self.test_user_id
        self.test_user_config.username = "testuser"
        self.test_user_config.password = "testpass123"  # Already "decrypted" in mock
        # Set attributes directly on the mock object
        self.test_user_config.website_url = "https://parquesdelsol.sasweb.net/"
        self.test_user_config.venue = "Parques del Sol"
        self.test_user_config.headless = True
        self.test_user_config.preferred_courts = [1]
        self.test_user_config.default_date = "2025-04-01"
        self.test_user_config.default_time = "De 08:00 AM a 09:00 AM"
        
    @patch('tennis.DYNAMODB_AVAILABLE', True)
    @patch('tennis.load_config_from_dynamodb')
    @patch('tennis.validate_config')
    def test_load_config_from_dynamodb_success(self, mock_validate_config, mock_load_config_from_dynamodb):
        """Test successful configuration loading from DynamoDB"""
        # Setup mock to return expected configuration
        expected_config = {
            'username': 'testuser',
            'password': 'testpass123',
            'website_url': 'https://parquesdelsol.sasweb.net/',
            'venue': 'Parques del Sol',
            'headless': True,
            'area_value': 5,  # Court 1 -> Area 5
            'date': self.future_date,
            'time_slot': 'De 09:00 AM a 10:00 AM'
        }
        mock_load_config_from_dynamodb.return_value = expected_config
        
        # Test configuration loading
        config = tennis.load_config(self.test_user_id, self.test_booking_request)
        
        # Verify results
        assert config['username'] == 'testuser'
        assert config['password'] == 'testpass123'
        assert config['website_url'] == 'https://parquesdelsol.sasweb.net/'
        assert config['venue'] == 'Parques del Sol'
        assert config['headless'] == True
        assert config['area_value'] == 5  # Court 1 -> Area 5
        assert config['date'] == self.future_date
        assert config['time_slot'] == 'De 09:00 AM a 10:00 AM'
        
        # Verify DynamoDB function was called correctly
        mock_load_config_from_dynamodb.assert_called_once_with(self.test_user_id, self.test_booking_request)
        mock_validate_config.assert_called_once_with(expected_config)
        
    @patch('tennis.DYNAMODB_AVAILABLE', True)
    @patch('tennis.EncryptedUserConfigDAO')
    def test_load_config_court_mapping(self, mock_dao_class):
        """Test court ID to area value mapping"""
        mock_dao = Mock()
        mock_dao.get_user.return_value = self.test_user_config
        mock_dao_class.return_value = mock_dao
        
        # Test Court 1 -> Area 5
        booking_court_1 = BookingRequestModel(
            request_id="req_1",
            user_id=self.test_user_id,
            court_id=1,
            booking_date=self.future_date,
            time_slot="De 09:00 AM a 10:00 AM",
            status=BookingStatus.PENDING,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        config = tennis.load_config_from_dynamodb(self.test_user_id, booking_court_1)
        assert config['area_value'] == 5
        
        # Test Court 2 -> Area 7
        booking_court_2 = BookingRequestModel(
            request_id="req_2",
            user_id=self.test_user_id,
            court_id=2,
            booking_date=self.future_date,
            time_slot="De 09:00 AM a 10:00 AM",
            status=BookingStatus.PENDING,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        config = tennis.load_config_from_dynamodb(self.test_user_id, booking_court_2)
        assert config['area_value'] == 7
        
    @patch('tennis.DYNAMODB_AVAILABLE', True)
    @patch('tennis.EncryptedUserConfigDAO')
    def test_load_config_invalid_court_id(self, mock_dao_class):
        """Test error handling for invalid court ID"""
        mock_dao = Mock()
        mock_dao.get_user.return_value = self.test_user_config
        mock_dao_class.return_value = mock_dao
        
        # Test invalid court ID
        booking_invalid_court = BookingRequestModel(
            request_id="req_invalid",
            user_id=self.test_user_id,
            court_id=999,  # Invalid court ID
            booking_date=self.future_date,
            time_slot="De 09:00 AM a 10:00 AM",
            status=BookingStatus.PENDING,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        with pytest.raises(ValueError, match="Invalid court_id: 999"):
            tennis.load_config_from_dynamodb(self.test_user_id, booking_invalid_court)
            
    @patch('tennis.DYNAMODB_AVAILABLE', True)
    @patch('tennis.EncryptedUserConfigDAO')
    def test_load_config_user_not_found(self, mock_dao_class):
        """Test error handling when user configuration not found"""
        mock_dao = Mock()
        mock_dao.get_user.return_value = None
        mock_dao_class.return_value = mock_dao
        
        with pytest.raises(ValueError, match="User configuration not found for user_id: test_user_123"):
            tennis.load_config_from_dynamodb(self.test_user_id, self.test_booking_request)
            
    @patch('tennis.DYNAMODB_AVAILABLE', True)
    @patch('tennis.EncryptedUserConfigDAO')
    def test_load_config_without_booking_request(self, mock_dao_class):
        """Test configuration loading without specific booking request"""
        mock_dao = Mock()
        mock_dao.get_user.return_value = self.test_user_config
        mock_dao_class.return_value = mock_dao
        
        # Test without booking request - should use user defaults
        config = tennis.load_config_from_dynamodb(self.test_user_id, None)
        
        assert config['area_value'] == 5  # Default to first preferred court (Court 1)
        assert config['date'] == '2025-04-01'  # User's default date
        assert config['time_slot'] == 'De 08:00 AM a 09:00 AM'  # User's default time
        
    @patch.dict(os.environ, {
        'TENNIS_USERNAME': 'env_user',
        'TENNIS_PASSWORD': 'env_pass',
        'TENNIS_WEBSITE_URL': 'https://env.example.com',
        'TENNIS_VENUE': 'Env Venue',
        'TENNIS_AREA_VALUE': '7',
        'TENNIS_DATE': '2025-05-01',
        'TENNIS_TIME_SLOT': 'De 10:00 AM a 11:00 AM',
        'TENNIS_HEADLESS': 'true'
    })
    def test_load_config_from_env(self):
        """Test configuration loading from environment variables"""
        config = tennis.load_config_from_env()
        
        assert config['username'] == 'env_user'
        assert config['password'] == 'env_pass'
        assert config['website_url'] == 'https://env.example.com'
        assert config['venue'] == 'Env Venue'
        assert config['area_value'] == 7
        assert config['date'] == '2025-05-01'
        assert config['time_slot'] == 'De 10:00 AM a 11:00 AM'
        assert config['headless'] == True
        
    @patch('tennis.DYNAMODB_AVAILABLE', True)
    @patch('tennis.load_config_from_dynamodb')
    @patch('tennis.load_config_from_env')
    def test_load_config_fallback_to_env(self, mock_env_config, mock_db_config):
        """Test fallback to environment variables when DynamoDB fails"""
        # Setup mocks
        mock_db_config.side_effect = Exception("DynamoDB connection failed")
        mock_env_config.return_value = {
            'username': 'fallback_user',
            'password': 'fallback_pass',
            'website_url': 'https://fallback.example.com',
            'venue': 'Fallback Venue',
            'area_value': 5,
            'date': '2025-04-01',
            'time_slot': 'De 09:00 AM a 10:00 AM',
            'headless': False
        }
        
        with patch('tennis.validate_config'):
            config = tennis.load_config(self.test_user_id, self.test_booking_request)
            
        # Verify fallback was used
        assert config['username'] == 'fallback_user'
        mock_env_config.assert_called_once()
        
    @patch('tennis.DYNAMODB_AVAILABLE', False)
    @patch('tennis.load_config_from_env')
    def test_load_config_dynamodb_not_available(self, mock_env_config):
        """Test configuration loading when DynamoDB is not available"""
        mock_env_config.return_value = {
            'username': 'env_only_user',
            'password': 'env_only_pass',
            'website_url': 'https://env-only.example.com',
            'venue': 'Env Only Venue',
            'area_value': 5,
            'date': '2025-04-01',
            'time_slot': 'De 09:00 AM a 10:00 AM',
            'headless': False
        }
        
        with patch('tennis.validate_config'):
            config = tennis.load_config(self.test_user_id, self.test_booking_request)
            
        # Verify environment config was used
        assert config['username'] == 'env_only_user'
        mock_env_config.assert_called_once()
        
    def test_validate_config_success(self):
        """Test successful configuration validation"""
        valid_config = {
            'username': 'testuser',
            'password': 'testpass',
            'website_url': 'https://example.com',
            'area_value': 5,
            'date': '2025-04-01',
            'time_slot': 'De 09:00 AM a 10:00 AM'
        }
        
        # Should not raise any exception
        tennis.validate_config(valid_config)
        
    def test_validate_config_missing_fields(self):
        """Test configuration validation with missing required fields"""
        invalid_config = {
            'username': 'testuser',
            # Missing password, website_url, area_value, date, time_slot
        }
        
        with pytest.raises(ValueError, match="Missing required configuration fields"):
            tennis.validate_config(invalid_config)
            
    def test_validate_config_invalid_area_value(self):
        """Test configuration validation with invalid area value"""
        invalid_config = {
            'username': 'testuser',
            'password': 'testpass',
            'website_url': 'https://example.com',
            'area_value': 999,  # Invalid area value
            'date': '2025-04-01',
            'time_slot': 'De 09:00 AM a 10:00 AM'
        }
        
        with pytest.raises(ValueError, match="Invalid area_value: 999"):
            tennis.validate_config(invalid_config)
            
    def test_validate_config_valid_area_values(self):
        """Test configuration validation with valid area values"""
        for area_value in [5, 7]:  # Only tennis courts
            valid_config = {
                'username': 'testuser',
                'password': 'testpass',
                'website_url': 'https://example.com',
                'area_value': area_value,
                'date': '2025-04-01',
                'time_slot': 'De 09:00 AM a 10:00 AM'
            }
            
            # Should not raise any exception
            tennis.validate_config(valid_config)


class TestTennisScriptExecution:
    """Test suite for tennis script execution and reservation functionality"""
    
    def setup_method(self):
        """Set up test environment before each test"""
        self.test_user_id = "test_user_123"
        # Use a future date for booking_date validation
        self.future_date = (datetime.now() + timedelta(days=5)).strftime("%Y-%m-%d")
        self.test_booking_request = BookingRequestModel(
            request_id="req_123",
            user_id=self.test_user_id,
            court_id=1,
            booking_date=self.future_date,
            time_slot="De 09:00 AM a 10:00 AM",
            status=BookingStatus.PENDING,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
    @patch('tennis.setup_driver')
    @patch('tennis.load_config')
    def test_make_reservation_success(self, mock_load_config, mock_setup_driver):
        """Test successful reservation execution"""
        # Setup mocks
        mock_config = {
            'username': 'testuser',
            'password': 'testpass',
            'website_url': 'https://parquesdelsol.sasweb.net/',
            'venue': 'Parques del Sol',
            'area_value': 5,
            'date': self.future_date,
            'time_slot': 'De 09:00 AM a 10:00 AM',
            'headless': True
        }
        mock_load_config.return_value = mock_config
        
        mock_driver = Mock()
        mock_setup_driver.return_value = mock_driver
        
        # Mock WebDriver elements
        mock_driver.find_element.return_value = Mock()
        mock_driver.save_screenshot.return_value = None
        
        # Mock WebDriverWait
        with patch('tennis.WebDriverWait') as mock_wait:
            mock_wait.return_value.until.return_value = Mock()
            
            # Mock os.makedirs
            with patch('os.makedirs'):
                result = tennis.make_reservation(self.test_user_id, self.test_booking_request)
                
        # Verify success
        assert result == True
        mock_load_config.assert_called_once_with(self.test_user_id, self.test_booking_request)
        mock_setup_driver.assert_called_once_with(mock_config)
        mock_driver.get.assert_called_once_with('https://parquesdelsol.sasweb.net/')
        mock_driver.quit.assert_called_once()
        
    @patch('tennis.setup_driver')
    @patch('tennis.load_config')
    def test_make_reservation_timeout_error(self, mock_load_config, mock_setup_driver):
        """Test reservation failure due to timeout"""
        # Setup mocks
        mock_config = {
            'username': 'testuser',
            'password': 'testpass',
            'website_url': 'https://parquesdelsol.sasweb.net/',
            'venue': 'Parques del Sol',
            'area_value': 5,
            'date': self.future_date,
            'time_slot': 'De 09:00 AM a 10:00 AM',
            'headless': True
        }
        mock_load_config.return_value = mock_config
        
        mock_driver = Mock()
        mock_setup_driver.return_value = mock_driver
        
        # Mock timeout exception
        from selenium.common.exceptions import TimeoutException
        with patch('tennis.WebDriverWait') as mock_wait:
            mock_wait.return_value.until.side_effect = TimeoutException("Element not found")
            
            result = tennis.make_reservation(self.test_user_id, self.test_booking_request)
            
        # Verify failure
        assert result == False
        mock_driver.quit.assert_called_once()
        
    @patch('tennis.setup_driver')
    @patch('tennis.load_config')
    def test_make_reservation_webdriver_error(self, mock_load_config, mock_setup_driver):
        """Test reservation failure due to WebDriver error"""
        # Setup mocks
        mock_config = {
            'username': 'testuser',
            'password': 'testpass',
            'website_url': 'https://parquesdelsol.sasweb.net/',
            'venue': 'Parques del Sol',
            'area_value': 5,
            'date': self.future_date,
            'time_slot': 'De 09:00 AM a 10:00 AM',
            'headless': True
        }
        mock_load_config.return_value = mock_config
        
        from selenium.common.exceptions import WebDriverException
        mock_setup_driver.side_effect = WebDriverException("Driver initialization failed")
        
        result = tennis.make_reservation(self.test_user_id, self.test_booking_request)
        
        # Verify failure
        assert result == False
        
    @patch('tennis.setup_driver')
    @patch('tennis.load_config')
    def test_make_reservation_config_error(self, mock_load_config, mock_setup_driver):
        """Test reservation failure due to configuration error"""
        # Setup mocks
        mock_load_config.side_effect = ValueError("Configuration validation failed")
        
        result = tennis.make_reservation(self.test_user_id, self.test_booking_request)
        
        # Verify failure
        assert result == False
        mock_setup_driver.assert_not_called()
        
    @patch('tennis.ChromeDriverManager')
    @patch('tennis.webdriver.Chrome')
    def test_setup_driver_success(self, mock_chrome, mock_driver_manager):
        """Test successful WebDriver setup"""
        # Setup mocks
        mock_driver_manager.return_value.install.return_value = "/path/to/chromedriver"
        mock_driver = Mock()
        mock_chrome.return_value = mock_driver
        
        config = {
            'headless': True
        }
        
        result = tennis.setup_driver(config)
        
        # Verify setup
        assert result == mock_driver
        mock_chrome.assert_called_once()
        
    @patch('tennis.ChromeDriverManager')
    def test_setup_driver_failure(self, mock_driver_manager):
        """Test WebDriver setup failure"""
        # Setup mocks
        from selenium.common.exceptions import WebDriverException
        mock_driver_manager.return_value.install.side_effect = WebDriverException("Driver not found")
        
        config = {
            'headless': True
        }
        
        with pytest.raises(WebDriverException):
            tennis.setup_driver(config)


class TestTennisScriptIntegration:
    """Integration tests for tennis script with booking processor"""
    
    def setup_method(self):
        """Set up test environment before each test"""
        self.test_user_id = "test_user_123"
        # Use a future date for booking_date validation
        self.future_date = (datetime.now() + timedelta(days=5)).strftime("%Y-%m-%d")
        self.test_booking_request = BookingRequestModel(
            request_id="req_123",
            user_id=self.test_user_id,
            court_id=1,
            booking_date=self.future_date,
            time_slot="De 09:00 AM a 10:00 AM",
            status=BookingStatus.PENDING,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
    @patch('tennis.make_reservation')
    def test_booking_processor_integration(self, mock_make_reservation):
        """Test integration between booking processor and tennis script"""
        from src.api.services.tennis_booking_processor import TennisBookingProcessor
        
        # Setup mock
        mock_make_reservation.return_value = True
        
        # Create processor instance
        processor = TennisBookingProcessor()
        
        # Mock dependencies
        with patch.object(processor, 'booking_dao') as mock_dao:
            mock_dao.get_requests_by_status.return_value = [self.test_booking_request]
            
            with patch.object(processor, '_handle_booking_success') as mock_success:
                # Process booking
                processor._execute_booking(self.test_booking_request)
                
                # Verify tennis script was called
                mock_make_reservation.assert_called_once_with(self.test_user_id, self.test_booking_request)
                mock_success.assert_called_once_with(self.test_booking_request)
                
    @patch('tennis.make_reservation')
    def test_booking_processor_failure_handling(self, mock_make_reservation):
        """Test booking processor failure handling"""
        from src.api.services.tennis_booking_processor import TennisBookingProcessor
        
        # Setup mock
        mock_make_reservation.return_value = False
        
        # Create processor instance
        processor = TennisBookingProcessor()
        
        # Mock dependencies
        with patch.object(processor, '_handle_booking_failure') as mock_failure:
            # Process booking
            processor._execute_booking(self.test_booking_request)
            
            # Verify failure was handled
            mock_make_reservation.assert_called_once_with(self.test_user_id, self.test_booking_request)
            mock_failure.assert_called_once_with(self.test_booking_request, "Tennis script returned failure")


if __name__ == '__main__':
    pytest.main([__file__, '-v'])