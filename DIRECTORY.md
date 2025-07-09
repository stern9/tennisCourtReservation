# Directory Structure Redesign

## Overview
This document outlines the rationale and implementation plan for restructuring the tennis court reservation system from a flat directory structure to a professional, scalable monorepo organization.

## Current State Analysis

### Problems with Current Structure
- **Flat organization**: All files mixed at root level (tennis.py, run_api_server.py, test_ui.py, etc.)
- **Documentation scatter**: Step summaries, planning docs, and implementation notes spread throughout root
- **No clear frontend/backend separation**: Preparing for Phase 3 frontend development
- **Configuration chaos**: .env files, Docker configs, and deployment scripts not organized
- **Script confusion**: Utility scripts mixed with core application code
- **Testing disorganization**: Tests in separate folder but operational scripts at root

### Technical Debt Impact
- **Developer onboarding**: New developers struggle to understand project structure
- **Deployment complexity**: Configuration files scattered, making CI/CD setup difficult
- **Maintenance burden**: Code changes require hunting through multiple directories
- **Scaling limitations**: Adding new services or components becomes increasingly complex

## Proposed Solution

### New Directory Structure Philosophy

We're implementing a **monorepo architecture** with **clear separation of concerns**:

```
tennis-court-reservation/
├── backend/          # Python API and automation
├── frontend/         # React/Next.js UI
├── scripts/          # Operational and utility scripts
├── config/           # Environment and deployment configs
├── docs/             # All documentation, organized by type
├── data/             # Database migrations, seeds, backups
├── logs/             # Application logs (gitignored)
├── screenshots/      # Debug screenshots (gitignored)
└── .github/          # CI/CD workflows
```

## Detailed Structure Rationale

### 1. Backend Directory (`backend/`)
**Purpose**: Contain all Python code, APIs, and automation logic

**Structure**:
```
backend/
├── tennis.py                 # Main automation script (stays at backend root)
├── run_api_server.py         # API launcher (centralized)
├── src/                      # Application source code
│   ├── api/                  # FastAPI application
│   ├── dao/                  # Data access objects
│   ├── database/             # Database operations
│   ├── models/               # Pydantic models
│   ├── security/             # Encryption and auth
│   └── factories/            # Test data factories
└── tests/                    # All backend tests
```

**Benefits**:
- **Clear API boundaries**: Everything backend-related is contained
- **Independent deployment**: Backend can be containerized separately
- **Language consistency**: All Python code in one place
- **Import clarity**: Simplified Python path management

### 2. Frontend Directory (`frontend/`)
**Purpose**: Modern React/Next.js application for user interface

**Structure** (Next.js App Router):
```
frontend/
├── src/
│   ├── app/                  # Next.js App Router (layout.tsx, page.tsx)
│   ├── components/           # React components organized by feature
│   │   ├── auth/             # Authentication components
│   │   ├── booking/          # Booking management UI
│   │   ├── config/           # Configuration forms
│   │   ├── layout/           # Layout components
│   │   └── common/           # Shared components
│   ├── lib/                  # API clients and utilities (Next.js convention)
│   ├── hooks/                # Custom React hooks
│   ├── store/                # State management (Redux/Zustand)
│   ├── utils/                # Frontend utilities
│   └── styles/               # CSS and styling
├── public/                   # Static assets
└── package.json              # Frontend dependencies
```

**Benefits**:
- **Modern development**: Leverages latest React/Next.js patterns
- **Component organization**: Feature-based structure for scalability
- **Independent development**: Frontend team can work independently
- **Deployment flexibility**: Can be deployed to CDN or static hosting

### 3. Scripts Directory (`scripts/`)
**Purpose**: Centralize all operational and utility scripts

**Contents**:
- `run_tests.py` - Test execution scripts
- `test_ui.py` - UI testing utilities
- `setup_dev_environment.py` - Development setup automation
- `deploy.py` - Deployment scripts
- `backup_database.py` - Database backup utilities

