# Tennis Booking Automation - Implementation Prompts

## Step 1.1: DynamoDB Local Setup & Schema Creation

### Context
This is the first step in migrating a tennis court booking automation system from .env configuration to DynamoDB. We need to establish the data foundation with proper schema design and local development setup.

### Prompt 1.1
```
I need to set up DynamoDB Local and create the initial table schemas for a tennis booking configuration system. The system will store user configurations, booking requests, and system settings.

Requirements:
1. Install and configure DynamoDB Local for development
2. Create table definitions for three tables:
   - UserConfigs: Store user credentials and preferences
   - BookingRequests: Store individual booking requests with TTL
   - SystemConfig: Store application settings and court configurations

3. Implement basic CRUD operations using boto3
4. Add comprehensive unit tests for all data operations
5. Create a simple script to populate test data

Table Schema Requirements:
- UserConfigs: userId (PK), username, password, preferredCourt, timestamps
- BookingRequests: requestId (PK), userId (SK), courtId, date, timeSlot, status, TTL
- SystemConfig: configKey (PK), configValue, description, lastModified

Create a clean, testable foundation that follows DynamoDB best practices. Include proper error handling and logging.

**State Tracking Requirements:**
After completing this step, update todo.md to:
1. Mark "Step 1.1: DynamoDB Local Setup & Schema Creation" as completed ✅
2. Update "Current Status" to "Phase 1: Step 1.1 Complete - DynamoDB foundation ready"
3. Mark "Step 1.2: Data Models & Validation Layer" as the next step 🔄
4. Add any implementation notes or discoveries to the Notes section
5. Update "Next Action" to "Execute Step 1.2 prompt for data models and validation"
```

---

## Step 1.2: Data Models & Validation Layer

### Context
Building on the DynamoDB foundation, we need robust data models and validation to ensure data integrity and type safety.

### Prompt 1.2
```
Building on the DynamoDB setup from Step 1.1, I need to create a comprehensive data validation layer using Pydantic models.

Requirements:
1. Create Pydantic models for all DynamoDB entities:
   - UserConfig model with field validation
   - BookingRequest model with business logic validation
   - SystemConfig model with type-safe configuration values

2. Implement a Data Access Object (DAO) pattern for database operations
3. Add input sanitization and validation for all user inputs
4. Create custom validators for:
   - Date formats (YYYY-MM-DD)
   - Time slot formats ("De HH:MM AM/PM a HH:MM AM/PM")
   - Court ID validation (5, 7, 17, etc.)
   - Username/password strength requirements

5. Add comprehensive unit tests for all models and validation logic
6. Create factory methods for test data generation

The validation layer should prevent invalid data from reaching the database and provide clear error messages for debugging.

**State Tracking Requirements:**
After completing this step, update todo.md to:
1. Mark "Step 1.2: Data Models & Validation Layer" as completed ✅
2. Update "Current Status" to "Phase 1: Step 1.2 Complete - Data validation layer ready"
3. Mark "Step 1.3: Encryption Utilities" as the next step 🔄
4. Add any implementation notes or discoveries to the Notes section
5. Update "Next Action" to "Execute Step 1.3 prompt for encryption utilities"
```

---

## Step 1.3: Encryption Utilities

### Context
User credentials must be encrypted at rest. We need a secure encryption layer using AWS KMS that integrates with our data models.

### Prompt 1.3
```
I need to implement secure encryption for sensitive data in the tennis booking system, building on the data models from Step 1.2.

Requirements:
1. Create an encryption utility class using AWS KMS
2. Implement encrypt/decrypt methods for sensitive fields
3. Add envelope encryption for performance (encrypt data keys with KMS)
4. Integrate encryption with the UserConfig model for password fields
5. Create environment-specific key management (dev/prod keys)

6. Add comprehensive unit tests for encryption operations
7. Create utility functions for key rotation
8. Add proper error handling for encryption failures
9. Implement secure key derivation for local development

Security Requirements:
- Never store encryption keys in code
- Use different keys for different environments
- Implement proper key rotation capabilities
- Add audit logging for encryption operations

The encryption should be transparent to the application layer - encrypted automatically on write, decrypted on read.

**State Tracking Requirements:**
After completing this step, update todo.md to:
1. Mark "Step 1.3: Encryption Utilities" as completed ✅
2. Update "Current Status" to "Phase 1: Complete - Foundation layer ready. Starting Phase 2: Backend Services"
3. Mark "Step 2.1: Configuration API Foundation" as the next step 🔄
4. Add any implementation notes or discoveries to the Notes section
5. Update "Next Action" to "Execute Step 2.1 prompt for configuration API foundation"
```

