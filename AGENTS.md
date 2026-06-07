# AGENTS.md

## Project Overview
Django 6 + DRF backend (`school_management/`) with React 19 + TypeScript + Zustand + Vite frontend (`client/`). School management system: students, teachers, staff, finance, books, results.

## Commands

### Backend
```bash
# Run dev server
python manage.py runserver

# Run all tests (uses SQLite in-memory via test_settings)
python manage.py test -v 2

# Run single app tests
python manage.py test finance.tests -v 2
python manage.py test core.tests -v 2

# Run single test class
python manage.py test finance.tests.FinanceTests.test_create_transaction -v 2

# If test DB already exists (PostgreSQL), use --keepdb
python manage.py test finance.tests -v 2 --keepdb

# Migrations
python manage.py makemigrations
python manage.py migrate
```

### Frontend
```bash
cd client
npm run dev        # Vite dev server (proxies /api to localhost:8000)
npm run build      # tsc -b && vite build
npm run lint       # eslint .
npm run test       # vitest run
npm run test:watch # vitest (watch mode)
```

## Architecture

### Backend Structure
- `school_management/` — Django project settings, root URL config
- `accounts/` — Custom User model (email-based auth), JWT auth, permissions
- `core/` — SchoolClass, AcademicYear, Subject, Category, Settings, Report views
- `students/` — Student model (soft delete via `deleted_at`)
- `teachers/` — Teacher model
- `staff/` — Staff model
- `finance/` — Transaction, FeeSchedule, FeeWaiver, PaymentAllocation, StudentFeeAssignment, OpeningBalance, PeriodClose, BankAccount, AccountBalance, Reconciliation. Sub-views in `finance/views/` (transactions.py, fees.py, reports.py, base.py)
- `books/` — Book model
- `results/` — Result model

### Frontend Structure
- `client/src/store.ts` — Zustand store, axios instance with JWT interceptors
- `client/src/lib/config.ts` — API_URL = `/api`, fiscal year config
- `client/src/lib/types.ts` — TypeScript interfaces
- `client/src/lib/validation.ts` — Zod schemas
- `client/src/pages/` — Feature sections (FinanceSection.tsx, StudentSection.tsx, etc.)
- `client/src/components/` — Shared UI components

### API URL Convention
- Frontend uses relative paths: `api.get('/students/')` — no `${API_URL}` prefix needed
- Axios `baseURL` is set to `/api` in store.ts
- All POST/PUT/PATCH/DELETE must include trailing slash (DRF router with `APPEND_SLASH=True`)

### Database
- **Production**: PostgreSQL (configured in settings.py via env vars)
- **Tests**: SQLite in-memory (test_settings.py). FK enforcement disabled globally for SQLite.
- **Custom user model**: `accounts.User` (email-based, not username)

## Key Conventions

### Pagination
- Global `LimitOffsetPagination`: PAGE_SIZE=50, MAX_PAGE_SIZE=2000
- List responses wrapped in `{ count, results, ... }`
- Small reference views opt out with `pagination_class = None`
- Frontend fetches with `limit: '2000'` to get all data

### Serializers
- Use `CamelCaseModelSerializer` from `core/camelcase.py` for automatic snake_case→camelCase
- `SlugRelatedField(slug_field='name')` for FK fields — API accepts/returns names, not IDs
- **Gotcha**: `SlugRelatedField` field names must be snake_case in the serializer. camelCase field names silently drop input data.

### Filtering
- `filterset_fields` with lookup dicts for date ranges: `{'transaction_date': ['gte', 'lte']}`
- Keep old param names for backward compat (e.g., `class_id` and `classId`)

### Finance Domain
- `FeeSchedule.applicability`: `'AUTO'` (all students) or `'ASSIGNED_ONLY'` (only assigned students)
- `StudentFeeAssignment` requires `starts_at` and `ends_at` when activating (`active=True`)
- `PeriodClosedMixin` blocks transaction mutations on closed fiscal years
- `AccountBalance` cache updated on transaction create/cancel
- Bank accounts are `SlugRelatedField` — API uses account names like `'AL_RAWA_BANK'`

### Migrations
- PostgreSQL-safe: never `ALTER COLUMN ... TYPE uuid USING` on non-UUID values
- Use temp FK column + RunPython + RemoveField + RenameField pattern
- Use `SeparateDatabaseAndState` when Django auto-generates different index names

### Frontend Trailing Slashes
Every API call must end with `/`:
```typescript
api.get('/students/')       // correct
api.post('/transactions/', data)  // correct
api.get('/students')        // wrong — causes 301 redirect
```

### JWT Auth
- Access token: 1 day lifetime
- Refresh token: 30 days, rotated on use
- Tokens stored in `localStorage`
- Axios interceptor handles 401 → token refresh

## Critical Rules (from opencode.md)

### Security
- Never hardcode secrets — use `os.environ.get()` with fallback defaults
- Never log tokens, passwords, or sensitive data
- Validate all input at API boundaries
- Use parameterized queries / ORM — never string-concat SQL
- Enforce authorization server-side, never rely on frontend checks

### Error Handling
- No empty `except` blocks — always log or re-raise
- Return structured error responses with appropriate HTTP status codes
- Distinguish validation (400), auth (401/403), not-found (404), conflict (409), server (500)

### Code Quality
- Minimal, well-scoped changes — no broad rewrites
- Preserve public APIs unless breaking change is requested
- Run verification after every edit: `python manage.py test <relevant_app> -v 2`
- If verification cannot be run, explain why

### Testing
- Test behavior, not implementation details
- Use `APIClient` with JWT auth (see `_auth()` helper in test files)
- Tests use SQLite in-memory — FK enforcement disabled, some PostgreSQL-specific behavior may differ
- Paginated responses: assert on `res.data['results']`, not `res.data` directly

## Known Issues (from ISSUES.md)
- `.env` and `pgpass.txt` committed to repo — rotate exposed credentials
- Debug `print()` statements in `finance/views/transactions.py` and `finance/views/fees.py` — should be `logger.debug()`
- Ad-hoc scripts in project root (`check_*.py`, `debug2.py`, `clear_users.py`) — should be moved or deleted
- No `pyproject.toml` or `setup.cfg` — no enforced Python linting/formatting config
- JWT tokens in `localStorage` — vulnerable to XSS if any XSS vector exists
