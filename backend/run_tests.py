# ABOUTME: Test runner script for DynamoDB operations and validation
# ABOUTME: Ensures DynamoDB Local is running and executes comprehensive test suite

import os
import sys
import subprocess
import time
import requests
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_dynamodb_local():
    """Check if DynamoDB Local is running"""
    try:
        response = requests.get('http://localhost:8000')
        return response.status_code == 400  # DynamoDB Local returns 400 for root endpoint
    except requests.exceptions.ConnectionError:
        return False

def start_dynamodb_local():
    """Start DynamoDB Local using Docker Compose"""
    logger.info("Starting DynamoDB Local...")
    
    try:
        # Start Docker Compose
        subprocess.run(['docker-compose', 'up', '-d', 'dynamodb-local'], check=True)
        
        # Wait for DynamoDB to be ready
        for i in range(30):
            if check_dynamodb_local():
                logger.info("DynamoDB Local is ready")
                return True
            time.sleep(1)
        
        logger.error("DynamoDB Local failed to start within 30 seconds")
        return False
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to start DynamoDB Local: {e}")
        return False

def run_tests():
    """Run the test suite"""
    logger.info("Running tests...")
    
    # Set environment variables
    os.environ['DYNAMODB_LOCAL_ENDPOINT'] = 'http://localhost:8000'
    os.environ['AWS_ACCESS_KEY_ID'] = 'fake'
    os.environ['AWS_SECRET_ACCESS_KEY'] = 'fake'
    os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'
    
    try:
        # Run pytest from backend directory
        result = subprocess.run([
            sys.executable, '-m', 'pytest', 
            'backend/tests/', 
            '-v', 
            '--tb=short'
        ], check=True, cwd=os.path.dirname(os.path.dirname(__file__)))
        
        logger.info("All tests passed!")
        return True
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Tests failed with exit code {e.returncode}")
        return False

def main():
    """Main test runner function"""
    # Check if DynamoDB Local is already running
    if not check_dynamodb_local():
        if not start_dynamodb_local():
            logger.error("Failed to start DynamoDB Local")
            return False
    else:
        logger.info("DynamoDB Local is already running")
    
    # Run tests
    success = run_tests()
    
    if success:
        logger.info("✅ All tests completed successfully")
        return True
    else:
        logger.error("❌ Some tests failed")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)