**Benefits**:
- **Operational clarity**: All scripts in one discoverable location
- **Maintenance simplicity**: Easy to update and version control scripts
- **Team collaboration**: Scripts become shared team tools
- **CI/CD integration**: Easy to reference in automated workflows

### 4. Configuration Directory (`config/`)
**Purpose**: Environment-specific and deployment configurations

**Structure**:
```
config/
├── .env.example              # Environment template
├── docker/                   # Container configurations
│   ├── backend.Dockerfile    # Backend container
│   ├── frontend.Dockerfile   # Frontend container
│   └── nginx.conf            # Reverse proxy config
├── kubernetes/               # K8s manifests
│   ├── deployment.yaml
│   ├── service.yaml
│   └── ingress.yaml
└── aws/                      # AWS-specific configs
    ├── lambda-config.yaml
    └── dynamodb-config.json
```

**Benefits**:
- **Environment management**: Clear separation of dev/staging/prod configs
- **Deployment standardization**: All deployment configs in one place
- **Infrastructure as Code**: Configuration becomes versionable
- **Security**: Easier to manage secrets and sensitive configurations

### 5. Documentation Directory (`docs/`)
**Purpose**: Comprehensive documentation organization

**Structure**:
```
docs/
├── README.md                 # Project overview
├── API_DOCUMENTATION.md      # API reference
├── DEPLOYMENT_GUIDE.md       # Deployment instructions
├── ARCHITECTURE.md           # System architecture
├── development/              # Development history
│   ├── STEP_1_1_SUMMARY.md
│   ├── STEP_1_2_SUMMARY.md
│   └── ...
├── planning/                 # Planning documents
│   ├── implementation-prompts.md
│   ├── plan.md
│   ├── frontEnd-plan.md
│   └── AWS_SETUP.md
└── assets/                   # Documentation assets
    ├── architecture-diagram.png
    └── flow-diagrams/
```

**Benefits**:
- **Documentation as code**: Treats documentation as first-class citizen
- **Organized knowledge**: Easy to find relevant documentation
- **Historical tracking**: Development history preserved and organized
- **Onboarding efficiency**: New developers can quickly understand project

## Implementation Strategy

### Phase 1: Backend Reorganization
```bash
# 1. Create backend directory and move code
mkdir backend
mv src backend/
mv tests backend/
mv tennis.py backend/
mv run_api_server.py backend/

# 2. Update import paths in backend code
# 3. Update test configurations
# 4. Verify all backend functionality works
```

### Phase 2: Frontend Setup
```bash
# 1. Create frontend directory
mkdir frontend
cd frontend

# 2. Initialize Next.js project
npx create-next-app@latest . --typescript --tailwind --app

# 3. Set up project structure
mkdir -p src/{components/{auth,booking,config,layout,common},lib,hooks,store,utils}

# 4. Configure build and development scripts
```

### Phase 3: Scripts and Configuration
```bash
# 1. Create scripts directory
mkdir scripts
mv run_tests.py scripts/
mv test_ui.py scripts/

# 2. Create config directory
mkdir -p config/{docker,kubernetes,aws}
mv .env.example config/
mv Dockerfile config/docker/backend.Dockerfile

# 3. Create deployment configurations
```

### Phase 4: Documentation Reorganization
```bash
# 1. Create docs structure
mkdir -p docs/{development,planning,assets}

# 2. Move existing documentation
mv STEP_*.md docs/development/
mv plan.md docs/planning/
mv implementation-prompts.md docs/planning/
mv frontEnd-plan.md docs/planning/
mv AWS_SETUP.md docs/planning/

# 3. Create new documentation
```

### Phase 5: Root-Level Organization
```bash
# 1. Create data and utility directories
mkdir -p data/{migrations,seeds,backups}
mkdir -p logs screenshots

# 2. Set up CI/CD
mkdir -p .github/workflows

# 3. Create root package.json for monorepo management
```

## Strengths of This Approach

### 1. Clear Separation of Concerns
The top-level separation into `backend/`, `frontend/`, `scripts/`, `config/`, and `docs/` is the **gold standard for monorepo organization**. It makes the project instantly understandable and prevents code from becoming entangled.

