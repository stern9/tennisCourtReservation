# ABOUTME: Script to set up DynamoDB tables and populate test data
# ABOUTME: Creates tables, initializes system config, and adds sample data for development

import os
import logging
from database.schemas import TableManager
from database.operations import UserConfigOperations, BookingRequestOperations, SystemConfigOperations

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def setup_database():
    """Set up DynamoDB tables and initial data"""
    logger.info("Starting database setup...")
    
    # Create tables
    table_manager = TableManager()
    if not table_manager.create_tables():
        logger.error("Failed to create tables")
        return False
    
    # Initialize system configuration
    system_config = SystemConfigOperations()
    
    # Set default system configurations
    configs = {
        'available_courts': [1, 2],
        'available_time_slots': [
            'De 08:00 AM a 09:00 AM',
            'De 09:00 AM a 10:00 AM',
            'De 10:00 AM a 11:00 AM',
            'De 11:00 AM a 12:00 PM',
            'De 12:00 PM a 01:00 PM',
            'De 01:00 PM a 02:00 PM',
            'De 02:00 PM a 03:00 PM',
            'De 03:00 PM a 04:00 PM',
            'De 04:00 PM a 05:00 PM',
            'De 05:00 PM a 06:00 PM',
            'De 06:00 PM a 07:00 PM',
            'De 07:00 PM a 08:00 PM',
            'De 08:00 PM a 09:00 PM',
            'De 09:00 PM a 10:00 PM'
        ],
        'booking_window_days': 7,
        'max_concurrent_requests': 10,
        'default_timeout_seconds': 30,
        'screenshot_enabled': True,
        'retry_attempts': 3,
        'retry_delay_seconds': 5
    }
    
    for key, value in configs.items():
        if not system_config.set_config(key, value, f"Default {key.replace('_', ' ')} configuration"):
            logger.error(f"Failed to set system config: {key}")
            return False
    
    logger.info("Database setup completed successfully")
    return True

def populate_test_data():
    """Populate test data for development"""
    logger.info("Populating test data...")
    
    # Create test user config
    user_config_ops = UserConfigOperations()
    
    test_user_config = {
        'username': 'test_user',
        'password': 'test_password',  # Will be encrypted in Step 1.3
        'website_url': 'https://example.com',
        'venue': 'Test Tennis Club',
        'preferred_court': 1,
        'default_date': '2025-04-01',
        'default_time': 'De 08:00 AM a 09:00 AM',
        'headless': True
    }
    
    if not user_config_ops.create_user_config('test-user-001', test_user_config):
        logger.error("Failed to create test user config")
        return False
    
    # Create test booking request
    booking_ops = BookingRequestOperations()
    
    test_booking_request = {
        'court_id': 1,
        'date': '2025-04-01',
        'time_slot': 'De 08:00 AM a 09:00 AM',
        'venue': 'Test Tennis Club'
    }
    
    request_id = booking_ops.create_booking_request('test-user-001', test_booking_request)
    if not request_id:
        logger.error("Failed to create test booking request")
        return False
    
    logger.info(f"Test data populated successfully. Test booking request ID: {request_id}")
    return True

def cleanup_database():
    """Clean up database (for testing)"""
    logger.info("Cleaning up database...")
    
    table_manager = TableManager()
    if table_manager.delete_all_tables():
        logger.info("Database cleanup completed")
        return True
    else:
        logger.error("Failed to cleanup database")
        return False

if __name__ == "__main__":
    # Check if we should use AWS instead of local
    use_aws = os.getenv('USE_AWS_DYNAMODB', 'false').lower() == 'true'
    
    if not use_aws:
        # Set up local DynamoDB endpoint if not set
        if not os.getenv('DYNAMODB_LOCAL_ENDPOINT'):
            os.environ['DYNAMODB_LOCAL_ENDPOINT'] = 'http://localhost:8000'
            logger.info("Using default local DynamoDB endpoint: http://localhost:8000")
    else:
        logger.info("Using AWS DynamoDB")
    
    # Setup database
    if setup_database():
        populate_test_data()
    else:
        logger.error("Database setup failed")