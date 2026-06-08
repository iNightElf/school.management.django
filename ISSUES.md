# Application Issues Report

Generated from line-by-line code review of the Django School Management System.

---

## Critical

### 1. Hardcoded Database Credentials in Source Code
- **File**: `core/management/commands/import_firebase.py:23-25`
- **What**: PostgreSQL connection string with username and password in plaintext
- **Risk**: Credential exposure in version control history
- **Fix**: Use `os.environ.get()` with a required env var, fail if missing

### 2. Committed Secrets Files
- **Files**: `.env`, `pgpass.txt`
- **What**: Supabase URL, service key, and likely DB password committed to repo
- **Risk**: All secrets exposed to anyone with repo access
- **Fix**: Add `.env` and `pgpass.txt` to `.gitignore`, rotate all exposed credentials

---

## High

### 3. Debug `print()` Statements in Production Code
- **File**: `finance/views/transactions.py:528,541`
- **File**: `finance/views/fees.py:110,119,126,130`
- **What**: `[DEBUG]` print statements left in view logic
- **Risk**: Debug output in production logs, potential performance impact
- **Fix**: Remove or replace with `logger.debug()`

### 4. `_month_extract` Returns Raw Dict Instead of ORM Expression
- **File**: `finance/views/reports.py:234-241`
- **What**: Returns `{"month": f"EXTRACT(MONTH FROM {field})"}` dict used as ORM annotation
- **Risk**: Breaks on SQLite (double `%` escape), fragile SQL string interpolation
- **Fix**: Use `django.db.models.functions.ExtractMonth` or `django.db.models.Func` for vendor-safe extraction

### 5. Paginated Endpoint Tests Assert Wrong Response Shape
- **File**: `core/tests.py:32` — `test_list_classes` asserts `len(res.data) == 2`
- **File**: `core/tests.py:109` — `test_list_academic_years` asserts `len(res.data) == 1`
- **File**: `core/tests.py:145` — `test_list_categories` asserts `len(res.data) == 2`
- **What**: Global `LimitOffsetPagination` wraps responses in `{count, results}`, but tests index `res.data` directly
- **Risk**: Tests pass only if views opt out of pagination or SQLite test DB differs
- **Fix**: Assert `len(res.data['results'])` or `res.data['count']`

### 6. Frontend Missing Trailing Slashes on API Calls
- **File**: `client/src/store.ts:313,322,335,348,361,375,511,596,602`
- **What**: Calls like `api.get('/classes')`, `api.get('/students')`, etc. lack trailing slashes
- **Risk**: 301 redirects on DRF router (wastes round-trips) or 404 if `APPEND_SLASH=False`
- **Fix**: Add trailing slashes: `api.get('/classes/')`, `api.get('/students/')`, etc.

---

## Medium

### 7. `StudentViewSet.get_queryset` Doesn't Use `super().get_queryset()`
- **File**: `students/views.py:27`
- **What**: Duplicates queryset instead of calling `super().get_queryset()` like `TeacherViewSet` and `StaffViewSet`
- **Risk**: DRY violation; if base queryset changes, this view misses the update
- **Fix**: Call `super().get_queryset()` and chain filters

### 8. Frontend `Transaction` Type Field Mismatch
- **File**: `client/src/lib/types.ts:82` — field named `date`
- **File**: `finance/serializers.py:11` — serializer outputs `transactionDate` (camelCase)
- **Risk**: Frontend reads `transaction.date` but API returns `transaction.transactionDate`
- **Fix**: Rename type field to `transactionDate` or add alias

### 9. Frontend `Book` Type Doesn't Match API Response
- **File**: `client/src/lib/types.ts:130-135` — uses `title`, `author`, `schoolClassId`
- **File**: `books/serializers.py:6` — API returns `name`, `publication`, `school_class` (via FK), `className`
- **Risk**: Frontend reads wrong field names
- **Fix**: Update `Book` type to match actual serializer output

### 10. `openingBalancesSchema` Hardcodes Bank Account Names
- **File**: `client/src/lib/validation.ts:62-66`
- **What**: Schema validates against `AL_RAWA_BANK`, `GLOBAL_FORUM_BANK`, `CASH_IN_HAND`
- **Risk**: Breaks if accounts are added/renamed; not maintainable
- **Fix**: Fetch account names dynamically or use a flexible `z.record(z.string(), z.number())`

