# Tennis Court Reservation System - Documentation

## Overview
This directory contains all documentation for the Tennis Court Reservation System, organized by type and purpose.

## Documentation Structure

### 📋 [Development History](./development/)
Step-by-step implementation summaries documenting the evolution of the system:
- `STEP_1_1_SUMMARY.md` - DynamoDB Local Setup & Schema Creation
- `STEP_1_2_SUMMARY.md` - Data Models & Validation Layer
- `STEP_1_3_SUMMARY.md` - Encryption Utilities
- `STEP_2_1_SUMMARY.md` - Configuration API Foundation
- `STEP_2_2_SUMMARY.md` - User Management Service
- `STEP_2_3_SUMMARY.md` - Booking Request Service
- `STEP_2_4_SUMMARY.md` - Tennis Script Integration

### 📝 [Planning Documents](./planning/)
Original planning and design documents:
- `plan.md` - Overall project plan and architecture
- `implementation-prompts.md` - Detailed implementation prompts
- `frontEnd-plan.md` - Frontend development plan
- `AWS_SETUP.md` - AWS deployment setup guide

### 🎨 [Assets](./assets/)
Documentation assets and diagrams:
- Architecture diagrams
- Flow charts
- Screenshots
- Visual documentation

## Quick Start

### For Developers
1. Read the [API Documentation](./API_DOCUMENTATION.md)
2. Review the [Architecture Overview](./ARCHITECTURE.md)
3. Follow the [Development Guide](./development/)

### For Deployment
1. Check the [Deployment Guide](./DEPLOYMENT_GUIDE.md)
2. Review [AWS Setup](./planning/AWS_SETUP.md)
3. See [Infrastructure as Code](./planning/infrastructure.md)

## System Architecture

The Tennis Court Reservation System is a full-stack application with:
- **Backend**: Python FastAPI with DynamoDB
- **Frontend**: React/Next.js (Phase 3)
- **Automation**: Selenium WebDriver for court booking
- **Security**: End-to-end encryption for credentials
- **Deployment**: AWS Lambda + DynamoDB

## Development Phases

### ✅ Phase 1: Foundation & Data Layer
- DynamoDB setup and schema design
- Data models with validation
- Encryption utilities and security

### ✅ Phase 2: Backend Services
- FastAPI application with JWT authentication
- User management with encrypted credentials
- Booking request service with scheduling
- Tennis script integration with DynamoDB

### 🔄 Phase 2.5: Project Restructure
- Monorepo organization
- Professional directory structure
- Documentation organization

### 🔜 Phase 3: Frontend Interface
- React/Next.js application
- User interface for booking management
- Real-time updates and notifications

### 🔜 Phase 4: Integration & Deployment
- End-to-end testing
- Infrastructure as Code
- Production deployment

## Contributing

### Documentation Standards
- Use clear, descriptive titles
- Include code examples where relevant
- Keep documentation up-to-date with code changes
- Use consistent formatting and structure

### File Organization
- **Development docs**: Step-by-step implementation history
- **Planning docs**: Design decisions and architecture
- **Assets**: Visual documentation and diagrams
- **API docs**: Endpoint documentation and examples

## Links and References

- [Project Repository](../README.md)
- [Backend Code](../backend/)
- [Frontend Code](../frontend/) *(Phase 3)*
- [Configuration](../config/)
- [Scripts](../scripts/)

---

*This documentation is actively maintained and updated with each development phase.*