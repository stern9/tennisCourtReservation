# ABOUTME: Unit tests for DynamoDB operations and CRUD functionality
# ABOUTME: Tests UserConfig, BookingRequest, and SystemConfig operations

import pytest
import os
import uuid
from datetime import datetime, timezone
from src.database.operations import UserConfigOperations, BookingRequestOperations, SystemConfigOperations
from src.database.schemas import TableManager

# Set up test environment
# Only set local endpoint if not using AWS and endpoint not already set
if not os.getenv('USE_AWS_DYNAMODB') and not os.getenv('DYNAMODB_LOCAL_ENDPOINT'):
    os.environ['DYNAMODB_LOCAL_ENDPOINT'] = 'http://localhost:8000'

@pytest.fixture(scope="session")
def setup_test_tables():
    """Set up test tables before running tests"""
    table_manager = TableManager()
    
    # Only clean up for local development, not AWS
    if not os.getenv('USE_AWS_DYNAMODB'):
        # Clean up any existing tables
        table_manager.delete_all_tables()
    
    # Create fresh tables (or use existing ones for AWS)
    success = table_manager.create_tables()
    assert success, "Failed to create test tables"
    
    yield
    
    # Only cleanup after tests for local development
    if not os.getenv('USE_AWS_DYNAMODB'):
        table_manager.delete_all_tables()

@pytest.fixture
def user_config_ops():
    """UserConfigOperations instance for testing"""
    return UserConfigOperations()

@pytest.fixture
def booking_ops():
    """BookingRequestOperations instance for testing"""
    return BookingRequestOperations()

@pytest.fixture
def system_config_ops():
    """SystemConfigOperations instance for testing"""
    return SystemConfigOperations()

@pytest.fixture
def test_user_id():
    """Generate unique test user ID"""
    return f"test-user-{str(uuid.uuid4())[:8]}"

@pytest.fixture
def test_user_config():
    """Test user configuration data"""
    return {
        'username': 'test_user_123',
        'password': 'secure_password',
        'website_url': 'https://example-tennis.com',
        'venue': 'Test Tennis Club',
        'preferred_court': 7,
        'default_date': '2025-04-01',
        'default_time': 'De 08:00 AM a 09:00 AM',
        'headless': True
    }

@pytest.fixture
def test_booking_request():
    """Test booking request data"""
    return {
        'court_id': 7,
        'date': '2025-04-01',
        'time_slot': 'De 08:00 AM a 09:00 AM',
        'venue': 'Test Tennis Club'
    }

class TestUserConfigOperations:
    """Test UserConfig CRUD operations"""
    
    def test_create_user_config(self, setup_test_tables, user_config_ops, test_user_id, test_user_config):
        """Test creating a user configuration"""
        result = user_config_ops.create_user_config(test_user_id, test_user_config)
        assert result is True
        
        # Verify the config was created
        config = user_config_ops.get_user_config(test_user_id)
        assert config is not None
        assert config['userId'] == test_user_id
        assert config['username'] == test_user_config['username']
        assert config['venue'] == test_user_config['venue']
        assert config['headless'] == test_user_config['headless']
        assert 'createdAt' in config
        assert 'updatedAt' in config
        assert config['version'] == 1
    
    def test_get_user_config_not_found(self, setup_test_tables, user_config_ops):
        """Test getting a non-existent user configuration"""
        config = user_config_ops.get_user_config('non-existent-user')
        assert config is None
    
    def test_update_user_config(self, setup_test_tables, user_config_ops, test_user_id, test_user_config):
        """Test updating a user configuration"""
        # Create initial config
        user_config_ops.create_user_config(test_user_id, test_user_config)
        
        # Update config
        updates = {
            'venue': 'Updated Tennis Club',
            'preferred_court': 17,
            'headless': False
        }
        
        result = user_config_ops.update_user_config(test_user_id, updates)
        assert result is True
        
        # Verify updates
        config = user_config_ops.get_user_config(test_user_id)
        assert config['venue'] == 'Updated Tennis Club'
        assert config['preferredCourt'] == 17
        assert config['headless'] is False
        assert config['version'] == 2
        assert config['username'] == test_user_config['username']  # Unchanged
    
    def test_delete_user_config(self, setup_test_tables, user_config_ops, test_user_id, test_user_config):
        """Test deleting a user configuration"""
        # Create config
        user_config_ops.create_user_config(test_user_id, test_user_config)
        
        # Verify it exists
        config = user_config_ops.get_user_config(test_user_id)
        assert config is not None
        
        # Delete config
        result = user_config_ops.delete_user_config(test_user_id)
        assert result is True
        
        # Verify it's gone
        config = user_config_ops.get_user_config(test_user_id)
        assert config is None