---

## Step 2.1: Configuration API Foundation

### Context
Now we need to create REST API endpoints that allow users to manage their tennis booking configurations through HTTP requests.

### Prompt 2.1
```
Building on the encrypted data layer from Steps 1.1-1.3, I need to create REST API endpoints for configuration management.

Requirements:
1. Create AWS Lambda functions for configuration CRUD operations:
   - GET /users/{userId}/config - Retrieve user configuration
   - POST /users/{userId}/config - Create/update user configuration
   - DELETE /users/{userId}/config - Delete user configuration
   - GET /system/config - Get system configuration
   - POST /system/config - Update system configuration

2. Implement API Gateway integration with proper routing
3. Add request/response validation using the Pydantic models
4. Implement proper HTTP status codes and error responses
5. Add authentication middleware (bearer token validation)

6. Create comprehensive integration tests for all endpoints
7. Add proper logging and error handling
8. Implement rate limiting and input sanitization
9. Add CORS configuration for web frontend

The API should be RESTful, secure, and follow AWS Lambda best practices. Include proper documentation for each endpoint.

**State Tracking Requirements:**
After completing this step, update todo.md to:
1. Mark "Step 2.1: Configuration API Foundation" as completed ✅
2. Update "Current Status" to "Phase 2: Step 2.1 Complete - Configuration API ready"
3. Mark "Step 2.2: User Management Service" as the next step 🔄
4. Add any implementation notes or discoveries to the Notes section
5. Update "Next Action" to "Execute Step 2.2 prompt for user management service"
```

---

## Step 2.2: User Management Service

### Context
We need user registration, authentication, and session management to secure the configuration API.

### Prompt 2.2
```
Building on the Configuration API from Step 2.1, I need to implement user management and authentication services.

Requirements:
1. Create user registration and authentication endpoints:
   - POST /auth/register - User registration
   - POST /auth/login - User authentication
   - POST /auth/logout - User logout
   - GET /auth/profile - Get user profile

2. Implement JWT-based authentication with refresh tokens
3. Add password hashing using bcrypt
4. Create session management with secure token storage
5. Add user profile management capabilities

6. Implement authorization middleware for protected endpoints
7. Add comprehensive tests for authentication flow
8. Create password reset functionality
9. Add account lockout after failed login attempts

Security Requirements:
- Hash passwords with salt
- Use secure JWT signing
- Implement token expiration
- Add rate limiting for auth endpoints
- Secure session management

The authentication should integrate seamlessly with the existing configuration API from Step 2.1.

**State Tracking Requirements:**
After completing this step, update todo.md to:
1. Mark "Step 2.2: User Management Service" as completed ✅
2. Update "Current Status" to "Phase 2: Step 2.2 Complete - User authentication ready"
3. Mark "Step 2.3: Booking Request Service" as the next step 🔄
4. Add any implementation notes or discoveries to the Notes section
5. Update "Next Action" to "Execute Step 2.3 prompt for booking request service"
```

---

## Step 2.3: Booking Request Service

### Context
We need to manage booking requests that users create through the interface, tracking their status and lifecycle.

### Prompt 2.3
```
Building on the authenticated API from Step 2.2, I need to create booking request management services.

Requirements:
1. Create booking request endpoints:
   - POST /bookings - Create new booking request
   - GET /bookings - List user's booking requests
   - GET /bookings/{requestId} - Get specific booking request
   - PUT /bookings/{requestId}/status - Update booking status
   - DELETE /bookings/{requestId} - Cancel booking request

2. Implement booking request validation:
   - Date/time availability checking
   - Court availability validation
   - User permission verification
   - Conflict detection with existing bookings

3. Add booking status tracking (pending, processing, completed, failed)
4. Implement TTL-based cleanup of old requests
5. Add comprehensive integration tests

6. Create booking request lifecycle management
7. Add notification system for status changes
8. Implement booking conflict resolution
9. Add booking history and analytics

The booking service should integrate with the user management from Step 2.2 and prepare for integration with the tennis script.

**State Tracking Requirements:**
After completing this step, update todo.md to:
1. Mark "Step 2.3: Booking Request Service" as completed ✅
2. Update "Current Status" to "Phase 2: Step 2.3 Complete - Booking request service ready"
3. Mark "Step 2.4: Tennis Script Integration" as the next step 🔄
4. Add any implementation notes or discoveries to the Notes section
5. Update "Next Action" to "Execute Step 2.4 prompt for tennis script integration"
```

