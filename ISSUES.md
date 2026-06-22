# Issue Tracker — AL RAWA English School Management System

Legend: `fixed` · `open` · `wontfix`

## Overview

| | Total | Fixed | Open |
|--|-------|-------|------|
| 🔴 Critical | 2 | 2 | **0** |
| 🟠 High | 6 | 6 | **0** |
| 🟡 Medium | 13 | 10 | **3** |
| 🟢 Resolved | 2 | 2 | — |
| **All** | **23** | **20** | **3** |

---

| ID | Sev | Area | Issue | Status |
|----|-----|------|-------|--------|
| C1 | 🔴 | Security | SSH password hardcoded in 30+ `tmp/*.py` scripts. Rotated, history scrubbed, switched to key auth, `tmp/` gitignored. | `fixed` |
| C2 | 🔴 | Security | Deploy hooks in `tmp/` transmitted same credential server-side. Resolved by C1. | `fixed` |
| H1 | 🟠 | Testing | `test_settings.py` monkey-patches SQLite FK enforcement off for entire test suite (hides referential bugs). Switched to PostgreSQL test runner. | `fixed` |
| H2 | 🟠 | Ops | `cleanup_test_data.py` deletes real transactions matching `"Fee"` — no production guard. Added `--force` flag, requires explicit opt-in. | `fixed` |
| H3 | 🟠 | Backend | `attendance/views.py` 4 report endpoints swallow `Exception` → silent 500. Removed outer wrappers, narrowed inner catches to `(KeyError, TypeError, ValueError)` with `logger.warning`. | `fixed` |
| H4 | 🟠 | Auth | `teachers/views_mobile.py` uses `AllowAny` + manual PIN JWT per view; `mobile_teachers` had zero auth. Created `PinAuthentication` DRF class, refactored 6 endpoints. | `fixed` |
| H5 | 🟡 | UI | Student import/edit/delete gated on `isAdmin` in UI, but backend allows teachers. Loosened to `canEditStudents`/`canSaveResults` in `StudentSection.tsx`, `EnterByStudent.tsx`, `EnterBySubject.tsx`. | `fixed` |
| H6 | 🟡 | Perf | All people-list fetchers override default pagination with `limit:2000`. Removed override, added `offset`/page state + `setPage` actions in `school.ts`. | `fixed` |
| C3 | 🟡 | Backend | Student/teacher/staff import views missing `url_path='import'` and returning `not_implemented`. Added routes and real creation logic. | `fixed` |
| — | 🟠 | Backend | Bank account names (`AL_RAWA_BANK`/`GLOBAL_FORUM_BANK`) hardcoded in 4 locations: `base.py`, `reports.py`, `ledger.py`, migration 0005. Centralized to `base.py` (backend) + `accounts.ts` (frontend). Adding a bank now requires edits in 2 places. | `fixed` |
| — | 🟠 | Backend | `finance/views/transactions.py::bulk` wraps entire loop in `atomic()` — validation error on item N rolls back all prior items. Replaced with per-item savepoints. | `fixed` |
| — | 🟡 | Arch | No `School` FK across any model — single-tenant only. Full SaaS blocker. | `open` |
| — | 🟡 | Ops | Migration 0005 does raw SQLite DROP/CREATE + patches `check_constraints`. Risk on migration squash or SQLite test runs. | `open` |
| — | 🟡 | Backend | `AcademicYear.start_date`/`end_date` required in model but nullable in serializer. PATCH with `null` 500s instead of 400. Stripped `None` from validated_data in `validate()`. | `fixed` |
| — | 🟡 | Security | Rate limiting only on auth endpoints; all data endpoints use generic `anon: 1000/hour`. Added `UserRateThrottle` to global defaults, tighter `5/min` on reset-password and pin-login. | `fixed` |
| — | 🟡 | Backend | `perform_create` in `transactions.py` is ~150 lines mixing fee validation, allocation, receipts, audit. Extracted to `finance/services/transaction_service.py`. | `fixed` |
| — | 🟡 | Backend | `LessonPlan` serializer uses `className` but model has `class_name` — breaks camelCase convention used elsewhere. Added explicit field mapping. | `fixed` |
| — | 🟡 | Frontend | `FinanceSection.tsx`, `AttendanceSection.tsx`, `ExcelImportTab.tsx` are large monolithic components with mixed concerns. | `open` |
| — | 🟡 | Frontend | `DataTable.tsx` exists but is not imported anywhere. Deleted (YAGNI). | `fixed` |
| — | 🟡 | Frontend | Zustand 60s TTL cache has no systematic invalidation strategy after writes. Added `invalidateCache(key)` and `invalidatePattern(prefix)` store methods. | `fixed` |
| — | 🟡 | Docs | `AGENTS.md` references Coordinator/Parent roles and admission numbers that don't exist in code. Corrected to actual roles and removed admission number. | `fixed` |
| R1 | 🟢 | Backend | `_month_extract` raw SQL in `reports.py` replaced with clean `ExtractMonth` + allowlist. | `fixed` |
| R2 | 🟢 | Security | `.env` / `pgpass.txt` credentials leaked in git. Rotated, purged, `.env` gitignored. | `fixed` |

---

## Summary

| Severity | Total | Fixed | Open |
|----------|-------|-------|------|
| 🔴 Critical | 2 | 2 | 0 |
| 🟠 High | 6 | 6 | 0 |
| 🟡 Medium | 13 | 10 | 3 |
| 🟢 Resolved | 2 | 2 | — |
| **Total** | **23** | **20** | **3** |