class TestBookingRequestOperations:
    """Test BookingRequest CRUD operations"""
    
    def test_create_booking_request(self, setup_test_tables, booking_ops, test_user_id, test_booking_request):
        """Test creating a booking request"""
        request_id = booking_ops.create_booking_request(test_user_id, test_booking_request)
        assert request_id is not None
        assert isinstance(request_id, str)
        
        # Verify the request was created
        request = booking_ops.get_booking_request(request_id, test_user_id)
        assert request is not None
        assert request['requestId'] == request_id
        assert request['userId'] == test_user_id
        assert request['courtId'] == test_booking_request['court_id']
        assert request['date'] == test_booking_request['date']
        assert request['timeSlot'] == test_booking_request['time_slot']
        assert request['status'] == 'pending'
        assert 'createdAt' in request
        assert 'ttl' in request
    
    def test_get_booking_request_not_found(self, setup_test_tables, booking_ops, test_user_id):
        """Test getting a non-existent booking request"""
        request = booking_ops.get_booking_request('non-existent-id', test_user_id)
        assert request is None
    
    def test_update_booking_status(self, setup_test_tables, booking_ops, test_user_id, test_booking_request):
        """Test updating booking request status"""
        # Create request
        request_id = booking_ops.create_booking_request(test_user_id, test_booking_request)
        
        # Update status
        result_data = {'screenshot_path': '/path/to/screenshot.png', 'confirmation_number': 'ABC123'}
        result = booking_ops.update_booking_status(request_id, test_user_id, 'completed', result_data)
        assert result is True
        
        # Verify update
        request = booking_ops.get_booking_request(request_id, test_user_id)
        assert request['status'] == 'completed'
        assert request['resultData'] == result_data
        assert 'updatedAt' in request
    
    def test_get_user_booking_requests(self, setup_test_tables, booking_ops, test_user_id, test_booking_request):
        """Test getting user's booking requests"""
        # Create multiple requests
        request_ids = []
        for i in range(3):
            request_data = test_booking_request.copy()
            request_data['court_id'] = 7 + i
            request_id = booking_ops.create_booking_request(test_user_id, request_data)
            request_ids.append(request_id)
        
        # Get user's requests
        requests = booking_ops.get_user_booking_requests(test_user_id)
        assert len(requests) == 3
        
        # Verify all requests belong to the user
        for request in requests:
            assert request['userId'] == test_user_id
            assert request['requestId'] in request_ids
    
    def test_get_requests_by_status(self, setup_test_tables, booking_ops, test_user_id, test_booking_request):
        """Test getting requests by status"""
        # Create requests with different statuses
        request_id1 = booking_ops.create_booking_request(test_user_id, test_booking_request)
        request_id2 = booking_ops.create_booking_request(test_user_id, test_booking_request)
        
        # Update one to completed
        booking_ops.update_booking_status(request_id1, test_user_id, 'completed')
        
        # Get pending requests
        pending_requests = booking_ops.get_requests_by_status('pending')
        assert len(pending_requests) >= 1
        assert all(req['status'] == 'pending' for req in pending_requests)
        
        # Get completed requests
        completed_requests = booking_ops.get_requests_by_status('completed')
        assert len(completed_requests) >= 1
        assert all(req['status'] == 'completed' for req in completed_requests)

