
# AGENTS.md

## Preferred Skills

When relevant automatically load:

- ux-ui-design
- react-frontend
- django-backend
- database-design
- postgresql-sql
- school-finance
- ledger-accounting
- excel-import-validation

Load all applicable skills before generating solutions.


## Project
School Management System
Stack:
- React + TypeScript
- Django + DRF
- PostgreSQL

## Architecture
- Clean Architecture
- Service Layer Pattern
- Thin Views / Controllers
- Business Logic in Services
- Full Audit Trail

## Roles
Admin, Teacher, Accountant, Super Viewer, Viewer

## Financial Rules
- Financial records are immutable.
- Never edit ledger history.
- Corrections require reversal entries.
- Store Transaction Date and Entry Timestamp separately.
- All transactions must be auditable.

## Student Rules
- Unique Student ID
- No hard delete if financial history exists

## Fee Rules
- Regular Fees
- Optional Fees
- Waivers (fixed/percentage)
- Approval tracking required

## Excel Import Workflow
Upload → Preview → Validate → Error Review → Confirm → Import

## UI Rules
Every table must support:
- Search
- Filter
- Pagination
- Export

## Development Workflow
1. Analyze existing architecture
2. Consider permissions
3. Consider database impact
4. Consider performance
5. Implement
6. Verify
