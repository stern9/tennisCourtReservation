# ABOUTME: Comprehensive unit tests for encryption utilities and security operations  
# ABOUTME: Tests encryption, credential storage, and key management functionality

import pytest
import os
import tempfile
import shutil
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

from src.security.encryption import (
    EncryptionService, EncryptionError, 
    get_encryption_service, encrypt_field, decrypt_field
)
from src.security.credential_storage import (
    CredentialStorage, CredentialError, EncryptedCredential,
    get_credential_storage, store_secure_credential, retrieve_secure_credential
)
from src.security.key_management import (
    KeyManager, KeyManagementError, KeyMetadata, Environment, KeyType,
    get_key_manager, initialize_encryption_keys, get_current_encryption_key
)


class TestEncryptionService:
    """Test encryption service functionality"""
    
    def setup_method(self):
        """Setup test environment"""
        self.temp_dir = tempfile.mkdtemp()
        os.environ['TENNIS_ENVIRONMENT'] = 'development'
        
    def teardown_method(self):
        """Clean up test environment"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        # Reset global instances
        import src.security.encryption as enc_module
        enc_module._encryption_service = None
        
    def test_encryption_service_initialization_development(self):
        """Test encryption service initialization for development"""
        service = EncryptionService(environment="development")
        assert service.environment == "development"
        assert service._local_key is not None
        assert service.kms_client is None
        
    def test_encryption_service_initialization_production(self):
        """Test encryption service initialization for production"""
        with patch('boto3.client') as mock_client:
            mock_client.return_value = Mock()
            os.environ['TENNIS_PROD_KMS_KEY_ID'] = 'test-key-id'
            
            service = EncryptionService(environment="production")
            assert service.environment == "production"
            assert service.kms_client is not None
            assert service.master_key_id == 'test-key-id'
            
    def test_local_encryption_decryption(self):
        """Test local encryption and decryption"""
        service = EncryptionService(environment="development")
        
        plaintext = "test_password_123"
        encrypted = service.encrypt(plaintext)
        
        assert encrypted != plaintext
        assert len(encrypted) > 0
        
        decrypted = service.decrypt(encrypted)
        assert decrypted == plaintext
        
    def test_encryption_with_context(self):
        """Test encryption with context"""
        service = EncryptionService(environment="development")
        
        plaintext = "sensitive_data"
        context = {"field": "password", "user_id": "user123"}
        
        encrypted = service.encrypt(plaintext, context)
        decrypted = service.decrypt(encrypted, context)
        
        assert decrypted == plaintext
        
    def test_encryption_empty_string_error(self):
        """Test encryption with empty string raises error"""
        service = EncryptionService(environment="development")
        
        with pytest.raises(ValueError, match="Cannot encrypt empty string"):
            service.encrypt("")
            
    def test_decryption_empty_string_error(self):
        """Test decryption with empty string raises error"""
        service = EncryptionService(environment="development")
        
        with pytest.raises(ValueError, match="Cannot decrypt empty string"):
            service.decrypt("")
            
    def test_encryption_sensitive_data_dict(self):
        """Test encryption of sensitive data dictionary"""
        service = EncryptionService(environment="development")
        
        data = {
            "username": "testuser",
            "password": "secret123",
            "email": "test@example.com",
            "name": "Test User"
        }
        
        sensitive_fields = ["username", "password", "email"]
        encrypted_data = service.encrypt_sensitive_data(data, sensitive_fields)
        
        # Sensitive fields should be encrypted
        assert encrypted_data["username"] != data["username"]
        assert encrypted_data["password"] != data["password"]
        assert encrypted_data["email"] != data["email"]
        # Non-sensitive fields should remain unchanged
        assert encrypted_data["name"] == data["name"]
        
        # Decrypt and verify
        decrypted_data = service.decrypt_sensitive_data(encrypted_data, sensitive_fields)
        assert decrypted_data["username"] == data["username"]
        assert decrypted_data["password"] == data["password"]
        assert decrypted_data["email"] == data["email"]
        assert decrypted_data["name"] == data["name"]
        
    def test_health_check_healthy(self):
        """Test health check for healthy service"""
        service = EncryptionService(environment="development")
        
        health = service.health_check()
        assert health['status'] == 'healthy'
        assert health['environment'] == 'development'
        assert health['encryption_mode'] == 'local'
        
    def test_health_check_unhealthy(self):
        """Test health check for unhealthy service"""
        service = EncryptionService(environment="development")
        
        # Mock encryption failure
        with patch.object(service, 'encrypt', side_effect=EncryptionError("Test error")):
            health = service.health_check()
            assert health['status'] == 'unhealthy'
            assert 'error' in health
            
    def test_get_encryption_service_singleton(self):
        """Test that get_encryption_service returns singleton"""
        service1 = get_encryption_service()
        service2 = get_encryption_service()
        assert service1 is service2
        
    def test_encrypt_decrypt_field_convenience_functions(self):
        """Test convenience functions for field encryption/decryption"""
        plaintext = "test_value"
        field_name = "password"
        
        encrypted = encrypt_field(plaintext, field_name)
        decrypted = decrypt_field(encrypted, field_name)
        
        assert decrypted == plaintext


class TestCredentialStorage:
    """Test credential storage functionality"""
    
    def setup_method(self):
        """Setup test environment"""
        os.environ['TENNIS_ENVIRONMENT'] = 'development'
        import src.security.credential_storage as cred_module
        cred_module._credential_storage = None
        
    def teardown_method(self):
        """Clean up test environment"""
        import src.security.credential_storage as cred_module
        cred_module._credential_storage = None
        
    def test_encrypted_credential_model(self):
        """Test EncryptedCredential model validation"""
        credential = EncryptedCredential(
            field_name="password",
            encrypted_value="encrypted_data",
            created_at="2025-01-01T00:00:00",
            updated_at="2025-01-01T00:00:00"
        )
        
        assert credential.field_name == "password"
        assert credential.encrypted_value == "encrypted_data"
        assert credential.is_active is True
        
    def test_encrypted_credential_validation_errors(self):
        """Test EncryptedCredential validation errors"""
        with pytest.raises(ValueError, match="Field name must be a non-empty string"):
            EncryptedCredential(
                field_name="",
                encrypted_value="encrypted_data",
                created_at="2025-01-01T00:00:00",
                updated_at="2025-01-01T00:00:00"
            )
            
    def test_credential_storage_initialization(self):
        """Test credential storage initialization"""
        storage = CredentialStorage()
        assert storage.encryption_service is not None
        assert "password" in storage.SENSITIVE_FIELDS
        assert "username" in storage.SENSITIVE_FIELDS
        
    def test_store_and_retrieve_credential(self):
        """Test storing and retrieving credentials"""
        storage = CredentialStorage()
        
        field_name = "password"
        value = "secret123"
        user_id = "user123"
        
        # Store credential
        credential = storage.store_credential(field_name, value, user_id)
        assert isinstance(credential, EncryptedCredential)
        assert credential.field_name == field_name
        assert credential.encrypted_value != value
        assert credential.is_active is True
        
        # Retrieve credential
        retrieved_value = storage.retrieve_credential(credential, user_id)
        assert retrieved_value == value
        
    def test_retrieve_inactive_credential_error(self):
        """Test retrieving inactive credential raises error"""
        storage = CredentialStorage()
        
        credential = storage.store_credential("password", "secret123")
        credential.is_active = False
        
        with pytest.raises(CredentialError, match="Credential is not active"):
            storage.retrieve_credential(credential)
            
    def test_update_credential(self):
        """Test updating existing credential"""
        storage = CredentialStorage()
        
        # Store initial credential
        credential = storage.store_credential("password", "old_password")
        original_timestamp = credential.updated_at
        
        # Update credential
        new_value = "new_password"
        updated_credential = storage.update_credential(credential, new_value)
        
        assert updated_credential.updated_at != original_timestamp
        
        # Verify new value
        retrieved_value = storage.retrieve_credential(updated_credential)
        assert retrieved_value == new_value
        
    def test_deactivate_credential(self):
        """Test deactivating a credential"""
        storage = CredentialStorage()
        
        credential = storage.store_credential("password", "secret123")
        assert credential.is_active is True
        
        deactivated = storage.deactivate_credential(credential)
        assert deactivated.is_active is False
        
    def test_is_sensitive_field(self):
        """Test sensitive field detection"""
        storage = CredentialStorage()
        
        assert storage.is_sensitive_field("password") is True
        assert storage.is_sensitive_field("username") is True
        assert storage.is_sensitive_field("email") is True
        assert storage.is_sensitive_field("name") is False
        assert storage.is_sensitive_field("id") is False
        
    def test_encrypt_decrypt_user_data(self):
        """Test encrypting and decrypting user data"""
        storage = CredentialStorage()
        
        user_data = {
            "username": "testuser",
            "password": "secret123",
            "email": "test@example.com",
            "name": "Test User",
            "id": "user123"
        }
        
        # Encrypt user data
        encrypted_data = storage.encrypt_user_data(user_data, "user123")
        
        # Sensitive fields should be encrypted
        assert encrypted_data["username"] != user_data["username"]
        assert encrypted_data["password"] != user_data["password"]
        assert encrypted_data["email"] != user_data["email"]
        # Non-sensitive fields should remain unchanged
        assert encrypted_data["name"] == user_data["name"]
        assert encrypted_data["id"] == user_data["id"]
        
        # Decrypt user data
        decrypted_data = storage.decrypt_user_data(encrypted_data, "user123")
        
        # All fields should match original
        assert decrypted_data == user_data
        
    def test_validate_password_strength(self):
        """Test password strength validation"""
        storage = CredentialStorage()
        
        # Strong password
        strong_result = storage.validate_credential_strength("password", "SecurePass123!")
        assert strong_result['is_valid'] is True
        assert strong_result['score'] >= 50
        
        # Weak password
        weak_result = storage.validate_credential_strength("password", "123")
        assert weak_result['is_valid'] is False
        assert len(weak_result['issues']) > 0
        
    def test_validate_username_strength(self):
        """Test username strength validation"""
        storage = CredentialStorage()
        
        # Valid username
        valid_result = storage.validate_credential_strength("username", "testuser123")
        assert valid_result['is_valid'] is True
        
        # Invalid username
        invalid_result = storage.validate_credential_strength("username", "te")
        assert invalid_result['is_valid'] is False
        
    def test_validate_email_format(self):
        """Test email format validation"""
        storage = CredentialStorage()
        
        # Valid email
        valid_result = storage.validate_credential_strength("email", "test@example.com")
        assert valid_result['is_valid'] is True
        
        # Invalid email
        invalid_result = storage.validate_credential_strength("email", "invalid-email")
        assert invalid_result['is_valid'] is False
        
    def test_health_check_healthy(self):
        """Test health check for healthy storage"""
        storage = CredentialStorage()
        
        health = storage.health_check()
        assert health['status'] == 'healthy'
        assert 'encryption_service' in health
        
    def test_convenience_functions(self):
        """Test convenience functions"""
        field_name = "password"
        value = "secret123"
        user_id = "user123"
        
        # Store credential
        credential = store_secure_credential(field_name, value, user_id)
        assert isinstance(credential, EncryptedCredential)
        
        # Retrieve credential
        retrieved_value = retrieve_secure_credential(credential, user_id)
        assert retrieved_value == value


class TestKeyManager:
    """Test key management functionality"""
    
    def setup_method(self):
        """Setup test environment"""
        self.temp_dir = tempfile.mkdtemp()
        # Reset global instances
        import src.security.key_management as key_module
        key_module._key_managers = {}
        
    def teardown_method(self):
        """Clean up test environment"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        import src.security.key_management as key_module
        key_module._key_managers = {}
        
    def test_key_metadata_model(self):
        """Test KeyMetadata model validation"""
        metadata = KeyMetadata(
            key_id="test-key-123",
            key_type=KeyType.MASTER,
            environment=Environment.DEVELOPMENT,
            created_at="2025-01-01T00:00:00"
        )
        
        assert metadata.key_id == "test-key-123"
        assert metadata.key_type == KeyType.MASTER
        assert metadata.environment == Environment.DEVELOPMENT
        assert metadata.is_active is True
        
    def test_key_manager_initialization_development(self):
        """Test key manager initialization for development"""
        with patch.object(KeyManager, '_get_metadata_file_path', return_value=os.path.join(self.temp_dir, 'metadata.json')):
            manager = KeyManager(Environment.DEVELOPMENT)
            assert manager.environment == Environment.DEVELOPMENT
            assert manager.kms_client is None
            
    def test_create_master_key_development(self):
        """Test creating master key in development"""
        with patch.object(KeyManager, '_get_metadata_file_path', return_value=os.path.join(self.temp_dir, 'metadata.json')):
            manager = KeyManager(Environment.DEVELOPMENT)
            
            description = "Test master key"
            metadata = manager.create_master_key(description)
            
            assert metadata.key_type == KeyType.MASTER
            assert metadata.environment == Environment.DEVELOPMENT
            assert metadata.description == description
            assert metadata.is_active is True
            
    def test_get_current_master_key(self):
        """Test getting current master key"""
        with patch.object(KeyManager, '_get_metadata_file_path', return_value=os.path.join(self.temp_dir, 'metadata.json')):
            manager = KeyManager(Environment.DEVELOPMENT)
            
            # No master key initially
            assert manager.get_current_master_key() is None
            
            # Create master key
            metadata = manager.create_master_key("Test key")
            
            # Should now return the master key
            current_key = manager.get_current_master_key()
            assert current_key is not None
            assert current_key.key_id == metadata.key_id
            
    def test_list_keys_with_filters(self):
        """Test listing keys with filters"""
        with patch.object(KeyManager, '_get_metadata_file_path', return_value=os.path.join(self.temp_dir, 'metadata.json')):
            manager = KeyManager(Environment.DEVELOPMENT)
            
            # Create multiple keys
            master_key = manager.create_master_key("Master key")
            
            # Test listing all keys
            all_keys = manager.list_keys()
            assert len(all_keys) == 1
            assert all_keys[0].key_id == master_key.key_id
            
            # Test filtering by key type
            master_keys = manager.list_keys(KeyType.MASTER)
            assert len(master_keys) == 1
            assert master_keys[0].key_type == KeyType.MASTER
            
            # Test filtering by active status
            master_key.is_active = False
            manager.key_metadata_cache[master_key.key_id] = master_key
            
            active_keys = manager.list_keys(active_only=True)
            assert len(active_keys) == 0
            
            inactive_keys = manager.list_keys(active_only=False)
            assert len(inactive_keys) == 1
            
    def test_key_rotation(self):
        """Test key rotation functionality"""
        with patch.object(KeyManager, '_get_metadata_file_path', return_value=os.path.join(self.temp_dir, 'metadata.json')):
            manager = KeyManager(Environment.DEVELOPMENT)
            
            # Create initial key
            original_key = manager.create_master_key("Original key")
            original_key_id = original_key.key_id
            
            # Rotate key
            new_key = manager.rotate_key(original_key_id, create_backup=True)
            
            # Original key should be deactivated
            original_metadata = manager.get_key_metadata(original_key_id)
            assert original_metadata.is_active is False
            assert original_metadata.last_rotated is not None
            
            # New key should be active
            assert new_key.is_active is True
            assert new_key.key_id != original_key_id
            
            # Backup should be created
            backup_keys = manager.list_keys(KeyType.BACKUP, active_only=False)
            assert len(backup_keys) > 0
            
    def test_rotation_scheduling(self):
        """Test key rotation scheduling"""
        with patch.object(KeyManager, '_get_metadata_file_path', return_value=os.path.join(self.temp_dir, 'metadata.json')):
            manager = KeyManager(Environment.DEVELOPMENT)
            
            # Create key
            key = manager.create_master_key("Test key")
            
            # Schedule rotation
            manager.schedule_key_rotation(key.key_id, "30d")
            
            # Verify schedule
            updated_key = manager.get_key_metadata(key.key_id)
            assert updated_key.rotation_schedule == "30d"
            
    def test_check_rotation_due(self):
        """Test checking for keys due for rotation"""
        with patch.object(KeyManager, '_get_metadata_file_path', return_value=os.path.join(self.temp_dir, 'metadata.json')):
            manager = KeyManager(Environment.DEVELOPMENT)
            
            # Create key with past creation date
            key = manager.create_master_key("Old key")
            past_date = (datetime.utcnow() - timedelta(days=40)).isoformat()
            key.created_at = past_date
            key.rotation_schedule = "30d"
            manager.key_metadata_cache[key.key_id] = key
            
            # Check rotation due
            due_keys = manager.check_rotation_due()
            assert len(due_keys) == 1
            assert due_keys[0].key_id == key.key_id
            
    def test_get_environment_config(self):
        """Test getting environment configuration"""
        with patch.object(KeyManager, '_get_metadata_file_path', return_value=os.path.join(self.temp_dir, 'metadata.json')):
            manager = KeyManager(Environment.DEVELOPMENT)
            
            config = manager.get_environment_config()
            assert config['environment'] == 'development'
            assert config['key_count'] == 0
            assert config['active_keys'] == 0
            assert config['master_key'] is None
            assert config['encryption_available'] is True
            assert config['kms_enabled'] is False
            
    def test_health_check_healthy(self):
        """Test health check for healthy key manager"""
        with patch.object(KeyManager, '_get_metadata_file_path', return_value=os.path.join(self.temp_dir, 'metadata.json')):
            manager = KeyManager(Environment.DEVELOPMENT)
            
            # Create master key
            manager.create_master_key("Test key")
            
            health = manager.health_check()
            assert health['status'] == 'healthy'
            assert health['environment'] == 'development'
            assert health['total_keys'] == 1
            assert health['active_keys'] == 1
            
    def test_health_check_unhealthy_no_master_key(self):
        """Test health check when no master key exists"""
        with patch.object(KeyManager, '_get_metadata_file_path', return_value=os.path.join(self.temp_dir, 'metadata.json')):
            manager = KeyManager(Environment.DEVELOPMENT)
            
            health = manager.health_check()
            assert health['status'] == 'unhealthy'
            assert 'No active master key found' in health['error']
            
    def test_convenience_functions(self):
        """Test convenience functions"""
        with patch.object(KeyManager, '_get_metadata_file_path', return_value=os.path.join(self.temp_dir, 'metadata.json')):
            # Test get_key_manager
            manager = get_key_manager(Environment.DEVELOPMENT)
            assert isinstance(manager, KeyManager)
            assert manager.environment == Environment.DEVELOPMENT
            
            # Test initialize_encryption_keys
            master_key = initialize_encryption_keys(Environment.DEVELOPMENT)
            assert isinstance(master_key, KeyMetadata)
            assert master_key.key_type == KeyType.MASTER
            
            # Test get_current_encryption_key
            key_id = get_current_encryption_key(Environment.DEVELOPMENT)
            assert key_id == master_key.key_id
            
    def test_key_manager_singleton(self):
        """Test that key manager returns singleton per environment"""
        with patch.object(KeyManager, '_get_metadata_file_path', return_value=os.path.join(self.temp_dir, 'metadata.json')):
            manager1 = get_key_manager(Environment.DEVELOPMENT)
            manager2 = get_key_manager(Environment.DEVELOPMENT)
            assert manager1 is manager2
            
            # Different environments should have different instances
            with patch.object(KeyManager, '_get_metadata_file_path', return_value=os.path.join(self.temp_dir, 'metadata_staging.json')):
                manager3 = get_key_manager(Environment.STAGING)
                assert manager3 is not manager1