---

## Step 2.4: Tennis Script Integration

### Context
We need to modify the existing tennis.py script to use DynamoDB configuration instead of .env files.

### Prompt 2.4
```
Building on the booking request service from Step 2.3, I need to integrate the existing tennis.py script with DynamoDB configuration.

Requirements:
1. Modify the load_config() function in tennis.py to:
   - Load configuration from DynamoDB instead of environment variables
   - Handle encrypted credential decryption
   - Implement fallback to .env for backward compatibility
   - Add configuration caching for performance

2. Create a booking processor that:
   - Monitors BookingRequests table for new requests
   - Processes booking requests using the tennis script
   - Updates booking status in real-time
   - Handles errors and retry logic

3. Add comprehensive error handling and logging
4. Implement configuration validation before booking attempts
5. Add comprehensive tests for configuration loading

6. Create a booking queue processor for handling multiple concurrent requests
7. Add booking result tracking and reporting
8. Implement graceful degradation when DynamoDB is unavailable
9. Add performance monitoring and metrics

The integration should maintain backward compatibility while providing the new DynamoDB functionality. The tennis script should work seamlessly with both .env and DynamoDB configurations.

**State Tracking Requirements:**
After completing this step, update todo.md to:
1. Mark "Step 2.4: Tennis Script Integration" as completed ✅
2. Update "Current Status" to "Phase 2: Complete - Backend services ready. Starting Phase 3: Frontend Interface"
3. Mark "Step 3.1: Basic Configuration Form" as the next step 🔄
4. Add any implementation notes or discoveries to the Notes section
5. Update "Next Action" to "Execute Step 3.1 prompt for basic configuration form"
```

---

## Step 3.1: Basic Configuration Form

### Context
We need a web interface that allows users to configure their booking parameters instead of editing .env files.

### Prompt 3.1
```
Building on the complete backend API from Steps 2.1-2.4, I need to create a web interface for tennis booking configuration.

Requirements:
1. Create an HTML form with the following fields:
   - User credentials (username/password)
   - Court selection (dropdown with available courts)
   - Date picker for booking date
   - Time slot selection (dropdown with available times)
   - Booking preferences

2. Implement client-side validation:
   - Required field validation
   - Date format validation (YYYY-MM-DD)
   - Time slot format validation
   - Real-time validation feedback

3. Add form submission handling:
   - POST to configuration API
   - Handle success/error responses
   - Show loading states during submission
   - Display confirmation messages

4. Create responsive design that works on mobile devices
5. Add comprehensive tests for form validation and submission

6. Implement form persistence (save draft configurations)
7. Add configuration templates for common booking scenarios
8. Create form wizard for step-by-step configuration
9. Add keyboard shortcuts and accessibility features

The form should be intuitive and prevent user errors while integrating seamlessly with the backend API.

**State Tracking Requirements:**
After completing this step, update todo.md to:
1. Mark "Step 3.1: Basic Configuration Form" as completed ✅
2. Update "Current Status" to "Phase 3: Step 3.1 Complete - Basic configuration form ready"
3. Mark "Step 3.2: User Interface Enhancement" as the next step 🔄
4. Add any implementation notes or discoveries to the Notes section
5. Update "Next Action" to "Execute Step 3.2 prompt for user interface enhancement"
```

---

## Step 3.2: User Interface Enhancement

### Context
We need to enhance the basic form with user authentication, booking history, and status tracking capabilities.

