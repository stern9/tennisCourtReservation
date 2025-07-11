# ABOUTME: SystemConfig Pydantic model with validation for application configuration
# ABOUTME: Handles system-wide settings with type-safe configuration values

from typing import Optional, Dict, Any, List, Union
from enum import Enum
from pydantic import Field, validator
from .base import DynamoDBModel, ValidationMixin
from .validators import validate_court_list, validate_time_slot


class ConfigCategory(str, Enum):
    """System configuration categories"""
    COURTS = "courts"
    SCHEDULING = "scheduling"
    NOTIFICATIONS = "notifications"
    SECURITY = "security"
    BOOKING = "booking"
    SYSTEM = "system"


class ConfigValueType(str, Enum):
    """Configuration value types"""
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    LIST = "list"
    DICT = "dict"


class SystemConfig(DynamoDBModel, ValidationMixin):
    """System configuration model with validation"""
    
    class Config(DynamoDBModel.Config):
        schema_extra = {
            "example": {
                "config_key": "available_courts",
                "config_value": [5, 7, 17, 19, 23],
                "value_type": "list",
                "category": "courts",
                "description": "List of available court IDs",
                "is_active": True,
                "is_required": True
            }
        }
    
    # Primary key
    config_key: str = Field(..., description="Unique configuration key", min_length=1, max_length=100)
    
    # Configuration value and metadata
    config_value: Union[str, int, float, bool, List[Any], Dict[str, Any]] = Field(
        ..., 
        description="Configuration value"
    )
    value_type: ConfigValueType = Field(..., description="Type of the configuration value")
    category: ConfigCategory = Field(..., description="Configuration category")
    
    # Documentation and metadata
    description: str = Field(..., description="Human-readable description of the configuration")
    default_value: Optional[Union[str, int, float, bool, List[Any], Dict[str, Any]]] = Field(
        None, 
        description="Default value for this configuration"
    )
    
    # Configuration management
    is_active: bool = Field(default=True, description="Whether configuration is active")
    is_required: bool = Field(default=False, description="Whether configuration is required")
    is_sensitive: bool = Field(default=False, description="Whether configuration contains sensitive data")
    
    # Validation constraints
    min_value: Optional[Union[int, float]] = Field(None, description="Minimum value for numeric types")
    max_value: Optional[Union[int, float]] = Field(None, description="Maximum value for numeric types")
    allowed_values: Optional[List[Any]] = Field(None, description="List of allowed values")
    validation_pattern: Optional[str] = Field(None, description="Regex pattern for string validation")
    
    # Environment and deployment
    environment: Optional[str] = Field(None, description="Environment this config applies to")
    version: str = Field(default="1.0", description="Configuration version")
    
    # Validators
    @validator('config_key')
    def validate_config_key(cls, v):
        if not isinstance(v, str):
            raise ValueError("Config key must be a string")
        
        if len(v.strip()) == 0:
            raise ValueError("Config key cannot be empty")
        
        import re
        pattern = r'^[a-zA-Z0-9_-]+$'
        if not re.match(pattern, v):
            raise ValueError("Config key can only contain letters, numbers, underscores, and hyphens")
        
        return v.strip()
    
    @validator('config_value')
    def validate_config_value(cls, v, values):
        if 'value_type' not in values:
            return v
        
        value_type = values['value_type']
        
        if value_type == ConfigValueType.STRING:
            if not isinstance(v, str):
                raise ValueError("Config value must be a string for STRING type")
        elif value_type == ConfigValueType.INTEGER:
            if not isinstance(v, int):
                raise ValueError("Config value must be an integer for INTEGER type")
        elif value_type == ConfigValueType.FLOAT:
            if not isinstance(v, (int, float)):
                raise ValueError("Config value must be a number for FLOAT type")
        elif value_type == ConfigValueType.BOOLEAN:
            if not isinstance(v, bool):
                raise ValueError("Config value must be a boolean for BOOLEAN type")
        elif value_type == ConfigValueType.LIST:
            if not isinstance(v, list):
                raise ValueError("Config value must be a list for LIST type")
        elif value_type == ConfigValueType.DICT:
            if not isinstance(v, dict):
                raise ValueError("Config value must be a dict for DICT type")
        
        return v
    
    @validator('description')
    def validate_description(cls, v):
        if not isinstance(v, str):
            raise ValueError("Description must be a string")
        
        if len(v.strip()) == 0:
            raise ValueError("Description cannot be empty")
        
        if len(v) > 500:
            raise ValueError("Description cannot be longer than 500 characters")
        
        return v.strip()
    
    @validator('min_value', 'max_value')
    def validate_numeric_constraints(cls, v, values):
        if v is None:
            return v
        
        if 'value_type' in values:
            value_type = values['value_type']
            if value_type not in [ConfigValueType.INTEGER, ConfigValueType.FLOAT]:
                raise ValueError("Numeric constraints only apply to INTEGER and FLOAT types")
        
        return v
    
    @validator('max_value')
    def validate_max_greater_than_min(cls, v, values):
        if v is None or 'min_value' not in values or values['min_value'] is None:
            return v
        
        if v <= values['min_value']:
            raise ValueError("Max value must be greater than min value")
        
        return v
    
    @validator('allowed_values')
    def validate_allowed_values(cls, v):
        if v is None:
            return v
        
        if not isinstance(v, list):
            raise ValueError("Allowed values must be a list")
        
        if len(v) == 0:
            raise ValueError("Allowed values list cannot be empty")
        
        return v
    
    @validator('validation_pattern')
    def validate_validation_pattern(cls, v):
        if v is None:
            return v
        
        if not isinstance(v, str):
            raise ValueError("Validation pattern must be a string")
        
        # Test if it's a valid regex
        import re
        try:
            re.compile(v)
        except re.error:
            raise ValueError("Validation pattern must be a valid regex")
        
        return v
    
    @validator('version')
    def validate_version(cls, v):
        if not isinstance(v, str):
            raise ValueError("Version must be a string")
        
        import re
        pattern = r'^\d+\.\d+(\.\d+)?$'
        if not re.match(pattern, v):
            raise ValueError("Version must be in format X.Y or X.Y.Z")
        
        return v
    
    def get_primary_key(self) -> Dict[str, Any]:
        """Get primary key for DynamoDB operations"""
        return {"config_key": self.config_key}
    
    def get_table_name(self) -> str:
        """Get DynamoDB table name"""
        return "SystemConfig"
    
    def validate_value_against_constraints(self, value: Any = None) -> bool:
        """Validate config value against defined constraints"""
        test_value = value if value is not None else self.config_value
        
        # Check allowed values
        if self.allowed_values and test_value not in self.allowed_values:
            return False
        
        # Check numeric constraints
        if self.value_type in [ConfigValueType.INTEGER, ConfigValueType.FLOAT]:
            if isinstance(test_value, (int, float)):
                if self.min_value is not None and test_value < self.min_value:
                    return False
                if self.max_value is not None and test_value > self.max_value:
                    return False
        
        # Check string pattern
        if self.value_type == ConfigValueType.STRING and self.validation_pattern:
            if isinstance(test_value, str):
                import re
                if not re.match(self.validation_pattern, test_value):
                    return False
        
        return True
    
    def get_typed_value(self) -> Any:
        """Get config value cast to the correct type"""
        if self.value_type == ConfigValueType.STRING:
            return str(self.config_value)
        elif self.value_type == ConfigValueType.INTEGER:
            return int(self.config_value)
        elif self.value_type == ConfigValueType.FLOAT:
            return float(self.config_value)
        elif self.value_type == ConfigValueType.BOOLEAN:
            return bool(self.config_value)
        else:
            return self.config_value
    
    def update_value(self, new_value: Any) -> None:
        """Update configuration value with validation"""
        if not self.validate_value_against_constraints(new_value):
            raise ValueError("New value does not meet configuration constraints")
        
        self.config_value = new_value
    
    def reset_to_default(self) -> None:
        """Reset configuration to default value"""
        if self.default_value is not None:
            self.config_value = self.default_value
        else:
            raise ValueError("No default value defined for this configuration")
    
    def is_numeric(self) -> bool:
        """Check if configuration value is numeric"""
        return self.value_type in [ConfigValueType.INTEGER, ConfigValueType.FLOAT]
    
    def is_collection(self) -> bool:
        """Check if configuration value is a collection"""
        return self.value_type in [ConfigValueType.LIST, ConfigValueType.DICT]
    
    def get_category_display(self) -> str:
        """Get formatted category display"""
        category_display = {
            ConfigCategory.COURTS: "Court Management",
            ConfigCategory.SCHEDULING: "Scheduling",
            ConfigCategory.NOTIFICATIONS: "Notifications",
            ConfigCategory.SECURITY: "Security",
            ConfigCategory.BOOKING: "Booking System",
            ConfigCategory.SYSTEM: "System Settings"
        }
        return category_display.get(self.category, str(self.category))
    
    def get_type_display(self) -> str:
        """Get formatted type display"""
        type_display = {
            ConfigValueType.STRING: "Text",
            ConfigValueType.INTEGER: "Number (Integer)",
            ConfigValueType.FLOAT: "Number (Decimal)",
            ConfigValueType.BOOLEAN: "Yes/No",
            ConfigValueType.LIST: "List",
            ConfigValueType.DICT: "Object"
        }
        return type_display.get(self.value_type, str(self.value_type))
    
    def to_dict_for_display(self) -> Dict[str, Any]:
        """Convert to dictionary for display purposes"""
        return {
            "config_key": self.config_key,
            "config_value": self.config_value,
            "type": self.get_type_display(),
            "category": self.get_category_display(),
            "description": self.description,
            "is_active": self.is_active,
            "is_required": self.is_required,
            "is_sensitive": self.is_sensitive,
            "default_value": self.default_value,
            "constraints": {
                "min_value": self.min_value,
                "max_value": self.max_value,
                "allowed_values": self.allowed_values,
                "validation_pattern": self.validation_pattern
            },
            "version": self.version,
            "environment": self.environment,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


# Predefined system configurations
DEFAULT_SYSTEM_CONFIGS = [
    {
        "config_key": "available_courts",
        "config_value": [5, 7, 17, 19, 23],
        "value_type": ConfigValueType.LIST,
        "category": ConfigCategory.COURTS,
        "description": "List of available court IDs for booking",
        "default_value": [5, 7, 17, 19, 23],
        "is_active": True,
        "is_required": True
    },
    {
        "config_key": "available_time_slots",
        "config_value": [
            "De 08:00 AM a 09:00 AM",
            "De 09:00 AM a 10:00 AM",
            "De 10:00 AM a 11:00 AM",
            "De 11:00 AM a 12:00 PM",
            "De 12:00 PM a 01:00 PM",
            "De 01:00 PM a 02:00 PM",
            "De 02:00 PM a 03:00 PM",
            "De 03:00 PM a 04:00 PM",
            "De 04:00 PM a 05:00 PM",
            "De 05:00 PM a 06:00 PM",
            "De 06:00 PM a 07:00 PM",
            "De 07:00 PM a 08:00 PM"
        ],
        "value_type": ConfigValueType.LIST,
        "category": ConfigCategory.SCHEDULING,
        "description": "Available time slots for booking",
        "is_active": True,
        "is_required": True
    },
    {
        "config_key": "max_advance_booking_days",
        "config_value": 7,
        "value_type": ConfigValueType.INTEGER,
        "category": ConfigCategory.BOOKING,
        "description": "Maximum number of days in advance bookings can be made",
        "default_value": 7,
        "min_value": 1,
        "max_value": 30,
        "is_active": True,
        "is_required": True
    },
    {
        "config_key": "booking_retry_attempts",
        "config_value": 3,
        "value_type": ConfigValueType.INTEGER,
        "category": ConfigCategory.BOOKING,
        "description": "Number of retry attempts for failed bookings",
        "default_value": 3,
        "min_value": 0,
        "max_value": 10,
        "is_active": True,
        "is_required": False
    },
    {
        "config_key": "enable_notifications",
        "config_value": True,
        "value_type": ConfigValueType.BOOLEAN,
        "category": ConfigCategory.NOTIFICATIONS,
        "description": "Enable email notifications for booking updates",
        "default_value": True,
        "is_active": True,
        "is_required": False
    }
]