# ABOUTME: Base DAO class with common database operations and error handling
# ABOUTME: Provides CRUD operations, validation, and error handling for all DAOs

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any, Type, TypeVar, Generic
import logging
from pydantic import ValidationError as PydanticValidationError
from botocore.exceptions import ClientError

from ..models.base import DynamoDBModel
from ..database.connection import get_client, get_resource

T = TypeVar('T', bound=DynamoDBModel)

logger = logging.getLogger(__name__)


class DAOError(Exception):
    """Base exception for DAO operations"""
    pass


class ValidationError(DAOError):
    """Validation error in DAO operations"""
    pass


class NotFoundError(DAOError):
    """Entity not found error"""
    pass


class ConflictError(DAOError):
    """Entity conflict error (duplicate key, etc.)"""
    pass


class DatabaseError(DAOError):
    """Database operation error"""
    pass


class BaseDAO(Generic[T], ABC):
    """Base Data Access Object with common operations"""
    
    def __init__(self, model_class: Type[T]):
        self.model_class = model_class
        self.client = get_client()
        self.resource = get_resource()
        self.table_name = self._get_table_name()
        self.table = self.resource.Table(self.table_name)
    
    @abstractmethod
    def _get_table_name(self) -> str:
        """Get table name for this DAO"""
        pass
    
    def _handle_client_error(self, error: ClientError, operation: str) -> None:
        """Handle and convert ClientError to appropriate DAO exception"""
        error_code = error.response.get('Error', {}).get('Code', 'Unknown')
        error_message = error.response.get('Error', {}).get('Message', str(error))
        
        logger.error(f"DynamoDB {operation} error [{error_code}]: {error_message}")
        
        if error_code == 'ResourceNotFoundException':
            raise NotFoundError(f"Table {self.table_name} not found")
        elif error_code == 'ConditionalCheckFailedException':
            raise ConflictError("Conditional check failed - item may already exist or was modified")
        elif error_code == 'ValidationException':
            raise ValidationError(f"DynamoDB validation error: {error_message}")
        else:
            raise DatabaseError(f"Database operation failed: {error_message}")
    
    def _validate_model(self, model: T) -> T:
        """Validate model before database operations"""
        try:
            # Pydantic validation happens automatically during model creation
            # but we can add additional validation here
            if hasattr(model, 'validate_all_fields'):
                if not model.validate_all_fields():
                    errors = model.get_validation_errors()
                    raise ValidationError(f"Model validation failed: {errors}")
            return model
        except PydanticValidationError as e:
            raise ValidationError(f"Pydantic validation failed: {e}")
    
    def create(self, model: T, condition_expression: Optional[str] = None) -> T:
        """Create a new item in the database"""
        try:
            validated_model = self._validate_model(model)
            item = validated_model.to_dynamodb_item()
            
            # Add condition to prevent overwrites by default
            if condition_expression is None:
                primary_key = validated_model.get_primary_key()
                key_attr = list(primary_key.keys())[0]
                condition_expression = f"attribute_not_exists({key_attr})"
            
            put_kwargs = {
                'Item': item
            }
            
            if condition_expression:
                put_kwargs['ConditionExpression'] = condition_expression
            
            self.table.put_item(**put_kwargs)
            
            logger.info(f"Created {self.model_class.__name__} with key: {validated_model.get_primary_key()}")
            return validated_model
            
        except ClientError as e:
            self._handle_client_error(e, 'create')
        except Exception as e:
            logger.error(f"Unexpected error creating {self.model_class.__name__}: {e}")
            raise DatabaseError(f"Failed to create item: {e}")
    
    def get(self, **key_attrs) -> Optional[T]:
        """Get an item by primary key"""
        try:
            response = self.table.get_item(Key=key_attrs)
            
            if 'Item' not in response:
                return None
            
            model = self.model_class.from_dynamodb_item(response['Item'])
            logger.debug(f"Retrieved {self.model_class.__name__} with key: {key_attrs}")
            return model
            
        except ClientError as e:
            self._handle_client_error(e, 'get')
        except Exception as e:
            logger.error(f"Unexpected error getting {self.model_class.__name__}: {e}")
            raise DatabaseError(f"Failed to get item: {e}")
    
    def update(self, model: T, condition_expression: Optional[str] = None) -> T:
        """Update an existing item"""
        try:
            validated_model = self._validate_model(model)
            item = validated_model.to_dynamodb_item()
            primary_key = validated_model.get_primary_key()
            
            # Build update expression
            update_expressions = []
            expression_attribute_values = {}
            expression_attribute_names = {}
            
            for key, value in item.items():
                if key not in primary_key:
                    attr_name = f"#{key}"
                    attr_value = f":{key}"
                    update_expressions.append(f"{attr_name} = {attr_value}")
                    expression_attribute_names[attr_name] = key
                    expression_attribute_values[attr_value] = value
            
            update_expression = "SET " + ", ".join(update_expressions)
            
            update_kwargs = {
                'Key': primary_key,
                'UpdateExpression': update_expression,
                'ExpressionAttributeNames': expression_attribute_names,
                'ExpressionAttributeValues': expression_attribute_values,
                'ReturnValues': 'ALL_NEW'
            }
            
            if condition_expression:
                update_kwargs['ConditionExpression'] = condition_expression
            
            response = self.table.update_item(**update_kwargs)
            
            updated_model = self.model_class.from_dynamodb_item(response['Attributes'])
            logger.info(f"Updated {self.model_class.__name__} with key: {primary_key}")
            return updated_model
            
        except ClientError as e:
            self._handle_client_error(e, 'update')
        except Exception as e:
            logger.error(f"Unexpected error updating {self.model_class.__name__}: {e}")
            raise DatabaseError(f"Failed to update item: {e}")
    
    def delete(self, **key_attrs) -> bool:
        """Delete an item by primary key"""
        try:
            response = self.table.delete_item(
                Key=key_attrs,
                ReturnValues='ALL_OLD'
            )
            
            deleted = 'Attributes' in response
            if deleted:
                logger.info(f"Deleted {self.model_class.__name__} with key: {key_attrs}")
            else:
                logger.warning(f"Attempted to delete non-existent {self.model_class.__name__} with key: {key_attrs}")
            
            return deleted
            
        except ClientError as e:
            self._handle_client_error(e, 'delete')
        except Exception as e:
            logger.error(f"Unexpected error deleting {self.model_class.__name__}: {e}")
            raise DatabaseError(f"Failed to delete item: {e}")
    
    def exists(self, **key_attrs) -> bool:
        """Check if an item exists"""
        try:
            response = self.table.get_item(
                Key=key_attrs,
                ProjectionExpression=list(key_attrs.keys())[0]  # Only get the first key attribute
            )
            return 'Item' in response
            
        except ClientError as e:
            self._handle_client_error(e, 'exists')
        except Exception as e:
            logger.error(f"Unexpected error checking existence of {self.model_class.__name__}: {e}")
            raise DatabaseError(f"Failed to check item existence: {e}")
    
    def list_all(self, limit: Optional[int] = None) -> List[T]:
        """List all items in the table"""
        try:
            scan_kwargs = {}
            if limit:
                scan_kwargs['Limit'] = limit
            
            response = self.table.scan(**scan_kwargs)
            items = []
            
            for item in response.get('Items', []):
                model = self.model_class.from_dynamodb_item(item)
                items.append(model)
            
            logger.debug(f"Listed {len(items)} {self.model_class.__name__} items")
            return items
            
        except ClientError as e:
            self._handle_client_error(e, 'list_all')
        except Exception as e:
            logger.error(f"Unexpected error listing {self.model_class.__name__}: {e}")
            raise DatabaseError(f"Failed to list items: {e}")
    
    def count(self) -> int:
        """Count total items in the table"""
        try:
            response = self.table.scan(Select='COUNT')
            return response.get('Count', 0)
            
        except ClientError as e:
            self._handle_client_error(e, 'count')
        except Exception as e:
            logger.error(f"Unexpected error counting {self.model_class.__name__}: {e}")
            raise DatabaseError(f"Failed to count items: {e}")
    
    def query_by_index(
        self, 
        index_name: str, 
        key_condition_expression: str,
        expression_attribute_values: Dict[str, Any],
        expression_attribute_names: Optional[Dict[str, str]] = None,
        filter_expression: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[T]:
        """Query items using a Global Secondary Index"""
        try:
            query_kwargs = {
                'IndexName': index_name,
                'KeyConditionExpression': key_condition_expression,
                'ExpressionAttributeValues': expression_attribute_values
            }
            
            if expression_attribute_names:
                query_kwargs['ExpressionAttributeNames'] = expression_attribute_names
            
            if filter_expression:
                query_kwargs['FilterExpression'] = filter_expression
            
            if limit:
                query_kwargs['Limit'] = limit
            
            response = self.table.query(**query_kwargs)
            items = []
            
            for item in response.get('Items', []):
                model = self.model_class.from_dynamodb_item(item)
                items.append(model)
            
            logger.debug(f"Queried {len(items)} {self.model_class.__name__} items from index {index_name}")
            return items
            
        except ClientError as e:
            self._handle_client_error(e, 'query_by_index')
        except Exception as e:
            logger.error(f"Unexpected error querying {self.model_class.__name__} by index: {e}")
            raise DatabaseError(f"Failed to query items by index: {e}")
    
    def batch_create(self, models: List[T]) -> List[T]:
        """Create multiple items in batch"""
        if not models:
            return []
        
        try:
            with self.table.batch_writer() as batch:
                validated_models = []
                for model in models:
                    validated_model = self._validate_model(model)
                    batch.put_item(Item=validated_model.to_dynamodb_item())
                    validated_models.append(validated_model)
            
            logger.info(f"Batch created {len(validated_models)} {self.model_class.__name__} items")
            return validated_models
            
        except ClientError as e:
            self._handle_client_error(e, 'batch_create')
        except Exception as e:
            logger.error(f"Unexpected error batch creating {self.model_class.__name__}: {e}")
            raise DatabaseError(f"Failed to batch create items: {e}")
    
    def batch_delete(self, key_attrs_list: List[Dict[str, Any]]) -> int:
        """Delete multiple items in batch"""
        if not key_attrs_list:
            return 0
        
        try:
            with self.table.batch_writer() as batch:
                for key_attrs in key_attrs_list:
                    batch.delete_item(Key=key_attrs)
            
            logger.info(f"Batch deleted {len(key_attrs_list)} {self.model_class.__name__} items")
            return len(key_attrs_list)
            
        except ClientError as e:
            self._handle_client_error(e, 'batch_delete')
        except Exception as e:
            logger.error(f"Unexpected error batch deleting {self.model_class.__name__}: {e}")
            raise DatabaseError(f"Failed to batch delete items: {e}")