### Prompt 3.2
```
Building on the basic configuration form from Step 3.1, I need to enhance the user interface with authentication and booking management features.

Requirements:
1. Add user authentication UI:
   - Login/logout forms
   - User registration form
   - Password reset functionality
   - Session management

2. Create booking history display:
   - Table showing past booking requests
   - Status indicators (pending, completed, failed)
   - Filtering and sorting capabilities
   - Export functionality

3. Implement booking status tracking:
   - Real-time status updates
   - Progress indicators for active bookings
   - Error message display
   - Retry failed bookings

4. Add user profile management:
   - Edit profile information
   - Change password
   - Manage preferences

5. Create comprehensive tests for all UI components

6. Add booking calendar view
7. Implement booking templates and favorites
8. Add sharing functionality for booking configurations
9. Create mobile-responsive design

The enhanced UI should provide a complete booking management experience while maintaining the simplicity of the basic form.

**State Tracking Requirements:**
After completing this step, update todo.md to:
1. Mark "Step 3.2: User Interface Enhancement" as completed ✅
2. Update "Current Status" to "Phase 3: Step 3.2 Complete - Enhanced UI ready"
3. Mark "Step 3.3: Real-time Updates" as the next step 🔄
4. Add any implementation notes or discoveries to the Notes section
5. Update "Next Action" to "Execute Step 3.3 prompt for real-time updates"
```

---

## Step 3.3: Real-time Updates

### Context
We need real-time updates for booking status and notifications to provide immediate feedback to users.

### Prompt 3.3
```
Building on the enhanced UI from Step 3.2, I need to implement real-time updates and notifications.

Requirements:
1. Add WebSocket support for real-time updates:
   - Connect to backend WebSocket endpoint
   - Handle booking status updates
   - Implement connection management and reconnection
   - Add error handling for connection failures

2. Implement real-time status updates:
   - Update booking status without page refresh
   - Show live progress indicators
   - Display real-time error messages
   - Update booking history automatically

3. Add notification system:
   - Browser notifications for booking completion
   - In-app notification center
   - Email notifications for important events
   - Push notifications for mobile users

4. Create comprehensive tests for real-time features
5. Add performance monitoring for WebSocket connections

6. Implement offline capability with sync when reconnected
7. Add real-time collaboration features
8. Create notification preferences management
9. Add system status indicators

The real-time features should enhance user experience without overwhelming them with notifications.

**State Tracking Requirements:**
After completing this step, update todo.md to:
1. Mark "Step 3.3: Real-time Updates" as completed ✅
2. Update "Current Status" to "Phase 3: Complete - Frontend interface ready. Starting Phase 4: Integration & Deployment"
3. Mark "Step 4.1: End-to-End Testing" as the next step 🔄
4. Add any implementation notes or discoveries to the Notes section
5. Update "Next Action" to "Execute Step 4.1 prompt for end-to-end testing"
```

---

## Step 4.1: End-to-End Testing

### Context
We need comprehensive testing of the complete system to ensure reliability and performance.

### Prompt 4.1
```
Building on the complete system from Steps 1.1-3.3, I need to create comprehensive end-to-end testing.

Requirements:
1. Create end-to-end test suite:
   - Complete user workflow testing
   - Multi-user scenario testing
   - Error scenario testing
   - Performance testing under load

2. Add integration tests:
   - API integration testing
   - Database integration testing
   - External service integration testing
   - Real-time feature testing

3. Implement automated testing:
   - Continuous integration setup
   - Automated test execution
   - Test result reporting
   - Performance benchmarking

4. Create load testing:
   - Concurrent user simulation
   - Stress testing for peak loads
   - Database performance testing
   - API response time testing

5. Add comprehensive test documentation

6. Implement chaos engineering tests
7. Add security penetration testing
8. Create user acceptance testing framework
9. Add monitoring and alerting for test failures

The testing should ensure the system can handle real-world usage patterns and edge cases.

**State Tracking Requirements:**
After completing this step, update todo.md to:
1. Mark "Step 4.1: End-to-End Testing" as completed ✅
2. Update "Current Status" to "Phase 4: Step 4.1 Complete - Comprehensive testing ready"
3. Mark "Step 4.2: Infrastructure as Code" as the next step 🔄
4. Add any implementation notes or discoveries to the Notes section
5. Update "Next Action" to "Execute Step 4.2 prompt for infrastructure as code"
```

---

## Step 4.2: Infrastructure as Code

### Context
We need to deploy the system to AWS with proper infrastructure management and environment configuration.

