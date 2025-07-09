# Tennis Booking Automation - Migration to DynamoDB Configuration

## Project Overview
Migrate from hardcoded .env configuration to a dynamic DynamoDB-based system that allows users to configure tennis court bookings through a web interface.

## Current State Analysis
- **Current Script**: Python Selenium automation for tennis court booking
- **Configuration**: Static .env file with hardcoded values
- **Issues**: Manual editing required, no encryption, limited flexibility

## Target Architecture
```
Frontend (React/HTML) → API Gateway → Lambda Functions → DynamoDB → Tennis Booking Script
```

## High-Level Blueprint

### Phase 1: Foundation & Data Layer
1. **DynamoDB Schema Design & Setup**
   - Design table schemas for UserConfigs, BookingRequests, SystemConfig
   - Create CloudFormation/CDK templates
   - Set up local DynamoDB for development

2. **Core Data Models & Encryption**
   - Implement data access layer with boto3
   - Add encryption/decryption utilities using AWS KMS
   - Create validation schemas for configuration data

### Phase 2: Backend Services
3. **Configuration Management Service**
   - Lambda functions for CRUD operations on configurations
   - API Gateway endpoints for configuration management
   - Input validation and error handling

4. **Booking Service Integration**
   - Modify existing tennis.py to use DynamoDB instead of .env
   - Create booking request processor
   - Add comprehensive logging and error handling

### Phase 3: Frontend Interface
5. **Web Interface Development**
   - Create configuration form for booking parameters
   - Implement user authentication/session management
   - Add booking history and status tracking

6. **Integration & Testing**
   - End-to-end testing of complete flow
   - Error handling and edge case validation
   - Performance optimization

### Phase 4: Deployment & Operations
7. **Infrastructure as Code**
   - Complete CloudFormation/CDK templates
   - CI/CD pipeline setup
   - Monitoring and alerting configuration

## Detailed Step Breakdown

### Phase 1: Foundation & Data Layer

#### Step 1.1: DynamoDB Local Setup & Schema Creation
- Install and configure DynamoDB Local
- Create table definitions with proper indexes
- Write basic CRUD operations for each table
- Unit tests for data operations

#### Step 1.2: Data Models & Validation
- Create Pydantic models for data validation
- Implement data access layer (DAO pattern)
- Add input sanitization and validation
- Unit tests for models and validation

#### Step 1.3: Encryption Layer
- Implement KMS-based encryption/decryption
- Create secure credential storage utilities
- Add environment-specific key management
- Unit tests for encryption operations

### Phase 2: Backend Services

#### Step 2.1: Configuration API Foundation
- Create FastAPI local development server
- Build basic booking API with validation against court-specific availability rules
- Add authentication middleware and JWT handling
- Integration tests with FastAPI test client
- Prepare Lambda deployment structure

#### Step 2.2: User Management Service
- Simple JWT-based authentication (1-day token expiration)
- Direct tennis site credential validation + encrypted DynamoDB storage
- Session management with JWT tokens
- User-specific configuration isolation
- Password validation and security checks
- Tests for authentication flow

**API Endpoints:**
- POST /auth/login          # JWT authentication against tennis site
- GET /users/me             # Current user profile
- PUT /users/me/config      # Update user config
- GET /bookings             # User's booking history
- POST /bookings            # Create new booking request (court, date, time)
- GET /bookings/{id}        # Get booking status
- REST API error response format

#### Step 2.3: Booking Request Service
- Create booking request creation/management (court, date, time)
- Add booking status tracking and workflow logic
- Implement court-specific availability windows (Court 1: 10 days, Court 2: 9 days)
- Smart validation: Check if date falls within court's booking window (relative to today)
- No retry mechanism - inform user if date not yet available
- Midnight booking scheduler and court availability updater
- Rolling window logic (removes past date, opens new date at midnight)
- User-friendly messaging: "Court 1 bookings for July 18th aren't open yet. Don't worry — we've scheduled your request and will confirm once it's successfully reserved after midnight on July 9th."
- Tests for court-specific booking logic and scheduling

#### Step 2.4: Tennis Script Integration
- Modify tennis.py to fetch configuration directly from DynamoDB
- Remove all .env file dependencies
- Implement Lambda function wrapper for tennis.py
- Add comprehensive error handling and retry logic
- Tests for DynamoDB configuration loading

### Phase 3: Frontend Interface

#### Step 3.1: Basic Configuration Form
- Create HTML form for booking parameters
- Add client-side validation
- Implement form submission to API
- Tests for form validation

#### Step 3.2: User Interface Enhancement
- Add user authentication UI
- Create booking history display
- Implement status tracking interface
- Tests for UI components

#### Step 3.3: Real-time Updates
- Add WebSocket support for booking status
- Implement real-time status updates
- Add notification system
- Tests for real-time features

### Phase 4: Integration & Deployment

#### Step 4.1: End-to-End Testing
- Create comprehensive test suite
- Add performance testing
- Implement error scenario testing
- Load testing for concurrent users

#### Step 4.2: Infrastructure as Code
- Create complete CloudFormation templates
- Add deployment scripts
- Implement environment management
- Tests for infrastructure deployment

#### Step 4.3: Monitoring & Operations
- Add CloudWatch logging and metrics
- Create alerting rules
- Implement health checks
- Operational runbooks

## Implementation Strategy

### Iterative Development Approach
1. **Start Small**: Begin with core data layer and basic CRUD operations
2. **Build Incrementally**: Each step builds on previous functionality
3. **Test Early**: Unit tests for each component before integration
4. **Validate Often**: Integration tests after each phase
5. **Deploy Frequently**: Continuous deployment of working features

### Testing Strategy
- **Unit Tests**: Individual functions and components
- **Integration Tests**: API endpoints with FastAPI test client
- **End-to-End Tests**: Complete user workflows
- **Performance Tests**: Load and stress testing
- **Security Tests**: Encryption and access control
- **Local Development Tests**: FastAPI server testing before Lambda deployment

### Risk Mitigation
- **Backward Compatibility**: Maintain .env fallback during migration
- **Rollback Plan**: Ability to revert to previous configuration
- **Data Backup**: Regular backups of DynamoDB data
- **Monitoring**: Comprehensive logging and alerting
- **Court Availability Monitoring**: Background job to detect changes in court availability windows
- **Configuration Flexibility**: Court-specific settings in SystemConfig table

## Success Criteria
- [ ] Users can configure bookings through web interface
- [ ] Sensitive data is encrypted at rest
- [ ] System handles multiple concurrent users
- [ ] Booking success rate matches or exceeds current system
- [ ] Complete audit trail of all bookings
- [ ] Zero-downtime deployment capability

## Next Steps
1. Review and approve this plan
2. Set up development environment
3. Begin Phase 1: Foundation & Data Layer
4. Implement iterative development cycle