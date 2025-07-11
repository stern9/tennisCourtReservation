# ABOUTME: Enhanced UserConfig model with encryption integration for sensitive data
# ABOUTME: Extends base UserConfig with automatic encryption/decryption of sensitive fields

from typing import Optional, List, Dict, Any
from pydantic import Field, validator
import logging

from .user_config import UserConfig
from ..security import get_credential_storage, CredentialStorage

logger = logging.getLogger(__name__)


class EncryptedUserConfig(UserConfig):
    """
    Enhanced UserConfig with automatic encryption/decryption of sensitive fields
    """
    
    # Track which fields are encrypted in storage
    _encrypted_fields = {'username', 'password', 'email', 'phone_number'}
    
    def __init__(self, **data):
        """Initialize with automatic decryption if needed"""
        # Get credential storage service
        self._credential_storage = get_credential_storage()
        
        # Decrypt sensitive fields if they appear to be encrypted
        decrypted_data = self._decrypt_if_needed(data)
        
        super().__init__(**decrypted_data)
    
    def _decrypt_if_needed(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Decrypt fields if they appear to be encrypted"""
        decrypted_data = data.copy()
        
        for field_name, value in data.items():
            if (field_name in self._encrypted_fields and 
                value and 
                isinstance(value, str) and 
                self._appears_encrypted(value)):
                try:
                    # Attempt to decrypt
                    decrypted_data[field_name] = self._credential_storage.decrypt_field(value, field_name)
                    logger.debug(f"Decrypted field: {field_name}")
                except Exception as e:
                    logger.warning(f"Failed to decrypt field {field_name}: {e}")
                    # Keep original value if decryption fails
                    decrypted_data[field_name] = value
        
        return decrypted_data
    
    def _appears_encrypted(self, value: str) -> bool:
        """Check if a value appears to be encrypted"""
        # Simple heuristic: encrypted values are typically base64 and longer than typical plaintext
        if len(value) < 20:
            return False
        
        # Check if it looks like base64
        import re
        base64_pattern = r'^[A-Za-z0-9+/]*={0,2}$'
        return bool(re.match(base64_pattern, value))
    
    def to_storage_dict(self, user_id: str = None) -> Dict[str, Any]:
        """
        Convert to dictionary with encrypted sensitive fields for storage
        
        Args:
            user_id: User ID for encryption context
            
        Returns:
            Dictionary with encrypted sensitive fields
        """
        # Get base dictionary
        data = self.dict()
        
        # Encrypt sensitive fields
        encrypted_data = self._credential_storage.encrypt_user_data(
            data, 
            user_id or self.user_id
        )
        
        logger.debug(f"Encrypted {len(self._encrypted_fields)} sensitive fields for storage")
        return encrypted_data
    
    @classmethod
    def from_storage_dict(cls, data: Dict[str, Any], user_id: str = None) -> 'EncryptedUserConfig':
        """
        Create instance from storage dictionary with encrypted fields
        
        Args:
            data: Dictionary from storage (with encrypted fields)
            user_id: User ID for decryption context
            
        Returns:
            EncryptedUserConfig instance with decrypted fields
        """
        credential_storage = get_credential_storage()
        
        # Decrypt sensitive fields
        decrypted_data = credential_storage.decrypt_user_data(
            data,
            user_id or data.get('user_id')
        )
        
        logger.debug(f"Decrypted sensitive fields from storage for user: {user_id}")
        return cls(**decrypted_data)
    
    def update_password(self, new_password: str, validate_strength: bool = True) -> None:
        """
        Update user password with validation
        
        Args:
            new_password: New password
            validate_strength: Whether to validate password strength
        """
        if validate_strength:
            validation = self._credential_storage.validate_credential_strength(
                'password', new_password
            )
            if not validation['is_valid']:
                raise ValueError(f"Password validation failed: {', '.join(validation['issues'])}")
        
        self.password = new_password
        logger.info(f"Password updated for user: {self.user_id}")
    
    def update_email(self, new_email: str, validate_format: bool = True) -> None:
        """
        Update user email with validation
        
        Args:
            new_email: New email address
            validate_format: Whether to validate email format
        """
        if validate_format:
            validation = self._credential_storage.validate_credential_strength(
                'email', new_email
            )
            if not validation['is_valid']:
                raise ValueError(f"Email validation failed: {', '.join(validation['issues'])}")
        
        self.email = new_email
        logger.info(f"Email updated for user: {self.user_id}")
    
    def update_username(self, new_username: str, validate_format: bool = True) -> None:
        """
        Update username with validation
        
        Args:
            new_username: New username
            validate_format: Whether to validate username format
        """
        if validate_format:
            validation = self._credential_storage.validate_credential_strength(
                'username', new_username
            )
            if not validation['is_valid']:
                raise ValueError(f"Username validation failed: {', '.join(validation['issues'])}")
        
        self.username = new_username
        logger.info(f"Username updated for user: {self.user_id}")
    
    def get_credential_validation_summary(self) -> Dict[str, Any]:
        """
        Get validation summary for all credentials
        
        Returns:
            Dictionary with validation results for each credential
        """
        validation_summary = {}
        
        for field_name in self._encrypted_fields:
            value = getattr(self, field_name, None)
            if value:
                validation = self._credential_storage.validate_credential_strength(field_name, value)
                validation_summary[field_name] = validation
        
        return validation_summary
    
    def has_weak_credentials(self) -> bool:
        """
        Check if user has any weak credentials
        
        Returns:
            True if any credentials are weak, False otherwise
        """
        validation_summary = self.get_credential_validation_summary()
        
        for field_name, validation in validation_summary.items():
            if not validation.get('is_valid', True) or validation.get('score', 100) < 70:
                return True
        
        return False
    
    def get_security_recommendations(self) -> List[str]:
        """
        Get security recommendations for the user
        
        Returns:
            List of security recommendations
        """
        recommendations = []
        validation_summary = self.get_credential_validation_summary()
        
        for field_name, validation in validation_summary.items():
            if not validation.get('is_valid', True):
                recommendations.extend([
                    f"{field_name.title()}: {issue}" 
                    for issue in validation.get('issues', [])
                ])
            
            recommendations.extend(validation.get('recommendations', []))
        
        # Additional security recommendations
        if not self.phone_number:
            recommendations.append("Consider adding a phone number for account recovery")
        
        if not self.notifications_enabled:
            recommendations.append("Enable notifications for security alerts")
        
        return list(set(recommendations))  # Remove duplicates
    
    def mask_sensitive_data(self) -> Dict[str, Any]:
        """
        Get user data with sensitive fields masked for logging/display
        
        Returns:
            Dictionary with sensitive fields masked
        """
        data = self.dict()
        
        # Mask sensitive fields
        for field_name in self._encrypted_fields:
            if field_name in data and data[field_name]:
                if field_name == 'email':
                    # Mask email partially
                    email = data[field_name]
                    if '@' in email:
                        local, domain = email.split('@', 1)
                        masked_local = local[0] + '*' * (len(local) - 2) + local[-1] if len(local) > 2 else '*' * len(local)
                        data[field_name] = f"{masked_local}@{domain}"
                    else:
                        data[field_name] = '***'
                elif field_name == 'phone_number':
                    # Mask phone number partially
                    phone = data[field_name]
                    if len(phone) > 4:
                        data[field_name] = '*' * (len(phone) - 4) + phone[-4:]
                    else:
                        data[field_name] = '***'
                else:
                    # Completely mask other sensitive fields
                    data[field_name] = '***'
        
        return data
    
    def to_public_dict(self) -> Dict[str, Any]:
        """
        Get public representation without sensitive data
        
        Returns:
            Dictionary safe for public consumption
        """
        public_data = {
            'user_id': self.user_id,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'preferred_courts': self.preferred_courts,
            'preferred_times': self.preferred_times,
            'auto_book': self.auto_book,
            'max_bookings_per_day': self.max_bookings_per_day,
            'booking_advance_days': self.booking_advance_days,
            'notifications_enabled': self.notifications_enabled,
            'is_active': self.is_active,
            'last_login': self.last_login,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
        
        # Add masked email for display
        if self.email:
            email = self.email
            if '@' in email:
                local, domain = email.split('@', 1)
                masked_local = local[0] + '*' * (len(local) - 2) + local[-1] if len(local) > 2 else '*' * len(local)
                public_data['masked_email'] = f"{masked_local}@{domain}"
        
        return public_data
    
    def validate_all_credentials(self) -> Dict[str, bool]:
        """
        Validate all credentials and return results
        
        Returns:
            Dictionary mapping field names to validation status
        """
        results = {}
        
        for field_name in self._encrypted_fields:
            value = getattr(self, field_name, None)
            if value:
                validation = self._credential_storage.validate_credential_strength(field_name, value)
                results[field_name] = validation.get('is_valid', False)
            else:
                results[field_name] = True  # Empty values are considered valid
        
        return results
    
    def get_encryption_status(self) -> Dict[str, bool]:
        """
        Get encryption status for sensitive fields
        
        Returns:
            Dictionary showing which fields are encrypted
        """
        return {
            field_name: field_name in self._encrypted_fields
            for field_name in ['username', 'password', 'email', 'phone_number']
        }
    
    class Config(UserConfig.Config):
        """Enhanced configuration for encrypted user config"""
        
        @staticmethod
        def schema_extra(schema: Dict[str, Any], model_class) -> None:
            """Add encryption information to schema"""
            UserConfig.Config.schema_extra(schema, model_class)
            
            # Add encryption information
            schema["properties"]["_encryption_info"] = {
                "type": "object",
                "description": "Information about field encryption",
                "properties": {
                    "encrypted_fields": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of fields that are encrypted in storage"
                    },
                    "encryption_enabled": {
                        "type": "boolean",
                        "description": "Whether encryption is enabled"
                    }
                }
            }