### 2. Scalability
This structure is **built for growth**. It would be trivial to add another service (e.g., a `worker/` directory for background jobs) or to containerize each part independently. The clear boundaries are essential for a growing team.

### 3. Developer Experience (DX)
Anyone joining the project would **immediately recognize this pattern**. It clarifies where to find code, how to run tests, and where configuration lives. The `scripts/` directory is a great touch for centralizing operational tasks.

### 4. Deployment Ready
The `config/` directory, with its subfolders for Docker, Kubernetes, and AWS, is **forward-thinking**. It shows that the project is designed not just to be written, but to be deployed and managed in a production environment.

### 5. Excellent Documentation Hierarchy
Moving all markdown files and planning documents into a structured `docs/` directory is a **fantastic idea**. It cleans up the root, makes documentation discoverable, and treats documentation as a first-class citizen of the project.

## Considerations and Refinements

### Frontend Structure Alignment
Since we're using **Next.js with the App Router** (as per the `frontEnd-plan.md`), the actual structure will be slightly different:
- No `public/index.html` or `App.jsx`
- Core will be `src/app/layout.tsx` and `src/app/page.tsx`
- Component folders (`auth/`, `booking/`, etc.) should be implemented within `src/components/`
- The `services/` directory is better named `lib/` in Next.js context to align with community conventions

### Root Package.json
We'll need a **root `package.json`** for:
- Shared development dependencies (prettier, eslint)
- Scripts that orchestrate both frontend and backend (using tools like `concurrently`)
- Monorepo management tools (if needed)

### Migration Verification
Each phase includes verification steps:
1. **Backend**: Ensure all APIs work and tests pass
2. **Frontend**: Verify build and development servers
3. **Scripts**: Test all operational scripts
4. **Documentation**: Ensure all links and references work
5. **Integration**: Verify full-stack functionality

## Expected Outcomes

### Immediate Benefits
- **Cleaner root directory**: Only essential files at top level
- **Better organization**: Code is logically grouped
- **Improved developer experience**: Easier to navigate and understand
- **Deployment preparation**: Ready for containerization and CI/CD

### Long-term Benefits
- **Team scalability**: Multiple developers can work efficiently
- **Maintainability**: Easier to update and refactor code
- **Feature development**: Clear patterns for adding new functionality
- **Professional presentation**: Project structure demonstrates maturity

## Risk Mitigation

### Import Path Changes
- **Backend**: Update all Python imports to reflect new structure
- **Frontend**: Ensure proper module resolution configuration
- **Tests**: Update test discovery and execution paths

### Build Process Updates
- **Docker**: Update Dockerfile paths and context
- **CI/CD**: Update workflow file paths and commands
- **Scripts**: Update any hardcoded paths in utility scripts

### Documentation Links
- **Internal references**: Update all markdown links
- **External references**: Ensure external tools can find files
- **API documentation**: Update any path references

## Success Metrics

### Technical Metrics
- [ ] All tests pass after migration
- [ ] All scripts execute successfully
- [ ] API endpoints respond correctly
- [ ] Frontend builds and runs without errors
- [ ] Docker containers build successfully

### Quality Metrics
- [ ] New developer onboarding time reduced
- [ ] Documentation is easily discoverable
- [ ] Code review process is more efficient
- [ ] Deployment process is streamlined
- [ ] Project structure is self-documenting

## Conclusion

This directory restructure represents a **significant improvement** in project organization, moving from a flat, development-phase structure to a **professional, scalable monorepo architecture**. The proposed structure aligns with industry best practices, facilitates team collaboration, and prepares the project for production deployment.

The **phased migration approach** ensures minimal disruption while providing clear checkpoints for validation. Each phase builds upon the previous one, allowing for incremental improvement and risk mitigation.

This restructure is **essential preparation** for Phase 3 (Frontend Interface) and positions the project as a **mature, maintainable application** ready for long-term development and deployment.

---

*This document should be updated as the migration progresses and new insights are gained.*