class TestIntegrationScenarios:
    """Test integration scenarios across all security components"""
    
    def setup_method(self):
        """Setup test environment"""
        self.temp_dir = tempfile.mkdtemp()
        os.environ['TENNIS_ENVIRONMENT'] = 'development'
        
        # Reset global instances
        import src.security.encryption as enc_module
        import src.security.credential_storage as cred_module
        import src.security.key_management as key_module
        
        enc_module._encryption_service = None
        cred_module._credential_storage = None
        key_module._key_managers = {}
        
    def teardown_method(self):
        """Clean up test environment"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        
    def test_full_encryption_workflow(self):
        """Test complete encryption workflow"""
        # Initialize key management
        with patch.object(KeyManager, '_get_metadata_file_path', return_value=os.path.join(self.temp_dir, 'metadata.json')):
            master_key = initialize_encryption_keys(Environment.DEVELOPMENT)
            assert master_key is not None
            
            # Get encryption service
            encryption_service = get_encryption_service()
            assert encryption_service is not None
            
            # Test encryption/decryption
            test_data = "sensitive_user_password"
            encrypted = encryption_service.encrypt(test_data)
            decrypted = encryption_service.decrypt(encrypted)
            assert decrypted == test_data
            
            # Test credential storage
            credential_storage = get_credential_storage()
            credential = credential_storage.store_credential("password", test_data, "user123")
            retrieved = credential_storage.retrieve_credential(credential, "user123")
            assert retrieved == test_data
            
    def test_user_data_encryption_workflow(self):
        """Test complete user data encryption workflow"""
        with patch.object(KeyManager, '_get_metadata_file_path', return_value=os.path.join(self.temp_dir, 'metadata.json')):
            # Initialize encryption
            initialize_encryption_keys(Environment.DEVELOPMENT)
            
            # Test user data encryption
            user_data = {
                "user_id": "user123",
                "username": "testuser",
                "password": "SecurePass123!",
                "email": "test@example.com",
                "first_name": "Test",
                "last_name": "User"
            }
            
            credential_storage = get_credential_storage()
            
            # Encrypt sensitive data
            encrypted_data = credential_storage.encrypt_user_data(user_data, "user123")
            
            # Verify encryption
            assert encrypted_data["username"] != user_data["username"]
            assert encrypted_data["password"] != user_data["password"]
            assert encrypted_data["email"] != user_data["email"]
            assert encrypted_data["first_name"] == user_data["first_name"]  # Not sensitive
            
            # Decrypt data
            decrypted_data = credential_storage.decrypt_user_data(encrypted_data, "user123")
            
            # Verify decryption
            assert decrypted_data == user_data
            
    def test_key_rotation_with_active_credentials(self):
        """Test key rotation with active credentials"""
        with patch.object(KeyManager, '_get_metadata_file_path', return_value=os.path.join(self.temp_dir, 'metadata.json')):
            # Initialize and create credentials
            key_manager = get_key_manager(Environment.DEVELOPMENT)
            original_key = key_manager.create_master_key("Original key")
            
            credential_storage = get_credential_storage()
            test_credential = credential_storage.store_credential("password", "secret123", "user123")
            
            # Verify credential works
            retrieved = credential_storage.retrieve_credential(test_credential, "user123")
            assert retrieved == "secret123"
            
            # Rotate key
            new_key = key_manager.rotate_key(original_key.key_id)
            
            # Verify credential still works (should use cached encryption service)
            retrieved_after_rotation = credential_storage.retrieve_credential(test_credential, "user123")
            assert retrieved_after_rotation == "secret123"
            
    def test_health_checks_across_components(self):
        """Test health checks across all security components"""
        with patch.object(KeyManager, '_get_metadata_file_path', return_value=os.path.join(self.temp_dir, 'metadata.json')):
            # Initialize all components
            initialize_encryption_keys(Environment.DEVELOPMENT)
            
            # Check encryption service health
            encryption_service = get_encryption_service()
            enc_health = encryption_service.health_check()
            assert enc_health['status'] == 'healthy'
            
            # Check credential storage health
            credential_storage = get_credential_storage()
            cred_health = credential_storage.health_check()
            assert cred_health['status'] == 'healthy'
            
            # Check key manager health
            key_manager = get_key_manager(Environment.DEVELOPMENT)
            key_health = key_manager.health_check()
            assert key_health['status'] == 'healthy'


if __name__ == "__main__":
    pytest.main([__file__, "-v"])