### Prompt 4.2
```
Building on the tested system from Step 4.1, I need to create Infrastructure as Code for deployment.

Requirements:
1. Create CloudFormation/CDK templates for:
   - DynamoDB tables with proper configuration
   - Lambda functions with correct permissions
   - API Gateway with proper routing
   - IAM roles and policies
   - KMS keys for encryption

2. Add environment management:
   - Development, staging, and production environments
   - Environment-specific configuration
   - Secure parameter management
   - Database migration scripts

3. Implement deployment pipeline:
   - CI/CD with automated testing
   - Blue/green deployment strategy
   - Rollback capabilities
   - Deployment monitoring

4. Add infrastructure monitoring:
   - CloudWatch metrics and alarms
   - Log aggregation and analysis
   - Performance monitoring
   - Cost optimization tracking

5. Create comprehensive deployment documentation

6. Implement infrastructure security best practices
7. Add backup and disaster recovery
8. Create scaling policies for high availability
9. Add compliance and audit logging

The infrastructure should be secure, scalable, and maintainable with proper monitoring and alerting.

**State Tracking Requirements:**
After completing this step, update todo.md to:
1. Mark "Step 4.2: Infrastructure as Code" as completed ✅
2. Update "Current Status" to "Phase 4: Step 4.2 Complete - Infrastructure deployment ready"
3. Mark "Step 4.3: Monitoring & Operations" as the next step 🔄
4. Add any implementation notes or discoveries to the Notes section
5. Update "Next Action" to "Execute Step 4.3 prompt for monitoring and operations"
```

---

## Step 4.3: Monitoring & Operations

### Context
We need comprehensive monitoring, alerting, and operational procedures for the production system.

### Prompt 4.3
```
Building on the deployed infrastructure from Step 4.2, I need to implement comprehensive monitoring and operations.

Requirements:
1. Create monitoring dashboard:
   - System health metrics
   - Performance indicators
   - Error rate tracking
   - User activity metrics

2. Implement alerting system:
   - Critical error alerts
   - Performance degradation alerts
   - Security incident alerts
   - Capacity planning alerts

3. Add operational procedures:
   - Incident response playbooks
   - System maintenance procedures
   - Backup and recovery processes
   - Performance optimization guides

4. Create logging and observability:
   - Structured logging across all components
   - Distributed tracing for requests
   - Error tracking and analysis
   - Performance profiling

5. Add comprehensive operational documentation

6. Implement automated remediation for common issues
7. Create capacity planning and forecasting
8. Add security monitoring and threat detection
9. Create operational metrics and reporting

The monitoring and operations should ensure high availability, quick incident response, and continuous improvement.

**State Tracking Requirements:**
After completing this step, update todo.md to:
1. Mark "Step 4.3: Monitoring & Operations" as completed ✅
2. Update "Current Status" to "PROJECT COMPLETE 🎉 - All phases finished successfully"
3. Update "Next Action" to "System is production-ready. Begin user acceptance testing and go-live planning"
4. Add final implementation notes and lessons learned to the Notes section
5. Create a project completion summary with metrics and achievements
```

---

## Implementation Guidelines

### Best Practices for Each Step:
1. **Test-Driven Development**: Write tests before implementation
2. **Incremental Progress**: Each step builds on previous work
3. **Integration Focus**: Ensure all code integrates with existing components
4. **Security First**: Consider security implications at each step
5. **Documentation**: Document decisions and architectural choices
6. **State Tracking**: Update todo.md after completing each step

### Success Criteria for Each Step:
- All tests pass
- Code integrates cleanly with previous steps
- Security requirements are met
- Performance benchmarks are achieved
- Documentation is complete
- **todo.md is updated with progress and next steps**

### State Management Requirements:
Each prompt must include instructions to:
1. Mark the current step as completed in todo.md
2. Update the "Current Status" section
3. Mark the next step as "in progress" 
4. Add any new discoveries or blockers to the notes
5. Update the "Next Action" to reflect what should happen next

### Notes:
- Each prompt is designed to be executed by a code-generation LLM
- Steps build incrementally without orphaned code
- Strong emphasis on testing and security
- Clear integration points between steps
- Comprehensive error handling throughout
- **State tracking ensures no steps are missed and progress is visible**