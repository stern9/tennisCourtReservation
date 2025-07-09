# ABOUTME: Encryption utilities for sensitive data using AWS KMS and envelope encryption
# ABOUTME: Provides secure encrypt/decrypt operations with proper key management and audit logging

import os
import base64
import json
import logging
from typing import Optional, Dict, Any, Union
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class EncryptionError(Exception):
    """Custom exception for encryption-related errors"""
    pass


class KeyManagementError(Exception):
    """Custom exception for key management errors"""
    pass


class EncryptionService:
    """
    Encryption service using AWS KMS with envelope encryption for performance.
    Provides secure encryption/decryption with proper key management.
    """
    
    def __init__(self, environment: str = "development"):
        """
        Initialize encryption service
        
        Args:
            environment: Environment name (development, staging, production)
        """
        self.environment = environment
        self.kms_client = None
        self.master_key_id = None
        self._local_key = None
        self._initialize_encryption()
    
    def _initialize_encryption(self):
        """Initialize encryption based on environment"""
        try:
            if self.environment == "development":
                self._setup_local_encryption()
            else:
                self._setup_kms_encryption()
        except Exception as e:
            logger.error(f"Failed to initialize encryption: {e}")
            raise EncryptionError(f"Encryption initialization failed: {e}")
    
    def _setup_local_encryption(self):
        """Setup local encryption for development environment"""
        try:
            # Use environment variable or generate a development key
            dev_key = os.getenv('TENNIS_DEV_ENCRYPTION_KEY')
            if not dev_key:
                # Generate a key from a known password for development
                password = os.getenv('TENNIS_DEV_PASSWORD', 'tennis-dev-key-2025').encode()
                salt = b'tennis-booking-salt-2025'
                kdf = PBKDF2HMAC(
                    algorithm=hashes.SHA256(),
                    length=32,
                    salt=salt,
                    iterations=100000,
                )
                key = base64.urlsafe_b64encode(kdf.derive(password))
                self._local_key = Fernet(key)
                logger.info("Local encryption initialized with derived key")
            else:
                self._local_key = Fernet(dev_key.encode())
                logger.info("Local encryption initialized with provided key")
        except Exception as e:
            logger.error(f"Failed to setup local encryption: {e}")
            raise KeyManagementError(f"Local encryption setup failed: {e}")
    
    def _setup_kms_encryption(self):
        """Setup KMS encryption for production environment"""
        try:
            self.kms_client = boto3.client('kms')
            self.master_key_id = self._get_master_key_id()
            logger.info(f"KMS encryption initialized for {self.environment}")
        except Exception as e:
            logger.error(f"Failed to setup KMS encryption: {e}")
            raise KeyManagementError(f"KMS encryption setup failed: {e}")
    
    def _get_master_key_id(self) -> str:
        """Get KMS master key ID for current environment"""
        env_key_map = {
            'development': 'TENNIS_DEV_KMS_KEY_ID',
            'staging': 'TENNIS_STAGING_KMS_KEY_ID',
            'production': 'TENNIS_PROD_KMS_KEY_ID'
        }
        
        key_env_var = env_key_map.get(self.environment)
        if not key_env_var:
            raise KeyManagementError(f"No KMS key mapping for environment: {self.environment}")
        
        key_id = os.getenv(key_env_var)
        if not key_id:
            raise KeyManagementError(f"KMS key ID not found in environment variable: {key_env_var}")
        
        return key_id
    
    def _generate_data_key(self) -> tuple:
        """Generate data key using KMS"""
        try:
            response = self.kms_client.generate_data_key(
                KeyId=self.master_key_id,
                KeySpec='AES_256'
            )
            return response['Plaintext'], response['CiphertextBlob']
        except ClientError as e:
            logger.error(f"Failed to generate data key: {e}")
            raise EncryptionError(f"Data key generation failed: {e}")
    
    def _decrypt_data_key(self, encrypted_key: bytes) -> bytes:
        """Decrypt data key using KMS"""
        try:
            response = self.kms_client.decrypt(CiphertextBlob=encrypted_key)
            return response['Plaintext']
        except ClientError as e:
            logger.error(f"Failed to decrypt data key: {e}")
            raise EncryptionError(f"Data key decryption failed: {e}")
    
    def encrypt(self, plaintext: str, context: Optional[Dict[str, str]] = None) -> str:
        """
        Encrypt plaintext string
        
        Args:
            plaintext: String to encrypt
            context: Additional context for encryption (used for audit logging)
            
        Returns:
            Base64-encoded encrypted data with metadata
        """
        if not plaintext:
            raise ValueError("Cannot encrypt empty string")
        
        try:
            if self.environment == "development":
                return self._encrypt_local(plaintext)
            else:
                return self._encrypt_with_kms(plaintext, context)
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            raise EncryptionError(f"Encryption failed: {e}")
    
    def decrypt(self, encrypted_data: str, context: Optional[Dict[str, str]] = None) -> str:
        """
        Decrypt encrypted string
        
        Args:
            encrypted_data: Base64-encoded encrypted data
            context: Additional context for decryption (used for audit logging)
            
        Returns:
            Decrypted plaintext string
        """
        if not encrypted_data:
            raise ValueError("Cannot decrypt empty string")
        
        try:
            if self.environment == "development":
                return self._decrypt_local(encrypted_data)
            else:
                return self._decrypt_with_kms(encrypted_data, context)
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise EncryptionError(f"Decryption failed: {e}")
    
    def _encrypt_local(self, plaintext: str) -> str:
        """Encrypt using local key for development"""
        try:
            encrypted = self._local_key.encrypt(plaintext.encode())
            return base64.urlsafe_b64encode(encrypted).decode()
        except Exception as e:
            raise EncryptionError(f"Local encryption failed: {e}")
    
    def _decrypt_local(self, encrypted_data: str) -> str:
        """Decrypt using local key for development"""
        try:
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode())
            decrypted = self._local_key.decrypt(encrypted_bytes)
            return decrypted.decode()
        except Exception as e:
            raise EncryptionError(f"Local decryption failed: {e}")
    
    def _encrypt_with_kms(self, plaintext: str, context: Optional[Dict[str, str]] = None) -> str:
        """Encrypt using KMS envelope encryption"""
        try:
            # Generate data key
            data_key, encrypted_data_key = self._generate_data_key()
            
            # Create Fernet cipher with data key
            fernet = Fernet(base64.urlsafe_b64encode(data_key[:32]))
            
            # Encrypt the plaintext
            encrypted_text = fernet.encrypt(plaintext.encode())
            
            # Create envelope with encrypted data key and encrypted text
            envelope = {
                'version': '1.0',
                'encrypted_data_key': base64.urlsafe_b64encode(encrypted_data_key).decode(),
                'encrypted_text': base64.urlsafe_b64encode(encrypted_text).decode(),
                'environment': self.environment
            }
            
            # Add context if provided
            if context:
                envelope['context'] = context
            
            # Log encryption operation for audit
            self._log_encryption_operation('encrypt', context)
            
            return base64.urlsafe_b64encode(json.dumps(envelope).encode()).decode()
        except Exception as e:
            raise EncryptionError(f"KMS encryption failed: {e}")
    
    def _decrypt_with_kms(self, encrypted_data: str, context: Optional[Dict[str, str]] = None) -> str:
        """Decrypt using KMS envelope encryption"""
        try:
            # Decode envelope
            envelope_data = base64.urlsafe_b64decode(encrypted_data.encode())
            envelope = json.loads(envelope_data.decode())
            
            # Validate envelope format
            if envelope.get('version') != '1.0':
                raise EncryptionError("Unsupported envelope version")
            
            # Decrypt data key
            encrypted_data_key = base64.urlsafe_b64decode(envelope['encrypted_data_key'])
            data_key = self._decrypt_data_key(encrypted_data_key)
            
            # Create Fernet cipher with data key
            fernet = Fernet(base64.urlsafe_b64encode(data_key[:32]))
            
            # Decrypt the text
            encrypted_text = base64.urlsafe_b64decode(envelope['encrypted_text'])
            decrypted_text = fernet.decrypt(encrypted_text)
            
            # Log decryption operation for audit
            self._log_encryption_operation('decrypt', context)
            
            return decrypted_text.decode()
        except Exception as e:
            raise EncryptionError(f"KMS decryption failed: {e}")
    
    def _log_encryption_operation(self, operation: str, context: Optional[Dict[str, str]] = None):
        """Log encryption operation for audit trail"""
        try:
            log_entry = {
                'operation': operation,
                'environment': self.environment,
                'timestamp': str(self._get_timestamp()),
                'context': context or {}
            }
            
            # In production, this would go to a secure audit log
            logger.info(f"Encryption audit: {json.dumps(log_entry)}")
        except Exception as e:
            logger.warning(f"Failed to log encryption operation: {e}")
    
    def _get_timestamp(self):
        """Get current timestamp for logging"""
        from datetime import datetime
        return datetime.utcnow().isoformat()
    
    def encrypt_sensitive_data(self, data: Dict[str, Any], sensitive_fields: list) -> Dict[str, Any]:
        """
        Encrypt sensitive fields in a data dictionary
        
        Args:
            data: Dictionary containing data to encrypt
            sensitive_fields: List of field names to encrypt
            
        Returns:
            Dictionary with sensitive fields encrypted
        """
        encrypted_data = data.copy()
        
        for field in sensitive_fields:
            if field in encrypted_data and encrypted_data[field]:
                context = {'field': field, 'operation': 'field_encryption'}
                encrypted_data[field] = self.encrypt(str(encrypted_data[field]), context)
        
        return encrypted_data
    
    def decrypt_sensitive_data(self, data: Dict[str, Any], sensitive_fields: list) -> Dict[str, Any]:
        """
        Decrypt sensitive fields in a data dictionary
        
        Args:
            data: Dictionary containing encrypted data
            sensitive_fields: List of field names to decrypt
            
        Returns:
            Dictionary with sensitive fields decrypted
        """
        decrypted_data = data.copy()
        
        for field in sensitive_fields:
            if field in decrypted_data and decrypted_data[field]:
                context = {'field': field, 'operation': 'field_decryption'}
                decrypted_data[field] = self.decrypt(decrypted_data[field], context)
        
        return decrypted_data
    
    def rotate_key(self) -> bool:
        """
        Rotate encryption key (placeholder for key rotation implementation)
        
        Returns:
            True if rotation successful, False otherwise
        """
        if self.environment == "development":
            logger.info("Key rotation not required for development environment")
            return True
        
        try:
            # In production, this would implement key rotation
            logger.info("Key rotation feature not yet implemented")
            return True
        except Exception as e:
            logger.error(f"Key rotation failed: {e}")
            return False
    
    def health_check(self) -> Dict[str, Any]:
        """
        Check encryption service health
        
        Returns:
            Dictionary containing health status
        """
        try:
            # Test encryption/decryption
            test_data = "health_check_test_data"
            encrypted = self.encrypt(test_data)
            decrypted = self.decrypt(encrypted)
            
            if decrypted != test_data:
                raise EncryptionError("Encryption/decryption test failed")
            
            return {
                'status': 'healthy',
                'environment': self.environment,
                'encryption_mode': 'local' if self.environment == 'development' else 'kms',
                'timestamp': self._get_timestamp()
            }
        except Exception as e:
            logger.error(f"Encryption health check failed: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e),
                'environment': self.environment,
                'timestamp': self._get_timestamp()
            }


# Global encryption service instance
_encryption_service = None


def get_encryption_service(environment: str = None) -> EncryptionService:
    """
    Get global encryption service instance
    
    Args:
        environment: Environment name (optional, defaults to env var or 'development')
        
    Returns:
        EncryptionService instance
    """
    global _encryption_service
    
    if _encryption_service is None:
        if environment is None:
            environment = os.getenv('TENNIS_ENVIRONMENT', 'development')
        _encryption_service = EncryptionService(environment)
    
    return _encryption_service


def encrypt_field(value: str, field_name: str = None) -> str:
    """
    Convenience function to encrypt a field value
    
    Args:
        value: Value to encrypt
        field_name: Name of the field (for context)
        
    Returns:
        Encrypted value
    """
    service = get_encryption_service()
    context = {'field': field_name} if field_name else None
    return service.encrypt(value, context)


def decrypt_field(encrypted_value: str, field_name: str = None) -> str:
    """
    Convenience function to decrypt a field value
    
    Args:
        encrypted_value: Encrypted value to decrypt
        field_name: Name of the field (for context)
        
    Returns:
        Decrypted value
    """
    service = get_encryption_service()
    context = {'field': field_name} if field_name else None
    return service.decrypt(encrypted_value, context)