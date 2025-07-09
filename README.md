# Tennis Booking Automation System

A comprehensive tennis court booking automation system transitioning from static .env configuration to a dynamic, secure, cloud-based architecture with web interface and encrypted data storage.

## 🎯 Project Overview

This project is migrating a simple tennis court booking script to a full-featured web application with:
- **Secure user management** with encrypted credentials
- **Web-based configuration interface** instead of manual .env editing  
- **DynamoDB-backed storage** with real-time booking management
- **AWS cloud architecture** with proper security and monitoring
- **Multi-user support** with isolated configurations

## 🏗️ Architecture

```
Frontend (React/HTML) → API Gateway → Lambda Functions → DynamoDB → Tennis Booking Script
                                                      ↓
                                              Encryption Layer (AWS KMS)
```

## 📋 Current Status: Phase 1 Complete ✅

### ✅ **What We Have Built (Phase 1: Foundation & Data Layer)**

#### 1. **Database Layer** (`src/database/`)
- **DynamoDB Local Setup**: Complete local development environment
- **Table Schemas**: UserConfigs, BookingRequests, SystemConfig tables
- **CRUD Operations**: Comprehensive database operations with error handling
- **Connection Management**: Robust connection handling and configuration

#### 2. **Data Models** (`src/models/`)
- **Pydantic Models**: Fully validated data models for all entities
- **Custom Validators**: Date, time, court, credential validation
- **Business Logic**: User preferences, booking constraints, system configuration
- **Type Safety**: Complete type checking and validation

#### 3. **Security Layer** (`src/security/`) 🔐
- **Encryption Service**: AWS KMS + envelope encryption for production, secure local encryption for development
- **Credential Storage**: Field-level encryption with password strength validation
- **Key Management**: Environment-specific keys with automated rotation support
- **Enhanced Data Models**: Transparent encryption/decryption integration

#### 4. **Data Access Layer** (`src/dao/`)
- **DAO Pattern**: Clean separation between business logic and database operations
- **Encrypted Operations**: Secure CRUD operations with automatic encryption/decryption
- **Advanced Queries**: Username/email lookup, user authentication, security analysis
- **Error Handling**: Comprehensive error management with proper logging

#### 5. **Testing Framework** (`tests/`)
- **Unit Tests**: 79+ test methods covering all components
- **Integration Tests**: End-to-end workflow validation
- **Security Tests**: Encryption, key management, credential validation
- **Test Data Factories**: Realistic test data generation

#### 6. **Original Tennis Script** (`tennis.py`)
- **Selenium Automation**: Automated court booking with Chrome WebDriver
- **Environment Configuration**: Configurable via .env variables
- **Error Handling**: Comprehensive logging and screenshot capture
- **Dockerized**: Ready for containerized deployment

## 🚀 Getting Started

### Prerequisites
- **Python 3.10+**
- **Docker** (for DynamoDB Local)
- **AWS CLI** (for production deployment)
- **Git**

### 1. **Environment Setup**

```bash
# Clone the repository
git clone <repository-url>
cd tennisCourtReservation

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment configuration
cp .env.example .env
# Edit .env with your tennis website credentials
```

### 2. **Database Setup**

```bash
# Start DynamoDB Local with Docker
docker-compose up -d

# Set up database tables and test data
python src/setup_database.py

# Verify database setup
python -c "
from src.database.connection import get_dynamodb_resource
dynamodb = get_dynamodb_resource()
print('Tables:', list(dynamodb.tables.all()))
"
```

### 3. **Security Setup**

```bash
# Initialize encryption keys for development
python -c "
from src.security import initialize_encryption_keys, Environment
key = initialize_encryption_keys(Environment.DEVELOPMENT)
print(f'Encryption key initialized: {key.key_id}')
"

# Test encryption service
python -c "
from src.security import get_encryption_service
service = get_encryption_service()
health = service.health_check()
print(f'Encryption status: {health[\"status\"]}')
"
```

## 🧪 Testing

### Run All Tests
```bash
# Run complete test suite
python -m pytest -v

# Run with coverage
python -m pytest --cov=src --cov-report=html

# Run specific test categories
python -m pytest tests/test_database_operations.py -v    # Database tests
python -m pytest tests/test_models_validation.py -v     # Model validation tests  
python -m pytest tests/test_encryption.py -v            # Security tests
```

### Test Database Operations
```bash
# Test basic database connectivity
python -c "
from src.dao import UserConfigDAO
from src.models import UserConfig
dao = UserConfigDAO()
print('Database connection: OK')
"

# Test encrypted user operations
python -c "
from src.dao import EncryptedUserConfigDAO
from src.models import EncryptedUserConfig
dao = EncryptedUserConfigDAO()
health = dao.get_encryption_health_check()
print(f'Encryption health: {health[\"status\"]}')
"
```

