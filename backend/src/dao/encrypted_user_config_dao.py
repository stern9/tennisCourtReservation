# ABOUTME: Enhanced UserConfig DAO with encryption support for sensitive data operations
# ABOUTME: Provides secure CRUD operations with automatic encryption/decryption and credential validation

from typing import Optional, List, Dict, Any
import logging
import hashlib
from datetime import datetime

from .base import BaseDAO, NotFoundError
from ..models.encrypted_user_config import EncryptedUserConfig
from ..security import get_credential_storage, CredentialStorage

logger = logging.getLogger(__name__)


class EncryptedUserConfigDAO(BaseDAO[EncryptedUserConfig]):
    """Enhanced Data Access Object for EncryptedUserConfig operations"""
    
    def __init__(self):
        super().__init__(EncryptedUserConfig)
        self.credential_storage = get_credential_storage()
    
    def _get_table_name(self) -> str:
        """Get table name for UserConfig"""
        return "UserConfigs"
    
    def create_user(self, user_config: EncryptedUserConfig, validate_credentials: bool = True) -> EncryptedUserConfig:
        """
        Create a new user configuration with encrypted storage
        
        Args:
            user_config: User configuration to create
            validate_credentials: Whether to validate credential strength
            
        Returns:
            Created user configuration
        """
        if validate_credentials:
            self._validate_user_credentials(user_config)
        
        # Check for existing username/email
        self._check_username_email_uniqueness(user_config)
        
        # Convert to storage format (with encryption)
        storage_data = user_config.to_storage_dict()
        
        # Add audit information
        storage_data['created_at'] = datetime.utcnow().isoformat()
        storage_data['updated_at'] = storage_data['created_at']
        
        # Store in database
        self.table.put_item(Item=storage_data)
        
        logger.info(f"Created encrypted user: {user_config.user_id}")
        return user_config
    
    def get_user(self, user_id: str) -> Optional[EncryptedUserConfig]:
        """Get user configuration by user ID with automatic decryption"""
        try:
            response = self.table.get_item(Key={'user_id': user_id})
            
            if 'Item' not in response:
                return None
            
            # Create user from storage data (automatic decryption)
            return EncryptedUserConfig.from_storage_dict(response['Item'], user_id)
            
        except Exception as e:
            logger.error(f"Error getting user {user_id}: {e}")
            raise
    
    def get_user_by_username(self, username: str) -> Optional[EncryptedUserConfig]:
        """
        Get user configuration by username
        Note: This requires scanning since username is encrypted
        """
        try:
            # Since usernames are encrypted, we need to scan and decrypt to find matches
            # In production, consider using a hash-based index for better performance
            response = self.table.scan()
            
            for item in response.get('Items', []):
                try:
                    user = EncryptedUserConfig.from_storage_dict(item)
                    if user.username == username:
                        return user
                except Exception as e:
                    logger.warning(f"Failed to decrypt user record: {e}")
                    continue
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting user by username: {e}")
            raise
    
    def get_user_by_email(self, email: str) -> Optional[EncryptedUserConfig]:
        """
        Get user configuration by email
        Note: This requires scanning since email is encrypted
        """
        try:
            # Since emails are encrypted, we need to scan and decrypt to find matches
            response = self.table.scan()
            
            for item in response.get('Items', []):
                try:
                    user = EncryptedUserConfig.from_storage_dict(item)
                    if user.email == email:
                        return user
                except Exception as e:
                    logger.warning(f"Failed to decrypt user record: {e}")
                    continue
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting user by email: {e}")
            raise
    
    def update_user(self, user_config: EncryptedUserConfig, validate_credentials: bool = True) -> EncryptedUserConfig:
        """
        Update user configuration with encrypted storage
        
        Args:
            user_config: Updated user configuration
            validate_credentials: Whether to validate credential strength
            
        Returns:
            Updated user configuration
        """
        # Check if user exists
        existing_user = self.get_user(user_config.user_id)
        if not existing_user:
            raise NotFoundError(f"User {user_config.user_id} not found")
        
        if validate_credentials:
            self._validate_user_credentials(user_config)
        
        # Check for username/email conflicts (excluding current user)
        self._check_username_email_uniqueness(user_config, exclude_user_id=user_config.user_id)
        
        # Convert to storage format (with encryption)
        storage_data = user_config.to_storage_dict()
        storage_data['updated_at'] = datetime.utcnow().isoformat()
        
        # Preserve creation timestamp
        if existing_user.created_at:
            storage_data['created_at'] = existing_user.created_at
        
        # Update in database
        self.table.put_item(Item=storage_data)
        
        logger.info(f"Updated encrypted user: {user_config.user_id}")
        return user_config
    
    def delete_user(self, user_id: str) -> bool:
        """Delete user configuration"""
        # Verify user exists before deletion
        if not self.user_exists(user_id):
            raise NotFoundError(f"User {user_id} not found")
        
        try:
            self.table.delete_item(Key={'user_id': user_id})
            logger.info(f"Deleted user: {user_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting user {user_id}: {e}")
            return False
    
    def user_exists(self, user_id: str) -> bool:
        """Check if user exists"""
        return self.get_user(user_id) is not None
    
    def username_exists(self, username: str, exclude_user_id: str = None) -> bool:
        """
        Check if username is already taken
        
        Args:
            username: Username to check
            exclude_user_id: User ID to exclude from check (for updates)
            
        Returns:
            True if username exists, False otherwise
        """
        user = self.get_user_by_username(username)
        if user is None:
            return False
        
        # Exclude current user if specified
        if exclude_user_id and user.user_id == exclude_user_id:
            return False
        
        return True
    
    def email_exists(self, email: str, exclude_user_id: str = None) -> bool:
        """
        Check if email is already registered
        
        Args:
            email: Email to check
            exclude_user_id: User ID to exclude from check (for updates)
            
        Returns:
            True if email exists, False otherwise
        """
        user = self.get_user_by_email(email)
        if user is None:
            return False
        
        # Exclude current user if specified
        if exclude_user_id and user.user_id == exclude_user_id:
            return False
        
        return True
    
    def authenticate_user(self, username: str, password: str) -> Optional[EncryptedUserConfig]:
        """
        Authenticate user by username and password
        
        Args:
            username: Username
            password: Password
            
        Returns:
            User configuration if authentication successful, None otherwise
        """
        user = self.get_user_by_username(username)
        if not user:
            logger.warning(f"Authentication failed: user not found - {username}")
            return None
        
        if not user.is_active:
            logger.warning(f"Authentication failed: user inactive - {username}")
            return None
        
        # Compare passwords (they're decrypted automatically)
        if user.password == password:
            user.update_last_login()
            self.update_user(user, validate_credentials=False)
            logger.info(f"User authenticated successfully: {username}")
            return user
        
        logger.warning(f"Authentication failed: invalid password - {username}")
        return None
    
    def get_active_users(self) -> List[EncryptedUserConfig]:
        """Get all active users with decrypted data"""
        try:
            response = self.table.scan(
                FilterExpression='is_active = :is_active',
                ExpressionAttributeValues={':is_active': True}
            )
            
            users = []
            for item in response.get('Items', []):
                try:
                    user = EncryptedUserConfig.from_storage_dict(item)
                    users.append(user)
                except Exception as e:
                    logger.warning(f"Failed to decrypt user record: {e}")
                    continue
            
            logger.debug(f"Retrieved {len(users)} active users")
            return users
            
        except Exception as e:
            logger.error(f"Error getting active users: {e}")
            raise
    
    def get_users_with_weak_credentials(self) -> List[EncryptedUserConfig]:
        """Get users with weak credentials"""
        try:
            active_users = self.get_active_users()
            weak_credential_users = []
            
            for user in active_users:
                if user.has_weak_credentials():
                    weak_credential_users.append(user)
            
            logger.debug(f"Found {len(weak_credential_users)} users with weak credentials")
            return weak_credential_users
            
        except Exception as e:
            logger.error(f"Error getting users with weak credentials: {e}")
            raise
    
    def update_user_password(self, user_id: str, new_password: str, validate_strength: bool = True) -> EncryptedUserConfig:
        """
        Update user password with validation
        
        Args:
            user_id: User ID
            new_password: New password
            validate_strength: Whether to validate password strength
            
        Returns:
            Updated user configuration
        """
        user = self.get_user(user_id)
        if not user:
            raise NotFoundError(f"User {user_id} not found")
        
        user.update_password(new_password, validate_strength)
        return self.update_user(user, validate_credentials=validate_strength)
    
    def update_user_email(self, user_id: str, new_email: str, validate_format: bool = True) -> EncryptedUserConfig:
        """
        Update user email with validation
        
        Args:
            user_id: User ID
            new_email: New email address
            validate_format: Whether to validate email format
            
        Returns:
            Updated user configuration
        """
        user = self.get_user(user_id)
        if not user:
            raise NotFoundError(f"User {user_id} not found")
        
        # Check if email is already taken
        if self.email_exists(new_email, exclude_user_id=user_id):
            raise ValueError(f"Email already registered: {new_email}")
        
        user.update_email(new_email, validate_format)
        return self.update_user(user, validate_credentials=validate_format)
    
    def get_user_security_summary(self, user_id: str) -> Dict[str, Any]:
        """
        Get security summary for a user
        
        Args:
            user_id: User ID
            
        Returns:
            Dictionary with security information
        """
        user = self.get_user(user_id)
        if not user:
            raise NotFoundError(f"User {user_id} not found")
        
        validation_summary = user.get_credential_validation_summary()
        
        return {
            'user_id': user_id,
            'has_weak_credentials': user.has_weak_credentials(),
            'credential_validation': validation_summary,
            'recommendations': user.get_security_recommendations(),
            'encryption_status': user.get_encryption_status(),
            'last_login': user.last_login,
            'is_active': user.is_active
        }
    
    def _validate_user_credentials(self, user_config: EncryptedUserConfig):
        """Validate user credentials"""
        validation_results = user_config.validate_all_credentials()
        
        invalid_fields = [field for field, is_valid in validation_results.items() if not is_valid]
        
        if invalid_fields:
            raise ValueError(f"Invalid credentials for fields: {', '.join(invalid_fields)}")
    
    def _check_username_email_uniqueness(self, user_config: EncryptedUserConfig, exclude_user_id: str = None):
        """Check username and email uniqueness"""
        if self.username_exists(user_config.username, exclude_user_id):
            raise ValueError(f"Username already exists: {user_config.username}")
        
        if self.email_exists(user_config.email, exclude_user_id):
            raise ValueError(f"Email already registered: {user_config.email}")
    
    def get_encryption_health_check(self) -> Dict[str, Any]:
        """
        Get encryption health check for user data
        
        Returns:
            Dictionary with encryption health information
        """
        try:
            # Test encryption/decryption with sample user
            test_user = EncryptedUserConfig(
                user_id="test_encryption_user",
                username="test_user",
                password="test_password",
                email="test@example.com",
                first_name="Test",
                last_name="User"
            )
            
            # Test storage conversion
            storage_data = test_user.to_storage_dict()
            recovered_user = EncryptedUserConfig.from_storage_dict(storage_data)
            
            # Verify data integrity
            integrity_check = (
                recovered_user.username == test_user.username and
                recovered_user.password == test_user.password and
                recovered_user.email == test_user.email
            )
            
            return {
                'status': 'healthy' if integrity_check else 'unhealthy',
                'encryption_enabled': True,
                'integrity_check': integrity_check,
                'credential_storage_health': self.credential_storage.health_check(),
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Encryption health check failed: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }