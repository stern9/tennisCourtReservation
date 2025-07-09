# ABOUTME: Basic CRUD operations for DynamoDB tables
# ABOUTME: Provides data access methods for UserConfigs, BookingRequests, and SystemConfig

import boto3
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from botocore.exceptions import ClientError
from .connection import get_resource
import uuid

logger = logging.getLogger(__name__)

class DynamoDBOperations:
    """Basic CRUD operations for DynamoDB tables"""
    
    def __init__(self):
        self.dynamodb = get_resource()
    
    def _get_table(self, table_name: str):
        """Get table resource"""
        return self.dynamodb.Table(table_name)
    
    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format"""
        return datetime.now(timezone.utc).isoformat()

class UserConfigOperations(DynamoDBOperations):
    """CRUD operations for UserConfigs table"""
    
    def __init__(self):
        super().__init__()
        self.table = self._get_table('UserConfigs')
    
    def create_user_config(self, user_id: str, config_data: Dict[str, Any]) -> bool:
        """Create a new user configuration"""
        try:
            timestamp = self._get_timestamp()
            item = {
                'userId': user_id,
                'username': config_data.get('username'),
                'password': config_data.get('password'),  # Will be encrypted in Step 1.3
                'websiteUrl': config_data.get('website_url'),
                'venue': config_data.get('venue'),
                'preferredCourt': config_data.get('preferred_court'),
                'defaultDate': config_data.get('default_date'),
                'defaultTime': config_data.get('default_time'),
                'headless': config_data.get('headless', False),
                'createdAt': timestamp,
                'updatedAt': timestamp,
                'version': 1
            }
            
            # Remove None values
            item = {k: v for k, v in item.items() if v is not None}
            
            self.table.put_item(Item=item)
            logger.info(f"User config created for user {user_id}")
            return True
            
        except ClientError as e:
            logger.error(f"Failed to create user config for {user_id}: {e}")
            return False
    
    def get_user_config(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user configuration"""
        try:
            response = self.table.get_item(Key={'userId': user_id})
            if 'Item' in response:
                logger.info(f"User config retrieved for user {user_id}")
                return response['Item']
            else:
                logger.info(f"No config found for user {user_id}")
                return None
                
        except ClientError as e:
            logger.error(f"Failed to get user config for {user_id}: {e}")
            return None
    
    def update_user_config(self, user_id: str, config_data: Dict[str, Any]) -> bool:
        """Update user configuration"""
        try:
            timestamp = self._get_timestamp()
            
            # Build update expression
            update_expression = "SET updatedAt = :timestamp"
            expression_values = {':timestamp': timestamp}
            
            # Add fields to update
            for key, value in config_data.items():
                if value is not None:
                    if key == 'username':
                        update_expression += ", username = :username"
                        expression_values[':username'] = value
                    elif key == 'password':
                        update_expression += ", password = :password"
                        expression_values[':password'] = value
                    elif key == 'website_url':
                        update_expression += ", websiteUrl = :websiteUrl"
                        expression_values[':websiteUrl'] = value
                    elif key == 'venue':
                        update_expression += ", venue = :venue"
                        expression_values[':venue'] = value
                    elif key == 'preferred_court':
                        update_expression += ", preferredCourt = :preferredCourt"
                        expression_values[':preferredCourt'] = value
                    elif key == 'default_date':
                        update_expression += ", defaultDate = :defaultDate"
                        expression_values[':defaultDate'] = value
                    elif key == 'default_time':
                        update_expression += ", defaultTime = :defaultTime"
                        expression_values[':defaultTime'] = value
                    elif key == 'headless':
                        update_expression += ", headless = :headless"
                        expression_values[':headless'] = value
            
            # Add version increment
            update_expression += " ADD version :inc"
            expression_values[':inc'] = 1
            
            self.table.update_item(
                Key={'userId': user_id},
                UpdateExpression=update_expression,
                ExpressionAttributeValues=expression_values
            )
            
            logger.info(f"User config updated for user {user_id}")
            return True
            
        except ClientError as e:
            logger.error(f"Failed to update user config for {user_id}: {e}")
            return False
    
    def delete_user_config(self, user_id: str) -> bool:
        """Delete user configuration"""
        try:
            self.table.delete_item(Key={'userId': user_id})
            logger.info(f"User config deleted for user {user_id}")
            return True
            
        except ClientError as e:
            logger.error(f"Failed to delete user config for {user_id}: {e}")
            return False

