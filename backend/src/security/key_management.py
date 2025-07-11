# ABOUTME: Environment-specific key management utilities for encryption services
# ABOUTME: Handles key rotation, environment isolation, and secure key storage

import os
import json
import logging
from typing import Dict, Any, Optional, List
from enum import Enum
from pydantic import BaseModel, Field
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class Environment(str, Enum):
    """Supported environments"""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class KeyType(str, Enum):
    """Types of encryption keys"""
    MASTER = "master"
    DATA = "data"
    BACKUP = "backup"


class KeyManagementError(Exception):
    """Custom exception for key management errors"""
    pass


class KeyMetadata(BaseModel):
    """Metadata for encryption keys"""
    
    key_id: str = Field(..., description="Unique key identifier")
    key_type: KeyType = Field(..., description="Type of key")
    environment: Environment = Field(..., description="Environment where key is used")
    created_at: str = Field(..., description="Key creation timestamp")
    last_rotated: Optional[str] = Field(None, description="Last rotation timestamp")
    is_active: bool = Field(default=True, description="Whether key is active")
    rotation_schedule: Optional[str] = Field(None, description="Rotation schedule (e.g., '30d')")
    description: Optional[str] = Field(None, description="Key description")
    
    class Config:
        use_enum_values = True


class KeyManager:
    """
    Environment-specific key management service
    """
    
    def __init__(self, environment: Environment = Environment.DEVELOPMENT):
        """
        Initialize key manager
        
        Args:
            environment: Target environment
        """
        self.environment = environment
        self.kms_client = None
        self.key_metadata_cache = {}
        self._initialize_key_manager()
    
    def _initialize_key_manager(self):
        """Initialize key manager based on environment"""
        try:
            if self.environment != Environment.DEVELOPMENT:
                self.kms_client = boto3.client('kms')
            
            # Load existing key metadata
            self._load_key_metadata()
            
            logger.info(f"Key manager initialized for environment: {self.environment}")
        except Exception as e:
            logger.error(f"Failed to initialize key manager: {e}")
            raise KeyManagementError(f"Key manager initialization failed: {e}")
    
    def _load_key_metadata(self):
        """Load key metadata from storage"""
        try:
            metadata_file = self._get_metadata_file_path()
            if os.path.exists(metadata_file):
                with open(metadata_file, 'r') as f:
                    data = json.load(f)
                    self.key_metadata_cache = {
                        key_id: KeyMetadata(**metadata)
                        for key_id, metadata in data.items()
                    }
        except Exception as e:
            logger.warning(f"Failed to load key metadata: {e}")
            self.key_metadata_cache = {}
    
    def _save_key_metadata(self):
        """Save key metadata to storage"""
        try:
            metadata_file = self._get_metadata_file_path()
            os.makedirs(os.path.dirname(metadata_file), exist_ok=True)
            
            data = {
                key_id: metadata.dict()
                for key_id, metadata in self.key_metadata_cache.items()
            }
            
            with open(metadata_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save key metadata: {e}")
            raise KeyManagementError(f"Key metadata save failed: {e}")
    
    def _get_metadata_file_path(self) -> str:
        """Get path to key metadata file"""
        base_dir = os.path.join(os.path.dirname(__file__), '..', '..', '.keys')
        return os.path.join(base_dir, f'{self.environment.value}_key_metadata.json')
    
    def create_master_key(self, description: str = None) -> KeyMetadata:
        """
        Create a new master key
        
        Args:
            description: Optional key description
            
        Returns:
            KeyMetadata for the new key
        """
        try:
            if self.environment == Environment.DEVELOPMENT:
                return self._create_development_key(KeyType.MASTER, description)
            else:
                return self._create_kms_key(KeyType.MASTER, description)
        except Exception as e:
            logger.error(f"Failed to create master key: {e}")
            raise KeyManagementError(f"Master key creation failed: {e}")
    
    def _create_development_key(self, key_type: KeyType, description: str = None) -> KeyMetadata:
        """Create a development key (simulated)"""
        import uuid
        
        key_id = f"dev-{key_type.value}-{uuid.uuid4().hex[:8]}"
        
        metadata = KeyMetadata(
            key_id=key_id,
            key_type=key_type,
            environment=self.environment,
            created_at=self._get_timestamp(),
            description=description or f"Development {key_type.value} key",
            rotation_schedule="90d"  # Development keys rotate every 90 days
        )
        
        self.key_metadata_cache[key_id] = metadata
        self._save_key_metadata()
        
        logger.info(f"Created development key: {key_id}")
        return metadata
    
    def _create_kms_key(self, key_type: KeyType, description: str = None) -> KeyMetadata:
        """Create a KMS key"""
        try:
            # Create KMS key
            key_spec = 'SYMMETRIC_DEFAULT'
            key_usage = 'ENCRYPT_DECRYPT'
            
            response = self.kms_client.create_key(
                Description=description or f"{self.environment.value} {key_type.value} key",
                KeyUsage=key_usage,
                KeySpec=key_spec,
                Tags=[
                    {'TagKey': 'Environment', 'TagValue': self.environment.value},
                    {'TagKey': 'KeyType', 'TagValue': key_type.value},
                    {'TagKey': 'Service', 'TagValue': 'tennis-booking'},
                ]
            )
            
            key_id = response['KeyMetadata']['KeyId']
            
            # Create alias for easier reference
            alias_name = f"alias/tennis-booking-{self.environment.value}-{key_type.value}"
            try:
                self.kms_client.create_alias(
                    AliasName=alias_name,
                    TargetKeyId=key_id
                )
            except ClientError as e:
                if e.response['Error']['Code'] != 'AlreadyExistsException':
                    raise
            
            metadata = KeyMetadata(
                key_id=key_id,
                key_type=key_type,
                environment=self.environment,
                created_at=self._get_timestamp(),
                description=description or f"{self.environment.value} {key_type.value} key",
                rotation_schedule="30d" if self.environment == Environment.PRODUCTION else "90d"
            )
            
            self.key_metadata_cache[key_id] = metadata
            self._save_key_metadata()
            
            logger.info(f"Created KMS key: {key_id} with alias: {alias_name}")
            return metadata
            
        except ClientError as e:
            logger.error(f"Failed to create KMS key: {e}")
            raise KeyManagementError(f"KMS key creation failed: {e}")
    
    def get_key_metadata(self, key_id: str) -> Optional[KeyMetadata]:
        """
        Get metadata for a specific key
        
        Args:
            key_id: Key identifier
            
        Returns:
            KeyMetadata or None if not found
        """
        return self.key_metadata_cache.get(key_id)
    
    def list_keys(self, key_type: KeyType = None, active_only: bool = True) -> List[KeyMetadata]:
        """
        List keys for current environment
        
        Args:
            key_type: Optional filter by key type
            active_only: Only return active keys
            
        Returns:
            List of KeyMetadata
        """
        keys = []
        
        for metadata in self.key_metadata_cache.values():
            if metadata.environment != self.environment:
                continue
            
            if key_type and metadata.key_type != key_type:
                continue
            
            if active_only and not metadata.is_active:
                continue
            
            keys.append(metadata)
        
        return sorted(keys, key=lambda x: x.created_at, reverse=True)
    
    def get_current_master_key(self) -> Optional[KeyMetadata]:
        """
        Get the current active master key
        
        Returns:
            KeyMetadata for current master key or None if not found
        """
        master_keys = self.list_keys(KeyType.MASTER, active_only=True)
        return master_keys[0] if master_keys else None
    
    def rotate_key(self, key_id: str, create_backup: bool = True) -> KeyMetadata:
        """
        Rotate a key
        
        Args:
            key_id: Key to rotate
            create_backup: Whether to create a backup of the old key
            
        Returns:
            KeyMetadata for the new key
        """
        try:
            old_metadata = self.get_key_metadata(key_id)
            if not old_metadata:
                raise KeyManagementError(f"Key not found: {key_id}")
            
            # Create backup if requested
            if create_backup:
                self._create_backup_key(old_metadata)
            
            # Deactivate old key
            old_metadata.is_active = False
            old_metadata.last_rotated = self._get_timestamp()
            
            # Create new key
            new_metadata = self.create_master_key(
                description=f"Rotated {old_metadata.description}"
            )
            
            self._save_key_metadata()
            
            logger.info(f"Key rotated: {key_id} -> {new_metadata.key_id}")
            return new_metadata
            
        except Exception as e:
            logger.error(f"Failed to rotate key {key_id}: {e}")
            raise KeyManagementError(f"Key rotation failed: {e}")
    
    def _create_backup_key(self, original_metadata: KeyMetadata) -> KeyMetadata:
        """Create a backup of an existing key"""
        backup_metadata = KeyMetadata(
            key_id=f"backup-{original_metadata.key_id}",
            key_type=KeyType.BACKUP,
            environment=self.environment,
            created_at=self._get_timestamp(),
            description=f"Backup of {original_metadata.key_id}",
            is_active=False
        )
        
        self.key_metadata_cache[backup_metadata.key_id] = backup_metadata
        return backup_metadata
    
    def schedule_key_rotation(self, key_id: str, schedule: str):
        """
        Schedule automatic key rotation
        
        Args:
            key_id: Key to schedule rotation for
            schedule: Rotation schedule (e.g., '30d', '90d')
        """
        metadata = self.get_key_metadata(key_id)
        if not metadata:
            raise KeyManagementError(f"Key not found: {key_id}")
        
        metadata.rotation_schedule = schedule
        self._save_key_metadata()
        
        logger.info(f"Scheduled rotation for key {key_id}: {schedule}")
    
    def check_rotation_due(self) -> List[KeyMetadata]:
        """
        Check which keys are due for rotation
        
        Returns:
            List of keys that need rotation
        """
        due_keys = []
        
        for metadata in self.key_metadata_cache.values():
            if not metadata.is_active or not metadata.rotation_schedule:
                continue
            
            if self._is_rotation_due(metadata):
                due_keys.append(metadata)
        
        return due_keys
    
    def _is_rotation_due(self, metadata: KeyMetadata) -> bool:
        """Check if a key is due for rotation"""
        if not metadata.rotation_schedule:
            return False
        
        from datetime import datetime, timedelta
        
        # Parse rotation schedule (e.g., '30d' for 30 days)
        schedule = metadata.rotation_schedule
        if schedule.endswith('d'):
            days = int(schedule[:-1])
            rotation_interval = timedelta(days=days)
        else:
            logger.warning(f"Unsupported rotation schedule format: {schedule}")
            return False
        
        # Check if rotation is due
        last_rotation = metadata.last_rotated or metadata.created_at
        last_rotation_dt = datetime.fromisoformat(last_rotation.replace('Z', '+00:00'))
        
        return datetime.utcnow() - last_rotation_dt.replace(tzinfo=None) > rotation_interval
    
    def get_environment_config(self) -> Dict[str, Any]:
        """
        Get environment-specific configuration
        
        Returns:
            Dictionary with environment configuration
        """
        config = {
            'environment': self.environment.value,
            'key_count': len(self.key_metadata_cache),
            'active_keys': len([k for k in self.key_metadata_cache.values() if k.is_active]),
            'master_key': None,
            'encryption_available': True,
            'kms_enabled': self.kms_client is not None
        }
        
        # Get current master key
        master_key = self.get_current_master_key()
        if master_key:
            config['master_key'] = {
                'key_id': master_key.key_id,
                'created_at': master_key.created_at,
                'rotation_schedule': master_key.rotation_schedule
            }
        
        return config
    
    def health_check(self) -> Dict[str, Any]:
        """
        Check key management health
        
        Returns:
            Dictionary containing health status
        """
        try:
            # Check if master key exists
            master_key = self.get_current_master_key()
            if not master_key:
                return {
                    'status': 'unhealthy',
                    'error': 'No active master key found',
                    'environment': self.environment.value,
                    'timestamp': self._get_timestamp()
                }
            
            # Check if keys are due for rotation
            due_keys = self.check_rotation_due()
            
            return {
                'status': 'healthy',
                'environment': self.environment.value,
                'master_key_id': master_key.key_id,
                'total_keys': len(self.key_metadata_cache),
                'active_keys': len([k for k in self.key_metadata_cache.values() if k.is_active]),
                'keys_due_for_rotation': len(due_keys),
                'timestamp': self._get_timestamp()
            }
        except Exception as e:
            logger.error(f"Key management health check failed: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e),
                'environment': self.environment.value,
                'timestamp': self._get_timestamp()
            }
    
    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime
        return datetime.utcnow().isoformat()


# Global key manager instances
_key_managers = {}


def get_key_manager(environment: Environment = Environment.DEVELOPMENT) -> KeyManager:
    """
    Get key manager instance for environment
    
    Args:
        environment: Target environment
        
    Returns:
        KeyManager instance
    """
    global _key_managers
    
    if environment not in _key_managers:
        _key_managers[environment] = KeyManager(environment)
    
    return _key_managers[environment]


def initialize_encryption_keys(environment: Environment = Environment.DEVELOPMENT) -> KeyMetadata:
    """
    Initialize encryption keys for environment
    
    Args:
        environment: Target environment
        
    Returns:
        KeyMetadata for the master key
    """
    key_manager = get_key_manager(environment)
    
    # Check if master key already exists
    master_key = key_manager.get_current_master_key()
    if master_key:
        logger.info(f"Master key already exists for {environment.value}: {master_key.key_id}")
        return master_key
    
    # Create new master key
    master_key = key_manager.create_master_key(
        description=f"Master encryption key for {environment.value} environment"
    )
    
    logger.info(f"Created master key for {environment.value}: {master_key.key_id}")
    return master_key


def get_current_encryption_key(environment: Environment = Environment.DEVELOPMENT) -> Optional[str]:
    """
    Get current encryption key ID for environment
    
    Args:
        environment: Target environment
        
    Returns:
        Key ID or None if not found
    """
    key_manager = get_key_manager(environment)
    master_key = key_manager.get_current_master_key()
    return master_key.key_id if master_key else None