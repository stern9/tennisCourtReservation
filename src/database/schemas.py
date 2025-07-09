# ABOUTME: DynamoDB table schema definitions and creation utilities
# ABOUTME: Defines table structures for UserConfigs, BookingRequests, and SystemConfig

import boto3
import logging
from botocore.exceptions import ClientError
from typing import Dict, Any, List
from .connection import get_client, get_resource

logger = logging.getLogger(__name__)

class TableSchemas:
    """Manages DynamoDB table schemas and creation"""
    
    @staticmethod
    def get_user_configs_schema() -> Dict[str, Any]:
        """Schema for UserConfigs table"""
        return {
            'TableName': 'UserConfigs',
            'KeySchema': [
                {
                    'AttributeName': 'userId',
                    'KeyType': 'HASH'
                }
            ],
            'AttributeDefinitions': [
                {
                    'AttributeName': 'userId',
                    'AttributeType': 'S'
                }
            ],
            'BillingMode': 'PAY_PER_REQUEST',
            'Tags': [
                {
                    'Key': 'Application',
                    'Value': 'TennisBooking'
                },
                {
                    'Key': 'Environment',
                    'Value': 'dev'
                }
            ]
        }
    
    @staticmethod
    def get_booking_requests_schema() -> Dict[str, Any]:
        """Schema for BookingRequests table"""
        return {
            'TableName': 'BookingRequests',
            'KeySchema': [
                {
                    'AttributeName': 'requestId',
                    'KeyType': 'HASH'
                },
                {
                    'AttributeName': 'userId',
                    'KeyType': 'RANGE'
                }
            ],
            'AttributeDefinitions': [
                {
                    'AttributeName': 'requestId',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'userId',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'status',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'createdAt',
                    'AttributeType': 'S'
                }
            ],
            'GlobalSecondaryIndexes': [
                {
                    'IndexName': 'UserIndex',
                    'KeySchema': [
                        {
                            'AttributeName': 'userId',
                            'KeyType': 'HASH'
                        },
                        {
                            'AttributeName': 'createdAt',
                            'KeyType': 'RANGE'
                        }
                    ],
                    'Projection': {
                        'ProjectionType': 'ALL'
                    }
                },
                {
                    'IndexName': 'StatusIndex',
                    'KeySchema': [
                        {
                            'AttributeName': 'status',
                            'KeyType': 'HASH'
                        },
                        {
                            'AttributeName': 'createdAt',
                            'KeyType': 'RANGE'
                        }
                    ],
                    'Projection': {
                        'ProjectionType': 'ALL'
                    }
                }
            ],
            'BillingMode': 'PAY_PER_REQUEST',
            'Tags': [
                {
                    'Key': 'Application',
                    'Value': 'TennisBooking'
                },
                {
                    'Key': 'Environment',
                    'Value': 'dev'
                }
            ]
        }
    
    @staticmethod
    def get_system_config_schema() -> Dict[str, Any]:
        """Schema for SystemConfig table"""
        return {
            'TableName': 'SystemConfig',
            'KeySchema': [
                {
                    'AttributeName': 'configKey',
                    'KeyType': 'HASH'
                }
            ],
            'AttributeDefinitions': [
                {
                    'AttributeName': 'configKey',
                    'AttributeType': 'S'
                }
            ],
            'BillingMode': 'PAY_PER_REQUEST',
            'Tags': [
                {
                    'Key': 'Application',
                    'Value': 'TennisBooking'
                },
                {
                    'Key': 'Environment',
                    'Value': 'dev'
                }
            ]
        }

class TableManager:
    """Manages DynamoDB table operations"""
    
    def __init__(self):
        self.client = get_client()
        self.resource = get_resource()
        self.schemas = TableSchemas()
    
    def create_tables(self) -> bool:
        """Create all required tables"""
        tables = [
            self.schemas.get_user_configs_schema(),
            self.schemas.get_booking_requests_schema(),
            self.schemas.get_system_config_schema()
        ]
        
        success = True
        for table_schema in tables:
            if not self._create_table(table_schema):
                success = False
        
        return success
    
    def _create_table(self, schema: Dict[str, Any]) -> bool:
        """Create a single table"""
        table_name = schema['TableName']
        
        try:
            # Check if table already exists
            if self._table_exists(table_name):
                logger.info(f"Table {table_name} already exists")
                return True
            
            # Create table
            logger.info(f"Creating table {table_name}")
            response = self.client.create_table(**schema)
            
            # Wait for table to be created
            waiter = self.client.get_waiter('table_exists')
            waiter.wait(TableName=table_name, WaiterConfig={'Delay': 1, 'MaxAttempts': 10})
            
            logger.info(f"Table {table_name} created successfully")
            return True
            
        except ClientError as e:
            logger.error(f"Failed to create table {table_name}: {e}")
            return False
    
    def _table_exists(self, table_name: str) -> bool:
        """Check if table exists"""
        try:
            self.client.describe_table(TableName=table_name)
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                return False
            raise
    
    def delete_all_tables(self) -> bool:
        """Delete all tables (for testing/cleanup)"""
        table_names = ['UserConfigs', 'BookingRequests', 'SystemConfig']
        success = True
        
        for table_name in table_names:
            if not self._delete_table(table_name):
                success = False
        
        return success
    
    def _delete_table(self, table_name: str) -> bool:
        """Delete a single table"""
        try:
            if not self._table_exists(table_name):
                logger.info(f"Table {table_name} does not exist")
                return True
            
            logger.info(f"Deleting table {table_name}")
            self.client.delete_table(TableName=table_name)
            
            # Wait for table to be deleted
            waiter = self.client.get_waiter('table_not_exists')
            waiter.wait(TableName=table_name, WaiterConfig={'Delay': 1, 'MaxAttempts': 10})
            
            logger.info(f"Table {table_name} deleted successfully")
            return True
            
        except ClientError as e:
            logger.error(f"Failed to delete table {table_name}: {e}")
            return False
    
    def list_tables(self) -> List[str]:
        """List all tables"""
        try:
            response = self.client.list_tables()
            return response['TableNames']
        except ClientError as e:
            logger.error(f"Failed to list tables: {e}")
            return []