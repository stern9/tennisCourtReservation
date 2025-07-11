# ABOUTME: DynamoDB connection management and configuration
# ABOUTME: Handles local and AWS DynamoDB connections with proper resource management

import boto3
import os
import logging
from typing import Optional
from botocore.exceptions import ClientError, NoCredentialsError

logger = logging.getLogger(__name__)

class DynamoDBConnection:
    """Manages DynamoDB connections for local and AWS environments"""
    
    def __init__(self, local_endpoint: Optional[str] = None, region: str = 'us-east-1'):
        self.local_endpoint = local_endpoint or os.getenv('DYNAMODB_LOCAL_ENDPOINT')
        self.region = region
        self._dynamodb = None
        self._dynamodb_resource = None
        
    def get_client(self):
        """Get DynamoDB client with proper configuration"""
        if self._dynamodb is None:
            try:
                if self.local_endpoint:
                    logger.info(f"Connecting to local DynamoDB at {self.local_endpoint}")
                    self._dynamodb = boto3.client(
                        'dynamodb',
                        endpoint_url=self.local_endpoint,
                        region_name=self.region,
                        aws_access_key_id='fake',
                        aws_secret_access_key='fake'
                    )
                else:
                    logger.info("Connecting to AWS DynamoDB")
                    self._dynamodb = boto3.client('dynamodb', region_name=self.region)
                    
                # Test connection
                self._dynamodb.list_tables()
                logger.info("DynamoDB connection established successfully")
                
            except (ClientError, NoCredentialsError) as e:
                logger.error(f"Failed to connect to DynamoDB: {e}")
                raise
                
        return self._dynamodb
    
    def get_resource(self):
        """Get DynamoDB resource for higher-level operations"""
        if self._dynamodb_resource is None:
            try:
                if self.local_endpoint:
                    logger.info(f"Creating local DynamoDB resource at {self.local_endpoint}")
                    self._dynamodb_resource = boto3.resource(
                        'dynamodb',
                        endpoint_url=self.local_endpoint,
                        region_name=self.region,
                        aws_access_key_id='fake',
                        aws_secret_access_key='fake'
                    )
                else:
                    logger.info("Creating AWS DynamoDB resource")
                    self._dynamodb_resource = boto3.resource('dynamodb', region_name=self.region)
                    
            except (ClientError, NoCredentialsError) as e:
                logger.error(f"Failed to create DynamoDB resource: {e}")
                raise
                
        return self._dynamodb_resource

# Global connection instance
_connection = None

def get_connection() -> DynamoDBConnection:
    """Get or create a global DynamoDB connection"""
    global _connection
    if _connection is None:
        _connection = DynamoDBConnection()
    return _connection

def get_client():
    """Get DynamoDB client"""
    return get_connection().get_client()

def get_resource():
    """Get DynamoDB resource"""
    return get_connection().get_resource()