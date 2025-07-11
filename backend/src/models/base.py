# ABOUTME: Base model classes and common configuration for Pydantic models
# ABOUTME: Provides shared configuration and utility methods for all models

from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, validator
from decimal import Decimal


class BaseModelConfig:
    """Base configuration for all Pydantic models"""
    
    # Allow validation of assignment after model creation
    validate_assignment = True
    
    # Use enum values instead of enum instances
    use_enum_values = True
    
    # Allow population by field name or alias
    allow_population_by_field_name = True
    
    # JSON encoders for custom types
    json_encoders = {
        datetime: lambda v: v.isoformat(),
        Decimal: lambda v: float(v)
    }
    
    # Extra fields behavior
    extra = 'forbid'  # Forbid extra fields not defined in model


class TimestampedModel(BaseModel):
    """Base model with timestamp fields"""
    
    class Config(BaseModelConfig):
        pass
    
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    
    @validator('updated_at', pre=True, always=True)
    def set_updated_at(cls, v, values):
        """Set updated_at to current time when model is updated"""
        if 'created_at' in values and v is None:
            return values['created_at']
        return v or datetime.utcnow()


class DynamoDBModel(TimestampedModel):
    """Base model for DynamoDB entities"""
    
    class Config(BaseModelConfig):
        pass
    
    def to_dynamodb_item(self) -> Dict[str, Any]:
        """Convert model to DynamoDB item format"""
        item = {}
        for field_name, field_value in self.dict().items():
            if field_value is not None:
                item[field_name] = self._convert_value_for_dynamodb(field_value)
        return item
    
    def _convert_value_for_dynamodb(self, value: Any) -> Any:
        """Convert Python value to DynamoDB-compatible format"""
        if isinstance(value, datetime):
            return value.isoformat()
        elif isinstance(value, Decimal):
            return float(value)
        elif isinstance(value, bool):
            return value
        elif isinstance(value, (int, float, str)):
            return value
        elif isinstance(value, list):
            return [self._convert_value_for_dynamodb(item) for item in value]
        elif isinstance(value, dict):
            return {k: self._convert_value_for_dynamodb(v) for k, v in value.items()}
        else:
            return str(value)
    
    @classmethod
    def from_dynamodb_item(cls, item: Dict[str, Any]) -> 'DynamoDBModel':
        """Create model instance from DynamoDB item"""
        converted_item = {}
        for field_name, field_value in item.items():
            converted_item[field_name] = cls._convert_value_from_dynamodb(field_value)
        return cls(**converted_item)
    
    @classmethod
    def _convert_value_from_dynamodb(cls, value: Any) -> Any:
        """Convert DynamoDB value to Python format"""
        if isinstance(value, str):
            # Try to parse as datetime
            try:
                return datetime.fromisoformat(value.replace('Z', '+00:00'))
            except ValueError:
                return value
        elif isinstance(value, list):
            return [cls._convert_value_from_dynamodb(item) for item in value]
        elif isinstance(value, dict):
            return {k: cls._convert_value_from_dynamodb(v) for k, v in value.items()}
        else:
            return value
    
    def get_primary_key(self) -> Dict[str, Any]:
        """Get primary key for DynamoDB operations"""
        raise NotImplementedError("Subclasses must implement get_primary_key")
    
    def get_table_name(self) -> str:
        """Get DynamoDB table name"""
        raise NotImplementedError("Subclasses must implement get_table_name")


class ValidationMixin:
    """Mixin for additional validation methods"""
    
    def validate_all_fields(self) -> bool:
        """Validate all fields and return True if valid"""
        try:
            self.validate(self.dict())
            return True
        except ValueError:
            return False
    
    def get_validation_errors(self) -> Dict[str, str]:
        """Get validation errors as dictionary"""
        try:
            self.validate(self.dict())
            return {}
        except ValueError as e:
            errors = {}
            for error in e.errors():
                field = '.'.join(str(x) for x in error['loc'])
                errors[field] = error['msg']
            return errors
    
    def is_valid(self) -> bool:
        """Check if model is valid"""
        return len(self.get_validation_errors()) == 0