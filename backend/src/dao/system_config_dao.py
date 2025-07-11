# ABOUTME: SystemConfig Data Access Object with configuration management operations
# ABOUTME: Provides validated CRUD operations and config queries for SystemConfig

from typing import Optional, List, Dict, Any, Union
import logging

from .base import BaseDAO, NotFoundError
from ..models.system_config import SystemConfig, ConfigCategory, DEFAULT_SYSTEM_CONFIGS

logger = logging.getLogger(__name__)


class SystemConfigDAO(BaseDAO[SystemConfig]):
    """Data Access Object for SystemConfig operations"""
    
    def __init__(self):
        super().__init__(SystemConfig)
    
    def _get_table_name(self) -> str:
        """Get table name for SystemConfig"""
        return "SystemConfig"
    
    def create_config(self, config: SystemConfig) -> SystemConfig:
        """Create a new system configuration"""
        return self.create(config)
    
    def get_config(self, config_key: str) -> Optional[SystemConfig]:
        """Get configuration by key"""
        return self.get(config_key=config_key)
    
    def get_config_value(self, config_key: str) -> Any:
        """Get configuration value by key"""
        config = self.get_config(config_key)
        if not config:
            raise NotFoundError(f"Configuration {config_key} not found")
        
        if not config.is_active:
            logger.warning(f"Accessing inactive configuration: {config_key}")
        
        return config.get_typed_value()
    
    def set_config(
        self, 
        config_key: str, 
        config_value: Any, 
        description: str = None,
        category: ConfigCategory = ConfigCategory.SYSTEM,
        **kwargs
    ) -> SystemConfig:
        """Set configuration value (create or update)"""
        existing_config = self.get_config(config_key)
        
        if existing_config:
            # Update existing configuration
            existing_config.update_value(config_value)
            if description:
                existing_config.description = description
            return self.update(existing_config)
        else:
            # Create new configuration
            from ..models.system_config import ConfigValueType
            
            # Determine value type
            if isinstance(config_value, str):
                value_type = ConfigValueType.STRING
            elif isinstance(config_value, int):
                value_type = ConfigValueType.INTEGER
            elif isinstance(config_value, float):
                value_type = ConfigValueType.FLOAT
            elif isinstance(config_value, bool):
                value_type = ConfigValueType.BOOLEAN
            elif isinstance(config_value, list):
                value_type = ConfigValueType.LIST
            elif isinstance(config_value, dict):
                value_type = ConfigValueType.DICT
            else:
                value_type = ConfigValueType.STRING
                config_value = str(config_value)
            
            new_config = SystemConfig(
                config_key=config_key,
                config_value=config_value,
                value_type=value_type,
                category=category,
                description=description or f"Configuration for {config_key}",
                **kwargs
            )
            
            return self.create_config(new_config)
    
    def update_config(self, config: SystemConfig) -> SystemConfig:
        """Update system configuration"""
        existing_config = self.get_config(config.config_key)
        if not existing_config:
            raise NotFoundError(f"Configuration {config.config_key} not found")
        
        return self.update(config)
    
    def delete_config(self, config_key: str) -> bool:
        """Delete system configuration"""
        config = self.get_config(config_key)
        if config and config.is_required:
            raise ValueError(f"Cannot delete required configuration: {config_key}")
        
        return self.delete(config_key=config_key)
    
    def get_configs_by_category(self, category: ConfigCategory) -> List[SystemConfig]:
        """Get all configurations in a category"""
        try:
            response = self.table.scan(
                FilterExpression='category = :category',
                ExpressionAttributeValues={':category': category.value}
            )
            
            configs = []
            for item in response.get('Items', []):
                config = self.model_class.from_dynamodb_item(item)
                configs.append(config)
            
            # Sort by config_key
            configs.sort(key=lambda x: x.config_key)
            
            logger.debug(f"Retrieved {len(configs)} configurations for category {category}")
            return configs
            
        except Exception as e:
            logger.error(f"Error getting configs by category: {e}")
            raise
    
    def get_active_configs(self) -> List[SystemConfig]:
        """Get all active configurations"""
        try:
            response = self.table.scan(
                FilterExpression='is_active = :is_active',
                ExpressionAttributeValues={':is_active': True}
            )
            
            configs = []
            for item in response.get('Items', []):
                config = self.model_class.from_dynamodb_item(item)
                configs.append(config)
            
            logger.debug(f"Retrieved {len(configs)} active configurations")
            return configs
            
        except Exception as e:
            logger.error(f"Error getting active configs: {e}")
            raise
    
    def get_required_configs(self) -> List[SystemConfig]:
        """Get all required configurations"""
        try:
            response = self.table.scan(
                FilterExpression='is_required = :is_required',
                ExpressionAttributeValues={':is_required': True}
            )
            
            configs = []
            for item in response.get('Items', []):
                config = self.model_class.from_dynamodb_item(item)
                configs.append(config)
            
            logger.debug(f"Retrieved {len(configs)} required configurations")
            return configs
            
        except Exception as e:
            logger.error(f"Error getting required configs: {e}")
            raise
    
    def get_sensitive_configs(self) -> List[SystemConfig]:
        """Get all sensitive configurations"""
        try:
            response = self.table.scan(
                FilterExpression='is_sensitive = :is_sensitive',
                ExpressionAttributeValues={':is_sensitive': True}
            )
            
            configs = []
            for item in response.get('Items', []):
                config = self.model_class.from_dynamodb_item(item)
                configs.append(config)
            
            logger.debug(f"Retrieved {len(configs)} sensitive configurations")
            return configs
            
        except Exception as e:
            logger.error(f"Error getting sensitive configs: {e}")
            raise
    
    def activate_config(self, config_key: str) -> SystemConfig:
        """Activate a configuration"""
        config = self.get_config(config_key)
        if not config:
            raise NotFoundError(f"Configuration {config_key} not found")
        
        config.is_active = True
        return self.update_config(config)
    
    def deactivate_config(self, config_key: str) -> SystemConfig:
        """Deactivate a configuration"""
        config = self.get_config(config_key)
        if not config:
            raise NotFoundError(f"Configuration {config_key} not found")
        
        if config.is_required:
            raise ValueError(f"Cannot deactivate required configuration: {config_key}")
        
        config.is_active = False
        return self.update_config(config)
    
    def reset_config_to_default(self, config_key: str) -> SystemConfig:
        """Reset configuration to default value"""
        config = self.get_config(config_key)
        if not config:
            raise NotFoundError(f"Configuration {config_key} not found")
        
        config.reset_to_default()
        return self.update_config(config)
    
    def get_config_with_fallback(self, config_key: str, fallback_value: Any = None) -> Any:
        """Get configuration value with fallback"""
        try:
            return self.get_config_value(config_key)
        except (NotFoundError, Exception) as e:
            logger.warning(f"Using fallback value for config {config_key}: {e}")
            return fallback_value
    
    def bulk_update_configs(self, config_updates: Dict[str, Any]) -> List[SystemConfig]:
        """Update multiple configurations in bulk"""
        updated_configs = []
        
        for config_key, config_value in config_updates.items():
            try:
                config = self.set_config(config_key, config_value)
                updated_configs.append(config)
            except Exception as e:
                logger.error(f"Error updating config {config_key}: {e}")
                raise
        
        logger.info(f"Bulk updated {len(updated_configs)} configurations")
        return updated_configs
    
    def validate_all_configs(self) -> Dict[str, bool]:
        """Validate all configurations against their constraints"""
        configs = self.list_all()
        validation_results = {}
        
        for config in configs:
            try:
                is_valid = config.validate_value_against_constraints()
                validation_results[config.config_key] = is_valid
                if not is_valid:
                    logger.warning(f"Configuration {config.config_key} fails validation")
            except Exception as e:
                logger.error(f"Error validating config {config.config_key}: {e}")
                validation_results[config.config_key] = False
        
        return validation_results
    
    def get_configs_by_environment(self, environment: str) -> List[SystemConfig]:
        """Get configurations for a specific environment"""
        try:
            response = self.table.scan(
                FilterExpression='environment = :environment OR attribute_not_exists(environment)',
                ExpressionAttributeValues={':environment': environment}
            )
            
            configs = []
            for item in response.get('Items', []):
                config = self.model_class.from_dynamodb_item(item)
                configs.append(config)
            
            logger.debug(f"Retrieved {len(configs)} configurations for environment {environment}")
            return configs
            
        except Exception as e:
            logger.error(f"Error getting configs by environment: {e}")
            raise
    
    def initialize_default_configs(self) -> List[SystemConfig]:
        """Initialize default system configurations"""
        created_configs = []
        
        for config_data in DEFAULT_SYSTEM_CONFIGS:
            config_key = config_data['config_key']
            
            # Check if config already exists
            if self.get_config(config_key):
                logger.info(f"Configuration {config_key} already exists, skipping")
                continue
            
            try:
                config = SystemConfig(**config_data)
                created_config = self.create_config(config)
                created_configs.append(created_config)
                logger.info(f"Created default configuration: {config_key}")
            except Exception as e:
                logger.error(f"Error creating default config {config_key}: {e}")
                raise
        
        logger.info(f"Initialized {len(created_configs)} default configurations")
        return created_configs
    
    def export_configs(self, category: Optional[ConfigCategory] = None) -> Dict[str, Any]:
        """Export configurations to dictionary"""
        if category:
            configs = self.get_configs_by_category(category)
        else:
            configs = self.list_all()
        
        exported = {}
        for config in configs:
            exported[config.config_key] = {
                'value': config.config_value,
                'type': config.value_type.value,
                'category': config.category.value,
                'description': config.description,
                'is_active': config.is_active,
                'is_required': config.is_required,
                'version': config.version
            }
        
        logger.info(f"Exported {len(exported)} configurations")
        return exported
    
    def import_configs(self, config_data: Dict[str, Any], overwrite: bool = False) -> List[SystemConfig]:
        """Import configurations from dictionary"""
        imported_configs = []
        
        for config_key, config_info in config_data.items():
            try:
                existing_config = self.get_config(config_key)
                
                if existing_config and not overwrite:
                    logger.info(f"Configuration {config_key} exists and overwrite=False, skipping")
                    continue
                
                config = SystemConfig(
                    config_key=config_key,
                    config_value=config_info['value'],
                    value_type=config_info['type'],
                    category=config_info['category'],
                    description=config_info['description'],
                    is_active=config_info.get('is_active', True),
                    is_required=config_info.get('is_required', False),
                    version=config_info.get('version', '1.0')
                )
                
                if existing_config:
                    imported_config = self.update_config(config)
                else:
                    imported_config = self.create_config(config)
                
                imported_configs.append(imported_config)
                logger.info(f"Imported configuration: {config_key}")
                
            except Exception as e:
                logger.error(f"Error importing config {config_key}: {e}")
                raise
        
        logger.info(f"Imported {len(imported_configs)} configurations")
        return imported_configs
    
    def get_config_stats(self) -> Dict[str, Any]:
        """Get configuration statistics"""
        try:
            total_count = self.count()
            
            # Count by category
            category_counts = {}
            for category in ConfigCategory:
                configs = self.get_configs_by_category(category)
                category_counts[category.value] = len(configs)
            
            # Count active/inactive
            active_configs = self.get_active_configs()
            active_count = len(active_configs)
            
            # Count required
            required_configs = self.get_required_configs()
            required_count = len(required_configs)
            
            # Count sensitive
            sensitive_configs = self.get_sensitive_configs()
            sensitive_count = len(sensitive_configs)
            
            stats = {
                'total_configs': total_count,
                'active_configs': active_count,
                'inactive_configs': total_count - active_count,
                'required_configs': required_count,
                'sensitive_configs': sensitive_count,
                'category_counts': category_counts
            }
            
            logger.debug(f"Config stats: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"Error getting config stats: {e}")
            raise