class BookingRequestOperations(DynamoDBOperations):
    """CRUD operations for BookingRequests table"""
    
    def __init__(self):
        super().__init__()
        self.table = self._get_table('BookingRequests')
    
    def create_booking_request(self, user_id: str, request_data: Dict[str, Any]) -> Optional[str]:
        """Create a new booking request"""
        try:
            request_id = str(uuid.uuid4())
            timestamp = self._get_timestamp()
            
            # Calculate TTL (30 days from now)
            ttl = int((datetime.now(timezone.utc).timestamp() + 30 * 24 * 60 * 60))
            
            item = {
                'requestId': request_id,
                'userId': user_id,
                'courtId': request_data.get('court_id'),
                'date': request_data.get('date'),
                'timeSlot': request_data.get('time_slot'),
                'venue': request_data.get('venue'),
                'status': 'pending',
                'createdAt': timestamp,
                'updatedAt': timestamp,
                'ttl': ttl
            }
            
            # Remove None values
            item = {k: v for k, v in item.items() if v is not None}
            
            self.table.put_item(Item=item)
            logger.info(f"Booking request created with ID {request_id}")
            return request_id
            
        except ClientError as e:
            logger.error(f"Failed to create booking request: {e}")
            return None
    
    def get_booking_request(self, request_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Get booking request"""
        try:
            response = self.table.get_item(Key={'requestId': request_id, 'userId': user_id})
            if 'Item' in response:
                logger.info(f"Booking request retrieved: {request_id}")
                return response['Item']
            else:
                logger.info(f"No booking request found: {request_id}")
                return None
                
        except ClientError as e:
            logger.error(f"Failed to get booking request {request_id}: {e}")
            return None
    
    def update_booking_status(self, request_id: str, user_id: str, status: str, 
                            result_data: Optional[Dict[str, Any]] = None) -> bool:
        """Update booking request status"""
        try:
            timestamp = self._get_timestamp()
            
            update_expression = "SET #status = :status, updatedAt = :timestamp"
            expression_values = {
                ':status': status,
                ':timestamp': timestamp
            }
            expression_names = {'#status': 'status'}
            
            if result_data:
                update_expression += ", resultData = :resultData"
                expression_values[':resultData'] = result_data
            
            self.table.update_item(
                Key={'requestId': request_id, 'userId': user_id},
                UpdateExpression=update_expression,
                ExpressionAttributeValues=expression_values,
                ExpressionAttributeNames=expression_names
            )
            
            logger.info(f"Booking request {request_id} status updated to {status}")
            return True
            
        except ClientError as e:
            logger.error(f"Failed to update booking request {request_id}: {e}")
            return False
    
    def get_user_booking_requests(self, user_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Get booking requests for a user"""
        try:
            response = self.table.query(
                IndexName='UserIndex',
                KeyConditionExpression='userId = :userId',
                ExpressionAttributeValues={':userId': user_id},
                ScanIndexForward=False,  # Most recent first
                Limit=limit
            )
            
            logger.info(f"Retrieved {len(response['Items'])} booking requests for user {user_id}")
            return response['Items']
            
        except ClientError as e:
            logger.error(f"Failed to get booking requests for user {user_id}: {e}")
            return []
    
    def get_requests_by_status(self, status: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get booking requests by status"""
        try:
            response = self.table.query(
                IndexName='StatusIndex',
                KeyConditionExpression='#status = :status',
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues={':status': status},
                ScanIndexForward=False,  # Most recent first
                Limit=limit
            )
            
            logger.info(f"Retrieved {len(response['Items'])} booking requests with status {status}")
            return response['Items']
            
        except ClientError as e:
            logger.error(f"Failed to get booking requests with status {status}: {e}")
            return []

class SystemConfigOperations(DynamoDBOperations):
    """CRUD operations for SystemConfig table"""
    
    def __init__(self):
        super().__init__()
        self.table = self._get_table('SystemConfig')
    
    def set_config(self, config_key: str, config_value: Any, description: str = "") -> bool:
        """Set system configuration"""
        try:
            timestamp = self._get_timestamp()
            
            item = {
                'configKey': config_key,
                'configValue': config_value,
                'description': description,
                'lastModified': timestamp
            }
            
            self.table.put_item(Item=item)
            logger.info(f"System config set: {config_key}")
            return True
            
        except ClientError as e:
            logger.error(f"Failed to set system config {config_key}: {e}")
            return False
    
    def get_config(self, config_key: str) -> Optional[Any]:
        """Get system configuration"""
        try:
            response = self.table.get_item(Key={'configKey': config_key})
            if 'Item' in response:
                logger.info(f"System config retrieved: {config_key}")
                return response['Item']['configValue']
            else:
                logger.info(f"No system config found: {config_key}")
                return None
                
        except ClientError as e:
            logger.error(f"Failed to get system config {config_key}: {e}")
            return None
    
    def get_all_configs(self) -> Dict[str, Any]:
        """Get all system configurations"""
        try:
            response = self.table.scan()
            configs = {}
            
            for item in response['Items']:
                configs[item['configKey']] = item['configValue']
            
            logger.info(f"Retrieved {len(configs)} system configs")
            return configs
            
        except ClientError as e:
            logger.error(f"Failed to get all system configs: {e}")
            return {}
    
    def delete_config(self, config_key: str) -> bool:
        """Delete system configuration"""
        try:
            self.table.delete_item(Key={'configKey': config_key})
            logger.info(f"System config deleted: {config_key}")
            return True
            
        except ClientError as e:
            logger.error(f"Failed to delete system config {config_key}: {e}")
            return False