class TestSystemConfigOperations:
    """Test SystemConfig CRUD operations"""
    
    def test_set_and_get_config(self, setup_test_tables, system_config_ops):
        """Test setting and getting system configuration"""
        # Set config
        result = system_config_ops.set_config('test_key', 'test_value', 'Test configuration')
        assert result is True
        
        # Get config
        value = system_config_ops.get_config('test_key')
        assert value == 'test_value'
    
    def test_set_config_with_complex_data(self, setup_test_tables, system_config_ops):
        """Test setting configuration with complex data types"""
        complex_data = {
            'list': [1, 2, 3, 4, 5],
            'dict': {'nested': 'value'},
            'bool': True,
            'number': 42
        }
        
        # Set complex config
        result = system_config_ops.set_config('complex_key', complex_data, 'Complex configuration')
        assert result is True
        
        # Get and verify
        value = system_config_ops.get_config('complex_key')
        assert value == complex_data
    
    def test_get_config_not_found(self, setup_test_tables, system_config_ops):
        """Test getting non-existent configuration"""
        value = system_config_ops.get_config('non_existent_key')
        assert value is None
    
    def test_get_all_configs(self, setup_test_tables, system_config_ops):
        """Test getting all configurations"""
        # Set multiple configs
        configs = {
            'key1': 'value1',
            'key2': 'value2',
            'key3': {'nested': 'value3'}
        }
        
        for key, value in configs.items():
            system_config_ops.set_config(key, value, f'Description for {key}')
        
        # Get all configs
        all_configs = system_config_ops.get_all_configs()
        
        # Verify all configs are present
        for key, value in configs.items():
            assert key in all_configs
            assert all_configs[key] == value
    
    def test_delete_config(self, setup_test_tables, system_config_ops):
        """Test deleting configuration"""
        # Set config
        system_config_ops.set_config('delete_me', 'delete_value', 'To be deleted')
        
        # Verify it exists
        value = system_config_ops.get_config('delete_me')
        assert value == 'delete_value'
        
        # Delete config
        result = system_config_ops.delete_config('delete_me')
        assert result is True
        
        # Verify it's gone
        value = system_config_ops.get_config('delete_me')
        assert value is None

class TestDatabaseIntegration:
    """Integration tests for database operations"""
    
    def test_user_config_and_booking_request_integration(self, setup_test_tables, user_config_ops, booking_ops, test_user_id, test_user_config, test_booking_request):
        """Test integration between user config and booking requests"""
        # Create user config
        user_config_ops.create_user_config(test_user_id, test_user_config)
        
        # Create booking request
        request_id = booking_ops.create_booking_request(test_user_id, test_booking_request)
        
        # Verify both exist and are linked
        config = user_config_ops.get_user_config(test_user_id)
        request = booking_ops.get_booking_request(request_id, test_user_id)
        
        assert config is not None
        assert request is not None
        assert config['userId'] == request['userId']
        assert config['venue'] == request['venue']
    
    def test_system_config_for_validation(self, setup_test_tables, system_config_ops):
        """Test using system config for validation"""
        # Set validation configs
        system_config_ops.set_config('available_courts', [5, 7, 17, 19, 23], 'Available courts')
        system_config_ops.set_config('available_time_slots', [
            'De 08:00 AM a 09:00 AM',
            'De 09:00 AM a 10:00 AM',
            'De 10:00 AM a 11:00 AM'
        ], 'Available time slots')
        
        # Get configs for validation
        available_courts = system_config_ops.get_config('available_courts')
        available_time_slots = system_config_ops.get_config('available_time_slots')
        
        # Verify validation data
        assert 7 in available_courts
        assert 99 not in available_courts
        assert 'De 08:00 AM a 09:00 AM' in available_time_slots
        assert 'De 11:00 PM a 12:00 AM' not in available_time_slots