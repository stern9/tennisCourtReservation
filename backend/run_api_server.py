# ABOUTME: Development script to run FastAPI server with proper configuration
# ABOUTME: Sets up environment and starts uvicorn server for local development

import os
import sys
import subprocess
import logging
from pathlib import Path

def setup_environment():
    """Setup environment variables for development"""
    env_vars = {
        'TENNIS_ENVIRONMENT': 'development',
        'DYNAMODB_ENDPOINT': 'http://localhost:8000',
        'JWT_SECRET_KEY': 'development-secret-key-change-in-production',
        'TENNIS_WEBSITE_URL': 'https://example.com',  # Replace with actual tennis site URL
        'TENNIS_DEV_PASSWORD': 'dev-encryption-password-123'
    }
    
    for key, value in env_vars.items():
        if key not in os.environ:
            os.environ[key] = value
            print(f"Set {key} = {value}")

def check_dynamodb_local():
    """Check if DynamoDB Local is running"""
    try:
        import boto3
        from botocore.exceptions import ClientError, EndpointConnectionError
        
        # Test connection to local DynamoDB
        dynamodb = boto3.resource(
            'dynamodb',
            endpoint_url='http://localhost:8000',
            region_name='us-east-1',
            aws_access_key_id='dummy',
            aws_secret_access_key='dummy'
        )
        
        # Try to list tables
        list(dynamodb.tables.limit(1))
        print("✅ DynamoDB Local is running")
        return True
        
    except (ClientError, EndpointConnectionError) as e:
        print("❌ DynamoDB Local is not running")
        print("Please start DynamoDB Local with: docker-compose up -d")
        return False

def check_database_tables():
    """Check if database tables exist"""
    try:
        # Add src directory to path for importing our modules
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
        from database.connection import get_resource
        
        dynamodb = get_resource()
        table_names = [table.name for table in dynamodb.tables.all()]
        
        required_tables = ['UserConfigs', 'BookingRequests', 'SystemConfig']
        missing_tables = [table for table in required_tables if table not in table_names]
        
        if missing_tables:
            print(f"❌ Missing tables: {missing_tables}")
            print("Please run: python backend/src/setup_database.py")
            return False
        
        print("✅ All required tables exist")
        return True
        
    except Exception as e:
        print(f"❌ Error checking database tables: {e}")
        return False

def run_server():
    """Run the FastAPI server"""
    print("🚀 Starting Tennis Booking API server...")
    print("📍 Server will be available at: http://localhost:8001")
    print("📖 API documentation at: http://localhost:8001/docs")
    print("🔍 Health check at: http://localhost:8001/health")
    print("\n Press Ctrl+C to stop the server\n")
    
    try:
        # Add src directory to path for importing our modules
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
        
        # Run uvicorn server from backend directory
        subprocess.run([
            sys.executable, "-m", "uvicorn",
            "backend.src.api.main:app",
            "--host", "0.0.0.0",
            "--port", "8001",
            "--reload",
            "--log-level", "info"
        ], cwd=os.path.dirname(os.path.dirname(__file__)))
    except KeyboardInterrupt:
        print("\n👋 Server stopped")

def main():
    """Main function"""
    print("🎾 Tennis Booking API Development Server")
    print("=" * 50)
    
    # Setup environment
    setup_environment()
    
    # Check prerequisites
    if not check_dynamodb_local():
        return 1
    
    if not check_database_tables():
        return 1
    
    # Run server
    run_server()
    return 0

if __name__ == "__main__":
    sys.exit(main())