### Test Tennis Script (Original Functionality)
```bash
# Test the original tennis booking script
# Make sure to configure .env with valid credentials first
python tennis.py
```

## 🔧 Usage Examples

### 1. **Basic User Management with Encryption**

```python
from src.dao import EncryptedUserConfigDAO
from src.models import EncryptedUserConfig

# Create DAO
dao = EncryptedUserConfigDAO()

# Create user with automatic encryption
user = EncryptedUserConfig(
    user_id="user123",
    username="john_doe",
    password="SecurePass123!",
    email="john@example.com",
    first_name="John",
    last_name="Doe",
    preferred_courts=[1, 2],
    preferred_times=["De 08:00 AM a 09:00 AM"]
)

# Save user (automatic encryption)
created_user = dao.create_user(user)

# Retrieve user (automatic decryption)
retrieved_user = dao.get_user("user123")

# Authenticate user
authenticated = dao.authenticate_user("john_doe", "SecurePass123!")
```

### 2. **Security Analysis**

```python
# Get security summary for a user
security_summary = dao.get_user_security_summary("user123")
print(f"Weak credentials: {security_summary['has_weak_credentials']}")
print(f"Recommendations: {security_summary['recommendations']}")

# Find users with weak credentials
weak_users = dao.get_users_with_weak_credentials()
print(f"Users needing security updates: {len(weak_users)}")

# Get encryption status
from src.security import get_encryption_service
service = get_encryption_service()
health = service.health_check()
print(f"Encryption service: {health['status']}")
```

### 3. **Database Operations**

```python
from src.dao import UserConfigDAO, BookingRequestDAO, SystemConfigDAO
from src.models import BookingRequest, SystemConfig

# Work with booking requests
booking_dao = BookingRequestDAO()
booking = BookingRequest(
    request_id="req123",
    user_id="user123", 
    court_id=1,
    booking_date="2025-03-29",
    time_slot="De 08:00 AM a 09:00 AM"
)
booking_dao.create_booking_request(booking)

# System configuration
config_dao = SystemConfigDAO()
config = config_dao.get_config("booking_window_days")
print(f"Booking window: {config.config_value} days")
```

## 📁 Project Structure

```
tennis-booking-automation/
├── 📁 src/                          # Main source code
│   ├── 📁 database/                 # Database connection and operations
│   │   ├── connection.py            # DynamoDB connection management
│   │   ├── schemas.py               # Table schema definitions
│   │   └── operations.py            # Low-level database operations
│   ├── 📁 models/                   # Pydantic data models
│   │   ├── user_config.py           # User configuration model
│   │   ├── encrypted_user_config.py # Encrypted user model
│   │   ├── booking_request.py       # Booking request model
│   │   ├── system_config.py         # System configuration model
│   │   └── validators.py            # Custom validation logic
│   ├── 📁 dao/                      # Data Access Objects
│   │   ├── base.py                  # Base DAO with common operations
│   │   ├── user_config_dao.py       # User operations
│   │   ├── encrypted_user_config_dao.py # Secure user operations
│   │   ├── booking_request_dao.py   # Booking operations
│   │   └── system_config_dao.py     # System config operations
│   ├── 📁 security/                 # Encryption and security 🔐
│   │   ├── encryption.py            # Core encryption service
│   │   ├── credential_storage.py    # Secure credential management
│   │   └── key_management.py        # Key lifecycle management
│   ├── 📁 factories/                # Test data factories
│   └── setup_database.py            # Database initialization script
├── 📁 tests/                        # Comprehensive test suite
│   ├── test_database_operations.py  # Database tests (25 tests)
│   ├── test_models_validation.py    # Model validation tests (36 tests)
│   └── test_encryption.py           # Security tests (43 tests)
├── 📁 screenshots/                  # Tennis script screenshots
├── 📄 tennis.py                     # Original tennis booking script
├── 📄 docker-compose.yml            # DynamoDB Local setup
├── 📄 Dockerfile                    # Container configuration
├── 📄 requirements.txt              # Python dependencies
├── 📄 .env.example                  # Environment template
├── 📄 claude.md                     # Project guidelines
├── 📄 plan.md                       # Architecture overview
├── 📄 STEP_1_1_SUMMARY.md          # Step 1.1 implementation summary
├── 📄 STEP_1_2_SUMMARY.md          # Step 1.2 implementation summary
└── 📄 STEP_1_3_SUMMARY.md          # Step 1.3 implementation summary
```

## 🔒 Security Features

### **Encryption at Rest**
- **AES-256 encryption** for all sensitive user data
- **AWS KMS integration** for production key management
- **Envelope encryption** for performance optimization
- **Environment isolation** with separate keys per environment

### **Credential Security**
- **Password strength validation** with scoring system
- **Secure password storage** with proper encryption
- **Credential audit trails** with comprehensive logging
- **Automatic weak credential detection**

