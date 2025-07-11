# Data Directory

This directory contains database-related files and utilities.

## Structure

### `/migrations/`
Database migration scripts for schema changes:
- Version control for database schema
- Incremental updates for production deployment
- Rollback capabilities

### `/seeds/`
Test data and initial data setup:
- Sample user configurations
- Test booking requests
- System configuration defaults

### `/backups/`
Database backup files:
- Automated backup storage
- Manual backup storage
- Restore utilities

## Usage

### Running Migrations
```bash
# Run all pending migrations
python backend/src/database/migrations/run_migrations.py

# Create new migration
python backend/src/database/migrations/create_migration.py "migration_name"
```

### Seeding Data
```bash
# Load test data
python backend/src/database/seeds/load_test_data.py

# Load production seeds
python backend/src/database/seeds/load_production_data.py
```

### Backup and Restore
```bash
# Create backup
python scripts/backup_database.py

# Restore from backup
python scripts/restore_database.py backup_file.json
```

## Files

- `migrations/` - Database schema migrations
- `seeds/` - Initial and test data
- `backups/` - Database backups
- `README.md` - This file