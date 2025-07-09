# ABOUTME: Secure credential storage utilities with encryption and validation
# ABOUTME: Handles encrypted storage and retrieval of sensitive user credentials

import logging
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field, validator
from .encryption import get_encryption_service, EncryptionService

logger = logging.getLogger(__name__)


class CredentialError(Exception):
    """Custom exception for credential-related errors"""
    pass


class EncryptedCredential(BaseModel):
    """Model for encrypted credential storage"""
    
    field_name: str = Field(..., description="Name of the credential field")
    encrypted_value: str = Field(..., description="Encrypted credential value")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")
    is_active: bool = Field(default=True, description="Whether credential is active")
    
    @validator('field_name')
    def validate_field_name(cls, v):
        if not v or not isinstance(v, str):
            raise ValueError("Field name must be a non-empty string")
        return v.strip()
    
    @validator('encrypted_value')
    def validate_encrypted_value(cls, v):
        if not v or not isinstance(v, str):
            raise ValueError("Encrypted value must be a non-empty string")
        return v


class CredentialStorage:
    """
    Secure credential storage service with encryption and validation
    """
    
    # Fields that should be encrypted
    SENSITIVE_FIELDS = {
        'password', 'username', 'email', 'phone_number', 
        'api_key', 'token', 'secret', 'private_key'
    }
    
    def __init__(self, encryption_service: Optional[EncryptionService] = None):
        """
        Initialize credential storage
        
        Args:
            encryption_service: Optional encryption service instance
        """
        self.encryption_service = encryption_service or get_encryption_service()
    
    def store_credential(self, field_name: str, value: str, user_id: str = None) -> EncryptedCredential:
        """
        Store a credential securely with encryption
        
        Args:
            field_name: Name of the credential field
            value: Credential value to encrypt and store
            user_id: Optional user ID for context
            
        Returns:
            EncryptedCredential instance
        """
        if not self.is_sensitive_field(field_name):
            logger.warning(f"Field '{field_name}' is not marked as sensitive")
        
        try:
            # Create encryption context
            context = {
                'field': field_name,
                'user_id': user_id or 'unknown',
                'operation': 'credential_storage'
            }
            
            # Encrypt the value
            encrypted_value = self.encryption_service.encrypt(value, context)
            
            # Create timestamp
            timestamp = self._get_timestamp()
            
            # Create encrypted credential
            credential = EncryptedCredential(
                field_name=field_name,
                encrypted_value=encrypted_value,
                created_at=timestamp,
                updated_at=timestamp,
                is_active=True
            )
            
            logger.info(f"Credential stored for field: {field_name}")
            return credential
            
        except Exception as e:
            logger.error(f"Failed to store credential for field '{field_name}': {e}")
            raise CredentialError(f"Credential storage failed: {e}")
    
    def retrieve_credential(self, encrypted_credential: EncryptedCredential, user_id: str = None) -> str:
        """
        Retrieve and decrypt a credential
        
        Args:
            encrypted_credential: EncryptedCredential instance
            user_id: Optional user ID for context
            
        Returns:
            Decrypted credential value
        """
        if not encrypted_credential.is_active:
            raise CredentialError("Credential is not active")
        
        try:
            # Create decryption context
            context = {
                'field': encrypted_credential.field_name,
                'user_id': user_id or 'unknown',
                'operation': 'credential_retrieval'
            }
            
            # Decrypt the value
            decrypted_value = self.encryption_service.decrypt(
                encrypted_credential.encrypted_value, context
            )
            
            logger.info(f"Credential retrieved for field: {encrypted_credential.field_name}")
            return decrypted_value
            
        except Exception as e:
            logger.error(f"Failed to retrieve credential for field '{encrypted_credential.field_name}': {e}")
            raise CredentialError(f"Credential retrieval failed: {e}")
    
    def update_credential(self, encrypted_credential: EncryptedCredential, new_value: str, user_id: str = None) -> EncryptedCredential:
        """
        Update an existing credential with a new value
        
        Args:
            encrypted_credential: Existing EncryptedCredential instance
            new_value: New credential value
            user_id: Optional user ID for context
            
        Returns:
            Updated EncryptedCredential instance
        """
        try:
            # Create encryption context
            context = {
                'field': encrypted_credential.field_name,
                'user_id': user_id or 'unknown',
                'operation': 'credential_update'
            }
            
            # Encrypt the new value
            encrypted_value = self.encryption_service.encrypt(new_value, context)
            
            # Update the credential
            encrypted_credential.encrypted_value = encrypted_value
            encrypted_credential.updated_at = self._get_timestamp()
            
            logger.info(f"Credential updated for field: {encrypted_credential.field_name}")
            return encrypted_credential
            
        except Exception as e:
            logger.error(f"Failed to update credential for field '{encrypted_credential.field_name}': {e}")
            raise CredentialError(f"Credential update failed: {e}")
    
    def deactivate_credential(self, encrypted_credential: EncryptedCredential) -> EncryptedCredential:
        """
        Deactivate a credential (soft delete)
        
        Args:
            encrypted_credential: EncryptedCredential instance to deactivate
            
        Returns:
            Updated EncryptedCredential instance
        """
        encrypted_credential.is_active = False
        encrypted_credential.updated_at = self._get_timestamp()
        
        logger.info(f"Credential deactivated for field: {encrypted_credential.field_name}")
        return encrypted_credential
    
    def is_sensitive_field(self, field_name: str) -> bool:
        """
        Check if a field should be encrypted
        
        Args:
            field_name: Name of the field to check
            
        Returns:
            True if field should be encrypted, False otherwise
        """
        return field_name.lower() in self.SENSITIVE_FIELDS
    
    def encrypt_user_data(self, user_data: Dict[str, Any], user_id: str = None) -> Dict[str, Any]:
        """
        Encrypt sensitive fields in user data dictionary
        
        Args:
            user_data: Dictionary containing user data
            user_id: Optional user ID for context
            
        Returns:
            Dictionary with sensitive fields encrypted
        """
        encrypted_data = user_data.copy()
        
        for field_name, value in user_data.items():
            if self.is_sensitive_field(field_name) and value:
                try:
                    encrypted_credential = self.store_credential(field_name, str(value), user_id)
                    encrypted_data[field_name] = encrypted_credential.encrypted_value
                except Exception as e:
                    logger.error(f"Failed to encrypt field '{field_name}': {e}")
                    raise
        
        return encrypted_data
    
    def decrypt_user_data(self, encrypted_data: Dict[str, Any], user_id: str = None) -> Dict[str, Any]:
        """
        Decrypt sensitive fields in user data dictionary
        
        Args:
            encrypted_data: Dictionary containing encrypted data
            user_id: Optional user ID for context
            
        Returns:
            Dictionary with sensitive fields decrypted
        """
        decrypted_data = encrypted_data.copy()
        
        for field_name, encrypted_value in encrypted_data.items():
            if self.is_sensitive_field(field_name) and encrypted_value:
                try:
                    # Create a temporary EncryptedCredential for decryption
                    temp_credential = EncryptedCredential(
                        field_name=field_name,
                        encrypted_value=encrypted_value,
                        created_at=self._get_timestamp(),
                        updated_at=self._get_timestamp(),
                        is_active=True
                    )
                    
                    decrypted_value = self.retrieve_credential(temp_credential, user_id)
                    decrypted_data[field_name] = decrypted_value
                except Exception as e:
                    logger.error(f"Failed to decrypt field '{field_name}': {e}")
                    raise
        
        return decrypted_data
    
    def validate_credential_strength(self, field_name: str, value: str) -> Dict[str, Any]:
        """
        Validate credential strength based on field type
        
        Args:
            field_name: Name of the credential field
            value: Credential value to validate
            
        Returns:
            Dictionary containing validation results
        """
        validation_result = {
            'is_valid': True,
            'score': 0,
            'issues': [],
            'recommendations': []
        }
        
        if field_name.lower() == 'password':
            return self._validate_password_strength(value)
        elif field_name.lower() == 'username':
            return self._validate_username_strength(value)
        elif field_name.lower() == 'email':
            return self._validate_email_format(value)
        else:
            # Basic validation for other fields
            if len(value) < 3:
                validation_result['is_valid'] = False
                validation_result['issues'].append("Value too short")
            elif len(value) > 255:
                validation_result['is_valid'] = False
                validation_result['issues'].append("Value too long")
            else:
                validation_result['score'] = 50
        
        return validation_result
    
    def _validate_password_strength(self, password: str) -> Dict[str, Any]:
        """Validate password strength"""
        result = {
            'is_valid': True,
            'score': 0,
            'issues': [],
            'recommendations': []
        }
        
        if len(password) < 8:
            result['is_valid'] = False
            result['issues'].append("Password too short (minimum 8 characters)")
        else:
            result['score'] += 20
        
        if not any(c.isupper() for c in password):
            result['issues'].append("No uppercase letters")
        else:
            result['score'] += 15
        
        if not any(c.islower() for c in password):
            result['issues'].append("No lowercase letters")
        else:
            result['score'] += 15
        
        if not any(c.isdigit() for c in password):
            result['issues'].append("No numbers")
        else:
            result['score'] += 15
        
        if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
            result['issues'].append("No special characters")
        else:
            result['score'] += 15
        
        if len(password) >= 12:
            result['score'] += 10
        
        if len(password) >= 16:
            result['score'] += 10
        
        if result['score'] < 50:
            result['is_valid'] = False
            result['recommendations'].append("Use a stronger password with mixed case, numbers, and symbols")
        
        return result
    
    def _validate_username_strength(self, username: str) -> Dict[str, Any]:
        """Validate username format"""
        result = {
            'is_valid': True,
            'score': 80,
            'issues': [],
            'recommendations': []
        }
        
        if len(username) < 3:
            result['is_valid'] = False
            result['issues'].append("Username too short (minimum 3 characters)")
        elif len(username) > 50:
            result['is_valid'] = False
            result['issues'].append("Username too long (maximum 50 characters)")
        
        import re
        if not re.match(r'^[a-zA-Z0-9_.-]+$', username):
            result['is_valid'] = False
            result['issues'].append("Username contains invalid characters")
        
        return result
    
    def _validate_email_format(self, email: str) -> Dict[str, Any]:
        """Validate email format"""
        result = {
            'is_valid': True,
            'score': 90,
            'issues': [],
            'recommendations': []
        }
        
        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            result['is_valid'] = False
            result['issues'].append("Invalid email format")
        
        return result
    
    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime
        return datetime.utcnow().isoformat()
    
    def health_check(self) -> Dict[str, Any]:
        """
        Check credential storage health
        
        Returns:
            Dictionary containing health status
        """
        try:
            # Test credential storage and retrieval
            test_credential = self.store_credential('test_field', 'test_value', 'health_check')
            retrieved_value = self.retrieve_credential(test_credential, 'health_check')
            
            if retrieved_value != 'test_value':
                raise CredentialError("Credential storage test failed")
            
            return {
                'status': 'healthy',
                'timestamp': self._get_timestamp(),
                'encryption_service': self.encryption_service.health_check()
            }
        except Exception as e:
            logger.error(f"Credential storage health check failed: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': self._get_timestamp()
            }


# Global credential storage instance
_credential_storage = None


def get_credential_storage() -> CredentialStorage:
    """
    Get global credential storage instance
    
    Returns:
        CredentialStorage instance
    """
    global _credential_storage
    
    if _credential_storage is None:
        _credential_storage = CredentialStorage()
    
    return _credential_storage


def store_secure_credential(field_name: str, value: str, user_id: str = None) -> EncryptedCredential:
    """
    Convenience function to store a credential securely
    
    Args:
        field_name: Name of the credential field
        value: Credential value to encrypt and store
        user_id: Optional user ID for context
        
    Returns:
        EncryptedCredential instance
    """
    storage = get_credential_storage()
    return storage.store_credential(field_name, value, user_id)


def retrieve_secure_credential(encrypted_credential: EncryptedCredential, user_id: str = None) -> str:
    """
    Convenience function to retrieve a credential securely
    
    Args:
        encrypted_credential: EncryptedCredential instance
        user_id: Optional user ID for context
        
    Returns:
        Decrypted credential value
    """
    storage = get_credential_storage()
    return storage.retrieve_credential(encrypted_credential, user_id)