### 11. `Book` Model Missing DB Index on `school_class` FK
- **File**: `books/models.py:12`
- **What**: `school_class` FK used in `filter()` queries but has no explicit `db_index=True`
- **Risk**: Slow queries on book list filtered by class at scale
- **Fix**: Add `db_index=True` to the FK field

### 12. `Dashboard.tsx` Swallows Errors Silently
- **File**: `client/src/pages/Dashboard.tsx:38`
- **What**: `catch { /* ignore */ }` on verification email resend
- **Risk**: User sees no feedback when request fails; violates opencode.md §7 (no silent failures)
- **Fix**: Show error toast or log the error

---

## Low

### 13. Ad-hoc Utility Scripts in Project Root
- **Files**: `check_fields.py`, `check_finance.py`, `check_finance2.py`, `check_register.py`, `clear_users.py`, `debug2.py`
- **What**: One-off debug/verification scripts left in project root
- **Risk**: Confusion about what's part of the application; may contain credentials or test data
- **Fix**: Move to `core/management/commands/` or delete

### 14. Stale Session File
- **File**: `session-ses_16cf.md`
- **What**: Appears to be a stale session log
- **Risk**: Confusion; may contain sensitive session data
- **Fix**: Delete from repo

### 15. Empty `admin.py` in All Apps
- **Files**: `students/admin.py`, `teachers/admin.py`, `staff/admin.py`, `books/admin.py`, `accounts/admin.py`
- **What**: No admin registrations for any models
- **Risk**: Operators can't manage data via Django admin
- **Fix**: Register key models with appropriate `list_display`, `search_fields`, `readonly_fields`

### 16. Missing `__str__` on Finance Models
- **File**: `finance/models.py` — `PaymentAllocation` (line 179), `StudentFeeAssignment` (line 154)
- **What**: No `__str__` method defined
- **Risk**: Unhelpful admin display and debug output
- **Fix**: Add `__str__` returning meaningful representation

### 17. `RoleChoicesView` Exposes Roles to Unauthenticated Users
- **File**: `accounts/views.py:143`
- **What**: `permission_classes = []` on role list endpoint
- **Risk**: Minor information disclosure
- **Fix**: Add `IsAuthenticated` permission

### 18. `results/views.py:53-54` — Empty Lines After Variable Assignment
- **File**: `results/views.py:53-54`
- **What**: Cosmetic empty lines in middle of function
- **Fix**: Remove extra blank lines

---

## Informational

### 19. `FeeSchedule` Uses `CharField` for `category` Instead of FK to `Category`
- **File**: `finance/models.py:94` — `category = models.CharField(max_length=100)`
- **File**: `core/models.py:84` — `Category` model exists with `INCOME`/`EXPENSE` types
- **What**: Fee categories are free-text, not normalized to the `Category` table
- **Note**: May be intentional for flexibility, but allows inconsistent data

### 20. `Transaction.category` Also Free-Text
- **File**: `finance/models.py:37` — `category = models.CharField(max_length=100, blank=True, null=True)`
- **What**: Same pattern as FeeSchedule — no FK to `Category` model
- **Note**: Allows mismatched category names between transactions and fee schedules

### 21. Frontend Uses `localStorage` for JWT Tokens
- **File**: `client/src/store.ts:14,18`
- **What**: Access and refresh tokens stored in `localStorage`
- **Note**: Vulnerable to XSS if any XSS vector exists; `httpOnly` cookies are more secure per opencode.md §4

### 22. `test_settings.py` Disables All FK Enforcement on SQLite
- **File**: `school_management/test_settings.py:14-34`
- **What**: Monkey-patches SQLite to always disable FK constraints
- **Note**: Masks FK constraint violations in tests; migration 0005 issue acknowledged in comment

### 23. `setup/ext.json` Missing
- **Note**: No `setup.cfg` or `pyproject.toml` for Python tooling (ruff, mypy, isort)
- **Impact**: No enforced code style for Python beyond manual review

---

## Summary

| Severity | Count |
|----------|-------|
| Critical | 2 |
| High | 4 |
| Medium | 6 |
| Low | 6 |
| Informational | 5 |
| **Total** | **23** |
