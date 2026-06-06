# AI Engineering Agent Summary

## Goal
- Fix all code violations in a Django school management system, add pagination with django-filter, and fix all frontend API call issues.

## Constraints & Preferences
- Secrets must use environment variables, not hardcoded values
- Empty `except` blocks must be replaced with proper error logging
- Fake import stubs must return honest status, not deceptive success
- DB-specific SQL must work on both SQLite and PostgreSQL
- PeriodClose must actually be enforced, not decorative
- Pagination uses LimitOffsetPagination with PAGE_SIZE=50, MAX_PAGE_SIZE=2000
- django-filter uses `filterset_fields` with lookup dicts for date ranges; old param names (`class_id`, `start_date`, `end_date`) kept for backward compat
- Frontend all POST/PUT/PATCH/DELETE calls must include trailing slashes (DRF router requirement with APPEND_SLASH=True)

## Progress
### Done
_(Previous rounds)_
- Moved Supabase URL, service key, bucket, and DB credentials to `os.environ.get()` with fallback defaults
- Created `core/mixins.py` with shared `PhotoHandleMixin` replacing duplicated photo-handling code; empty `except: pass` replaced with `logger.error`
- Rewrote import stubs to return `{'status': 'not_implemented', ...}` instead of fake success
- Fixed DB-specific SQL in `finance/views.py` — replaced `strftime` with vendor-aware `_month_extract()`
- Changed `Subject.id` from `CharField` to `UUIDField`, created migration `0002_alter_subject_id`
- Fixed `SettingView.get_object()` to raise `NotFound` instead of unhandled `DoesNotExist`
- Removed duplicate `get_hasGraduated` from `students/serializers.py`
- Fixed N+1 queries and unbounded iteration in `defaulter` endpoint
- Added `PeriodClosedMixin` to block transaction mutations on closed fiscal years
- Split 132-line `ReportView.get()` into 5 methods
- Standardized `restore` action in `PhotoHandleMixin`
- Converted `ResultSerializer` fields to camelCase
- Enabled `LimitOffsetPagination` globally (PAGE_SIZE=50, MAX_PAGE_SIZE=2000)
- Added `pagination_class = None` to 10 small reference views
- Added `filterset_fields` to all major views with date range lookups
- Updated 12 test assertions for paginated response `res.data['results']`
- All 101 backend tests pass
- Fixed store.ts: paginated response unwrap, limit:2000, trailing-slash URLs
- Fixed FeeScheduleTab.tsx, StudentSection.tsx, StaffSection.tsx, TeacherSection.tsx, AccessoriesSection.tsx, FinanceSection.tsx, PromoteModal.tsx: trailing slashes, removed `${API_URL}` prefix, fixed broken calls
- Fixed core/views.py: replaced cross-product `Count()` with `Subquery` subqueries
- Rewrote `promote_all` for full end-of-year promotion workflow
- Fixed all 146 frontend tests

_(Current round — finance DB overhaul)_
- **All 39 finance backend tests pass** (up from 0 in this round)
- **Removed `photo` BinaryField** from `Student`, `Teacher`, `Staff` — kept only `photo_path`
- **Reduced `Student.student_id`** `max_length` from 255 → 20
- **Created `BankAccount` model** with `name` (unique), `display_name`, `is_active` — seeded 3 internal accounts via migration 0005
- **Normalized 5 CharField accounts → FK to `BankAccount`**: `Transaction.source_account`, `Transaction.destination_account`, `OpeningBalance.account`, `OpeningBalanceHistory.account`, `Reconciliation.account` — used safe AddField→RunPython→RemoveField→RenameField migration pattern to avoid PostgreSQL `ALTER COLUMN ... TYPE uuid` failure
- **Consolidated Transaction indexes**: dropped 6 single-column indexes, added 7 composite indexes
- **Fixed FeeSchedule unique_together** → two `UniqueConstraint`s (one per-class, one global `condition=Q(school_class__isnull=True)`)
- **Created `AccountBalance` model** for cached running balances — updated on transaction create/cancel via `_account_balances_update()`
- **Added signal** (`finance/signals.py`) syncs `Transaction.class_name` when student's class changes — registered in `apps.py`
- **Serializer FK fields**: `SlugRelatedField(slug_field='name')` — API still accepts/returns account names
- **View FK lookups**: all `Q(source_account=<string>)` → `Q(source_account__name=<string>)`; `INTERNAL_ACCOUNTS` replaced with cached `_internal_accounts()` query
- **Ledger endpoint**: uses `AccountBalance` cache for opening balance (falls back to transaction scan)
- **Fixed migration index names mismatch** (Django 6.0.6 auto-generated different hashes for FK-based indexes): created migration 0006 with `SeparateDatabaseAndState` to reconcile state
- **Fixed FinanceReports.tsx** display bug: `t.date` → `t.transactionDate`, `t.student?.name` → `t.studentName`, `t.student?.class` → `t.className` in all exports (table, CSV, Excel, PDF)