### **Key Management**
- **Automated key rotation** with configurable schedules
- **Key backup and recovery** for business continuity
- **Environment-specific keys** for security isolation
- **Health monitoring** for key availability

## 🚦 Current Limitations & What's Missing

### **❌ Not Yet Implemented (Phases 2-4)**

#### **Phase 2: Backend Services** 
- **🔧 API Gateway & Lambda Functions**: REST endpoints for configuration management
- **🔧 User Authentication Service**: JWT-based auth with session management
- **🔧 Booking Request Service**: Real-time booking management and status tracking
- **🔧 Tennis Script Integration**: DynamoDB configuration loading in existing script

#### **Phase 3: Frontend Interface**
- **🔧 Web Configuration Form**: User-friendly interface for booking parameters
- **🔧 User Dashboard**: Booking history, status tracking, profile management
- **🔧 Real-time Updates**: WebSocket integration for live booking status
- **🔧 Mobile-Responsive Design**: Cross-device compatibility

#### **Phase 4: Integration & Deployment**
- **🔧 End-to-End Testing**: Complete workflow automation testing
- **🔧 Infrastructure as Code**: CloudFormation/CDK templates for AWS deployment
- **🔧 Monitoring & Operations**: CloudWatch metrics, alerting, and operational runbooks
- **🔧 CI/CD Pipeline**: Automated testing and deployment

### **🔧 Technical Debt & Improvements Needed**

#### **Database Optimizations**
- **Global Secondary Indexes (GSI)**: For efficient username/email lookups
- **Pagination**: For large result sets in user listing operations
- **Caching Layer**: Redis/ElastiCache for frequently accessed data
- **Connection Pooling**: More efficient database connection management

#### **Security Enhancements**
- **Rate Limiting**: API endpoint protection against abuse
- **Input Sanitization**: Additional XSS and injection protection
- **Audit Logging**: Enhanced security event logging and monitoring
- **Multi-Factor Authentication**: Additional security layer for user accounts

#### **Performance & Scalability**
- **Async Operations**: Non-blocking I/O for better concurrency
- **Background Jobs**: Queue-based processing for long-running tasks
- **Load Balancing**: Multi-instance deployment support
- **Database Sharding**: Horizontal scaling for large user bases

#### **Operational Readiness**
- **Health Checks**: Comprehensive application health monitoring
- **Metrics Collection**: Performance and usage analytics
- **Error Tracking**: Centralized error reporting and alerting
- **Backup & Recovery**: Automated data backup and disaster recovery

## 🎯 Next Steps

### **Immediate Priorities (Phase 2)**
1. **Configure AWS Environment**: Set up KMS keys, IAM roles, and Lambda functions
2. **Implement Configuration API**: REST endpoints for user and system configuration
3. **Add User Authentication**: JWT-based authentication service
4. **Integrate with Tennis Script**: Modify existing script to use DynamoDB

### **Development Guidelines**
- **Follow TDD**: Write tests before implementation
- **Security First**: All sensitive data must be encrypted
- **Documentation**: Update summaries after each step
- **Integration Testing**: Verify all components work together
- **Performance Testing**: Validate response times and scalability

## 🤝 Contributing

### **Development Workflow**
1. **Check Current Status**: Review `todo.md` for current phase and next steps
2. **Follow Implementation Prompts**: Use detailed prompts in `implementation-prompts.md`
3. **Write Tests First**: Implement comprehensive test coverage
4. **Update Documentation**: Create step summaries and update README
5. **Verify Integration**: Ensure new components work with existing system

### **Code Standards**
- **Type Hints**: All functions must have proper type annotations
- **Error Handling**: Comprehensive exception handling with logging
- **Security**: All sensitive data must be encrypted
- **Testing**: Minimum 90% test coverage for new code
- **Documentation**: Clear docstrings and implementation summaries

## 📞 Support

- **Check Logs**: Review `tennis_automation.log` for operation details
- **Run Health Checks**: Use built-in health check methods for component status
- **Test Database**: Verify DynamoDB Local connectivity and table setup
- **Validate Security**: Check encryption service health and key availability

## 🔄 Migration Path

### **From Current .env to Full System**
1. **Phase 1**: ✅ **Complete** - Secure foundation with encrypted storage
2. **Phase 2**: **In Progress** - Backend API services for configuration management
3. **Phase 3**: **Planned** - Web interface replacing manual .env editing
4. **Phase 4**: **Planned** - Production deployment with full monitoring

The system maintains **backward compatibility** with the original `tennis.py` script while building toward the full web-based solution.

---

**📊 Current Statistics:**
- **Lines of Code**: ~2,500+ (excluding tests)
- **Test Coverage**: 104+ test methods across all components
- **Security**: AES-256 encryption with comprehensive key management
- **Architecture**: Production-ready foundation with AWS integration
- **Documentation**: Complete implementation summaries and usage guides