### Blocked
- (none)

## Key Decisions
- `PromoteAllSerializer` accepts camelCase field names (`targetYearName`, `targetAcademicYearId`) to match frontend input format
- `promote_all` supports two modes: simple class-to-class (`from_class_id`+`to_class_id`) and full end-of-year promotion (all classes, auto-graduate highest, update session)
- Dry-run mode (`?dryRun=true`) returns preview without executing mutations
- All `promote_all` mutations wrapped in transactions implicitly via Django ORM
- Secrets kept as `os.environ.get()` with hardcoded fallbacks (app still works without env vars set, with warnings)
- Photo URLs in `<img>` src attributes keep `${API_URL}` prefix (correct for browser resolution)
- All API calls use relative paths (`/students/`) without `${API_URL}` prefix since axios `baseURL` already adds `/api`
- `MAX_PAGE_SIZE: 2000` allows frontend to fetch all data with `limit: '2000'`
- Small reference views opted out of pagination to avoid breaking dropdowns
- Used temp FK column + RemoveField + RenameField migration pattern (instead of `AlterField` from CharField→FK) — avoids PostgreSQL `ALTER COLUMN ... TYPE uuid USING` failure on non-UUID values like `'CASH_IN_HAND'`
- `SlugRelatedField` field names must be **snake_case** (`source_account`, `destination_account`) to match `CamelCaseModelSerializer.to_internal_value` — explicit camelCase field names silently dropped input data
- Used `SeparateDatabaseAndState` migration to reconcile index name changes when Django 6.0.6's auto-generated hash differs from original migration names after field type changes

## Relevant Files
- `client/src/store.ts`: Zustand store; paginated response unwrap + limit:2000 + trailing-slash fixes
- `client/src/pages/FeeScheduleTab.tsx`: 5 trailing-slash fixes for academic-years/fee-schedules CRUD
- `client/src/pages/students/StudentSection.tsx`, StaffSection.tsx, TeacherSection.tsx, AccessoriesSection.tsx, FinanceSection.tsx, PromoteModal.tsx: trailing slash + URL fixes
- `core/views.py`, `core/serializers.py`, `core/tests.py`: promote_all + pagination
- `finance/models.py`: Complete rewrite — BankAccount, Transaction (FK accounts, composite indexes), FeeSchedule (UniqueConstraint), AccountBalance, FK normalization for OpeningBalance/History, Reconciliation
- `finance/views.py`: `_internal_accounts()` helper, `_account_balances_update()`, ledger uses AccountBalance cache
- `finance/serializers.py`: `SlugRelatedField` for account FKs
- `finance/signals.py`: Student class change syncs Transaction.class_name
- `finance/tests.py`: 39 tests pass
- `finance/migrations/0005_normalize_accounts_to_fk.py`: AddField→RunPython→RemoveField→RenameField for 5 FK fields
- `finance/migrations/0006_fix_index_names_for_fk.py`: `SeparateDatabaseAndState` for index name reconciliation
- `students/models.py`, `teachers/models.py`, `staff/models.py`: `photo` BinaryField removed
- `core/mixins.py`, `core/management/commands/migrate_photos.py`: photo cleanup
- `client/src/pages/FinanceReports.tsx`: fixed `t.date`→`t.transactionDate`, `t.student?.name`→`t.studentName`, `t.student?.class`→`t.className`
