# AL RAWA English School — Architecture Reference

---

## Stack

| Layer | Technology |
|-------|-----------|
| Backend | Django 6 + Django REST Framework 3.17 |
| Frontend | React 19 + TypeScript 6 + Vite 8 + Tailwind v4 |
| Database | PostgreSQL (Supabase free tier) |
| Auth | JWT (simplejwt) via HttpOnly cookies |
| AI | Gemini (primary) or OpenAI-compatible providers |
| Push | Web Push (VAPID) — pywebpush |
| Deployment | Backend: alwaysdata (Gunicorn), Frontend: GitHub Pages |
| Python | 3.12 |

---

## High-Level Architecture

```
┌──────────────────────────────────────────────────┐
│                   Frontend (:5173)                │
│  React SPA │ HashRouter │ Zustand │ Tailwind v4   │
│  PWA (manifest + service worker)                  │
│  Vite proxy: /api → Django :8000                  │
└──────────────────────┬───────────────────────────┘
                       │ HTTP (JSON)
┌──────────────────────▼───────────────────────────┐
│                   Backend (:8000)                  │
│  Django 6 │ DRF │ Custom CookieJWTAuth            │
│  14 apps (accounts, core, students, teachers...)  │
│  Gunicorn WSGI │ PostgreSQL                        │
└──────────────────────────────────────────────────┘
```

---

## Design Patterns

| Pattern | Where |
|---------|-------|
| **Model-View-Serializer** (DRF) | All apps — DRF ViewSets + Serializers |
| **Registry Pattern** | `ai_query/handlers/` — `@ai_function` decorator registers 25 handlers |
| **Soft Delete** | Student, Teacher, Staff — `deleted_at` field, no hard deletes |
| **Lazy Generation** | Finance `ensure_student_fee_statuses()` creates records on first view |
| **Mixins** | `PhotoUrlMixin`, `PhotoHandleMixin`, `AuditLogMixin`, `CamelCaseModelSerializer` |
| **Service Layer** | `finance/services/`, `parents/services.py`, `core/services.py`, `engagement/ai_service.py` |
| **Cache + Invalidation** | `@cache_page(60)` on dashboard, signals invalidate on model changes |
| **CamelCase JSON API** | `CamelCaseModelSerializer` converts snake_case ↔ camelCase |
| **State Management** | Zustand stores (`useAuthStore`, `useSchoolStore`, `useUIStore`, etc.) |
| **Lazy Loading** | `React.lazy()` for all route pages |
| **Deduped Requests** | `dedupedFetch` — key-based in-flight request deduplication |
| **API Versioning** | Single version — `/api/` prefix |
| **Role-Based Access** | `ROLE_PERMISSIONS` dict — 6 roles (admin/teacher/accountant/super_viewer/viewer/parent) |
| **Audit Logging** | `AuditLogMixin` on ViewSets + manual `log_audit()` calls |
| **Draft/Publish** | Results — teachers enter marks anytime, admin publishes per term |

---

## Project Structure

```
python-django/
├── manage.py
├── requirements.txt / requirements-production.txt
├── Procfile / runtime.txt
├── .env / .env.example
├── AGENTS.md / README.md / ARCHITECTURE.md
│
├── school_management/              # Django project config
│   ├── settings.py
│   ├── urls.py                     # Root URL routing
│   └── wsgi.py
│
├── accounts/                       # Auth & user management
├── core/                           # Shared base models
├── students/                       # Student management
├── teachers/                       # Teacher management
├── staff/                          # Staff management
├── books/                          # Book inventory
├── results/                        # Exam results
├── attendance/                     # Attendance tracking
├── finance/                        # Fee obligation tracker
├── academic/                       # Academic structure
├── parents/                        # Parent portal
├── engagement/                     # Gamification
├── ai_query/                       # NL AI query engine
│
├── templates/
├── staticfiles/
│
└── client/                         # React SPA frontend
    ├── index.html
    ├── vite.config.ts
    ├── package.json
    ├── tsconfig.json
    ├── public/
    │   ├── manifest.json
    │   └── sw.js                    # Service worker
    └── src/
        ├── main.tsx
        ├── App.tsx                  # HashRouter + all routes
        ├── store.ts                 # Re-exports
        ├── stores/
        │   ├── api.ts               # Axios instance + deduped fetch
        │   ├── auth.ts              # useAuthStore
        │   ├── school.ts            # useSchoolStore
        │   ├── ui.ts                # useUIStore + useDarkMode
        │   ├── users.ts             # useUserManagementStore
        │   └── aiQuery.ts           # useAIQueryStore
        ├── lib/
        │   ├── types.ts             # All TypeScript interfaces
        │   ├── config.ts            # API_URL, constants
        │   ├── supabase.ts          # Supabase client
        │   ├── validation.ts        # Zod schemas
        │   ├── accounts.ts          # Account definitions
        │   ├── reportPdf.ts         # Report card PDF
        │   ├── tabulationPdf.ts     # Tabulation PDF
        │   ├── financeReportPdf.ts  # Financial report PDFs
        │   ├── defaulterPdf.ts      # Defaulter PDF
        │   ├── usePullToRefresh.ts
        │   ├── useFocusTrap.ts
        │   └── usePushSubscription.ts
        ├── ai/
        │   ├── AICommandPalette.tsx  # Cmd+K palette
        │   ├── AIResultPanel.tsx
        │   ├── AIResultTable.tsx
        │   └── AIResultSummary.tsx
        ├── components/
        │   ├── Layout.tsx
        │   ├── BottomNav.tsx
        │   ├── Toast.tsx
        │   ├── Modal.tsx
        │   ├── Skeleton.tsx
        │   ├── ExportMenu.tsx
        │   ├── ClassSelect.tsx
        │   ├── DatePicker.tsx
        │   ├── PhotoUpload.tsx
        │   ├── CameraModal.tsx
        │   ├── ImportModal.tsx
        │   ├── PromoteModal.tsx
        │   ├── TransactionForm.tsx
        │   ├── LedgerTable.tsx
        │   ├── BalanceSummary.tsx
        │   ├── EmptyState.tsx
        │   ├── ErrorBoundary.tsx
        │   ├── IOSInstallPrompt.tsx
        │   └── ... (edit modals, document layouts)
        ├── pages/
        │   ├── Login.tsx
        │   ├── Register.tsx
        │   ├── VerifyEmail.tsx
        │   ├── Dashboard.tsx (Root + Layout)
        │   ├── IdCardSection.tsx
        │   ├── AccessoriesSection.tsx
        │   ├── AttendanceSection.tsx
        │   ├── ResultSection.tsx (+ tabs/)
        │   ├── FinanceSection.tsx (+ tabs/)
        │   ├── UserManagement.tsx
        │   ├── AuditLogs.tsx
        │   ├── PinAttendance.tsx
        │   ├── teacher/
        │   │   ├── TeacherLayout.tsx
        │   │   ├── TeacherDashboard.tsx
        │   │   ├── WeeklyRoutine.tsx
        │   │   ├── HomeworkPage.tsx
        │   │   └── DiaryPage.tsx
        │   ├── parents/
        │   │   ├── ParentLayout.tsx
        │   │   ├── ParentDashboard.tsx
        │   │   ├── ParentAttendance.tsx
        │   │   ├── ParentFees.tsx
        │   │   ├── ParentResults.tsx
        │   │   ├── ParentHomework.tsx
        │   │   ├── ParentDiary.tsx
        │   │   ├── ParentRoutine.tsx
        │   │   ├── ParentExamRoutine.tsx
        │   │   └── ParentAnnouncements.tsx
        │   └── engagement/
        │       └── EngagementWidget.tsx
        └── test/
            ├── stores.test.ts
            ├── financeStore.test.ts
            ├── peopleStore.test.ts
            ├── academicStore.test.ts
            ├── validation.test.ts
            ├── financeReportPdf.test.ts
            ├── TransactionForm.test.tsx
            ├── LedgerTable.test.tsx
            ├── BalanceSummary.test.tsx
            └── setup.ts
```

---

## Root URL Routing

| Path | Target |
|------|--------|
| `/admin/` | Django admin |
| `/` | Redirects to `/admin/` |
| `/healthz/` | Simple health check (`{"status": "ok"}`) |
| `/health/` | DB health check (200 or 503) |
| `/api/wake-db/` | Admin-only Supabase cold-start wake |
| `/api/` | accounts, core, students, teachers, staff, books, results, attendance, parents, academic |
| `/api/finance/` | finance |
| `/api/engagement/` | engagement |
| `/api/ai/` | ai_query |
| `/api/m/` | teachers (mobile endpoints) |
| `/m/` | Redirects to frontend PWA |

---

## All 13 Backend Apps

---

### 1. `accounts` — Auth & User Management

**Models:**

| Model | Key Fields |
|-------|-----------|
| `User` (AbstractUser) | `id` (UUID PK), `email` (unique, USERNAME_FIELD), `name`, `role` (admin/teacher/accountant/super_viewer/viewer/parent), `email_verified`, `image`. No username. |
| `EmailVerification` | `user` (FK), `token` (unique), `expires_at`, `used` |
| `PasswordReset` | `user` (FK), `token` (unique), `expires_at`, `used` |

**Auth Classes:**
- `CookieJWTAuthentication` — reads JWT from `access_token` cookie or Authorization header
- `PinAuthentication` — for mobile; reads JWT with `pin_auth` claim

**Endpoints:**

| Method | Path | Purpose |
|--------|------|---------|
| POST | `auth/register/` | Register (first user becomes admin) |
| POST | `auth/login/` | Login (JWT via cookies) |
| POST | `auth/refresh/` | Refresh JWT |
| POST | `auth/logout/` | Logout |
| GET/PUT | `auth/me/` | Get/update current user |
| GET | `auth/get-session/` | Session check |
| POST | `auth/send-verification/` | Resend email verification |
| POST | `auth/verify-email/` | Verify email with token |
| POST | `auth/request-password-reset/` | Request password reset |
| POST | `auth/reset-password/` | Reset password with token |
| GET | `users/` | List all users |
| GET | `users/roles/` | List available roles |
| PUT | `users/<pk>/role/` | Update user role |
| DELETE | `users/<pk>/` | Delete user |

---

### 2. `core` — Shared Base Models

**Models:**

| Model | Key Fields |
|-------|-----------|
| `SchoolClass` | `name` (unique), `order` |
| `Subject` | `name`, `full_marks`, `order`, `school_class` (FK). Unique: `(name, school_class)` |
| `AcademicYear` | `name` (unique), `start_date`, `end_date`, `is_active` |
| `SchoolSetting` | `key` (unique), `value` (JSON) |
| `AuditLog` | `user_id`, `user_name`, `action`, `entity_type`, `entity_id`, `details` |
| `Category` | `type` (INCOME/EXPENSE), `name`. Unique: `(type, name)` |
| `Program` | `name` (unique), `active` |
| `StudentIdCounter` | Singleton — generates student ID prefix + sequence |

**Endpoints:**

| Method | Path | Purpose |
|--------|------|---------|
| GET/POST | `classes/` | List/create classes (with counts) |
| GET/PUT/DELETE | `classes/<pk>/` | Single class CRUD |
| POST | `classes/reorder/` | Reorder classes |
| POST | `classes/promote-all/` | Promote all students to next class |
| GET/POST | `classes/<id>/subjects/` | List/create subjects for a class |
| GET/PUT/DELETE | `subjects/<pk>/` | Single subject CRUD |
| GET/POST | `academic-years/` | List/create academic years |
| GET/PUT/DELETE | `academic-years/<pk>/` | CRUD |
| GET/PUT | `settings/` | Get/update school settings |
| GET | `setup/status/` | Check if initialized |
| POST | `setup/init/` | First-time setup (creates admin) |
| GET | `dashboard-summary/` | Dashboard counts (cached 60s) |
| GET | `audit/` | Read-only audit logs |
| GET/POST | `categories/` | CRUD categories |

**Services:**
- `promote_all()` / `_simple_promote()` — end-of-year student promotion
- `_parse_student_roll()`, `_generate_student_roll()` — roll ID generation

**Management Commands:** set_subject_order, migrate_photos, import_firebase_results, import_firebase, cleanup_test_data, backup_students

---

### 3. `students` — Student Management

**Model:**

| Field | Type |
|-------|------|
| `id` | UUID PK |
| `school_class` | FK SchoolClass (nullable) |
| `program` | FK Program (nullable) |
| `student_id` | Unique, auto-generated |
| `roll` | Integer |
| `session` | Char |
| `name` | Char |
| `father_name` | Char |
| `mother_name` | Char |
| `contact` | Char |
| `photo_path` | Char (Supabase storage) |
| `deleted_at` | DateTime (soft-delete) |
| `graduated_at` | DateTime |
| `created_at` | DateTime |

**Endpoints:**

| Method | Path | Purpose |
|--------|------|---------|
| GET/POST | `students/` | List/create |
| GET/PUT/DELETE | `students/<pk>/` | CRUD |
| GET | `students/<pk>/photo/` | Photo proxy |
| POST | `students/<pk>/graduate/` | Graduate |
| POST | `students/<pk>/ungraduate/` | Ungraduate |
| POST | `students/<pk>/restore/` | Restore soft-deleted |
| POST | `students/import/` | Bulk import |
| POST | `students/graduate_class/` | Graduate entire class |

---

### 4. `teachers` — Teacher Management

**Models:**

| Model | Key Fields |
|-------|-----------|
| `Teacher` | `user` (OneToOne User, nullable), `designation`, `name`, `email`, `contact`, `photo_path`, `pin` (hashed), `deleted_at` |
| `ClassTeacher` | `teacher` (FK), `school_class` (FK). Unique: `(teacher, school_class)` |
| `TeacherSubject` | `teacher` (FK), `subject` (FK), `school_class` (FK). Unique: `(teacher, subject, school_class)` |

**Endpoints:**

| Method | Path | Purpose |
|--------|------|---------|
| GET/POST | `teachers/` | List/create |
| GET/PUT/DELETE | `teachers/<pk>/` | CRUD |
| GET | `teachers/<pk>/photo/` | Photo |
| POST | `teachers/<pk>/restore/` | Restore |
| POST | `teachers/import/` | Bulk import |
| GET/POST | `teachers/<pk>/class_teacher/` | Assign/get class teacher |
| POST | `teachers/<pk>/remove_class_teacher/` | Remove class teacher |
| GET/POST | `teachers/<pk>/subject_assignment/` | Assign/get subject |
| POST | `teachers/<pk>/remove_subject/` | Remove subject |
| POST | `teachers/<pk>/set_pin/` | Set mobile PIN |

**Mobile Endpoints** (under `/api/m/`):

| Method | Path | Purpose |
|--------|------|---------|
| POST | `auth/pin/` | PIN login |
| POST | `auth/set-pin/` | Set PIN |
| GET | `teachers/` | List |
| GET | `students/` | Students by class |
| GET | `attendance/` | Get attendance |
| POST | `attendance/batch/` | Batch mark |
| GET | `attendance/class-daily-report/` | Daily report |
| GET | `attendance/monthly-report/` | Monthly report |

---

### 5. `staff` — Staff Management

**Model:**

| Field | Type |
|-------|------|
| `id` | UUID PK |
| `role` | Char |
| `name` | Char |
| `email` | Char |
| `contact` | Char |
| `photo_path` | Char |
| `deleted_at` | DateTime (soft-delete) |
| `created_at` | DateTime |

**Endpoints:** CRUD, photo, restore, bulk import.

---

### 6. `books` — Book Inventory

**Model:** `Book` — `name`, `publication`, `mrp` (Decimal), `discounted` (Decimal), `sell` (Decimal), `school_class` (FK). Constraints: all >= 0.

**Endpoints:** CRUD.

---

### 7. `results` — Exam Results (Draft/Publish)

**Model:**

| Field | Type |
|-------|------|
| `id` | UUID PK |
| `student` | FK Student (PROTECT) |
| `session` | Char |
| `term` | Char |
| `marks` | JSONField |
| `attendance` | JSONField (nullable) |
| `comment` | Text |
| `created_at` | DateTime |

**Endpoints:**

| Method | Path | Purpose |
|--------|------|---------|
| GET/POST | `results/` | List/create |
| GET/PUT/DELETE | `results/<pk>/` | CRUD |
| GET | `results/published_terms/` | Get published terms |
| POST | `results/publish_terms/` | Publish terms (push notification) |
| GET | `results/class_results/` | Results by class |
| DELETE | `results/delete_class_results/` | Delete class results |
| GET/POST | `students/<id>/results/` | Student-specific |
| GET/DELETE | `classes/<id>/results/` | Class-specific |

---

### 8. `attendance` — Attendance Tracking

**Models:**

| Model | Key Fields |
|-------|-----------|
| `Holiday` | `date` (unique), `name`, `type` (public/school) |
| `AttendanceRecord` | `student` (FK, PROTECT), `school_class` (FK), `date`, `term`, `session`, `status` (present/absent/late/excused), `marked_by` (FK User). Unique: `(student, date)` |

**Endpoints:**

| Method | Path | Purpose |
|--------|------|---------|
| GET | `attendance/` | List by class + date |
| POST | `attendance/batch/` | Batch mark (notifies parents on absent) |
| GET | `attendance/summary/` | Student summary |
| GET | `attendance/student/<id>/` | Monthly calendar |
| GET | `attendance/class-report/` | Class grid |
| GET | `attendance/class-daily-report/` | Daily report |
| GET | `attendance/all-classes-daily/` | All classes summary |
| GET | `attendance/monthly-report/` | Monthly report |
| GET/POST | `holidays/` | CRUD |

---

### 9. `finance` — Full Accounting & Fee Management

Full double-accounting system with transactions, fee schedules, bank accounts, ledger, reports, reconciliation, and period closes.

**Models:**

| Model | Key Fields |
|-------|-----------|
| `BankAccount` | `name` (unique, e.g. `AL_RAWA_BANK`, `GLOBAL_FORUM_BANK`, `CASH_IN_HAND`), `display_name`, `is_active` |
| `Transaction` | `transaction_type` (INCOME/EXPENSE/INTERNAL_TRANSFER), `source_account` (FK), `destination_account` (FK), `amount` (Decimal), `category`, `description`, `student` (FK), `class_name`, `fee_month`, `fiscal_year`, `is_cancelled`, `cancelled_at/by/reason`, `reversal_of_id`, `reference_id` (e.g. RCPT-2026-0001), `token_number`, `receipt_sequence`, `affects_income_ledger`, `affects_expense_ledger`, `created_by`, `approved_by` |
| `FeeSchedule` | `academic_year` (FK), `school_class` (FK, nullable), `category`, `amount`, `frequency` (MONTHLY/YEARLY/ONE_TIME), `applicability` (AUTO/ASSIGNED_ONLY), `effective_from/to` |
| `FeeWaiver` | `student` (FK), `fee_schedule` (FK), `type` (CUSTOM_AMOUNT/PERCENTAGE), `value`, `reason`, `approval_status` (pending/approved/rejected), `active`, `starts_at`, `ends_at` |
| `StudentFeeAssignment` | `student` (FK), `fee_schedule` (FK), `active`, `starts_at` (YYYY-MM), `ends_at` (YYYY-MM), `note` |
| `PaymentAllocation` | `transaction` (FK), `fee_schedule` (FK), `student` (FK), `period` (YYYY-MM), `amount` |
| `ReceiptCounter` | `fiscal_year`, `receipt_type` (RCPT/PV/TV/TOKEN), `next_sequence` |
| `OpeningBalance` | `fiscal_year`, `account` (FK), `amount`, `updated_by` |
| `OpeningBalanceHistory` | Tracks changes to opening balances with old/new amounts |
| `PeriodClose` | `fiscal_year` (unique), `closed_at`, `closed_by`, `notes` |
| `Reconciliation` | `account` (FK), `statement_date`, `closing_balance`, `system_balance`, `difference`, `status` (pending/matched/difference) |
| `AccountBalance` | `account` (FK), `fiscal_year`, `month`, `opening_balance`, `total_debits`, `total_credits`, `closing_balance` |
| `AccountBalance` | Per-account monthly cached balance snapshot |

**Endpoints** (all under `/api/finance/`):

| Method | Path | Purpose |
|--------|------|---------|
| GET/POST | `transactions/` | List/create transactions |
| GET/PUT/DELETE | `transactions/<pk>/` | Retrieve (update/delete raise error — immutable) |
| POST | `transactions/bulk/` | Bulk create with dedup |
| POST | `transactions/<pk>/cancel/` | Cancel + auto-reversal |
| GET | `transactions/balances/` | Current account balances |
| GET | `transactions/dashboard-summary/` | Dashboard (cached 60s) |
| GET | `transactions/ledger/` | Paginated ledger with running balance |
| GET | `transactions/fee-status/` | Fee status per student |
| GET | `transactions/defaulter/` | Defaulter report |
| GET/POST | `fee-schedules/` | CRUD |
| POST | `fee-schedules/copy_from_year/` | Copy to new academic year |
| GET/POST | `fee-waivers/` | CRUD |
| POST | `fee-waivers/<pk>/deactivate/` | Deactivate waiver |
| GET/POST | `student-fee-assignments/` | CRUD |
| POST | `student-fee-assignments/toggle/` | Toggle active |
| POST | `student-fee-assignments/bulk/` | Bulk assign to class |
| GET/POST | `opening-balances/` | CRUD with history tracking |
| GET | `opening-balances/history/` | Change history |
| POST | `opening-balances/revert/<history_pk>/` | Revert to historical |
| GET/POST | `period-closes/` | CRUD (locks fiscal year) |
| GET/POST | `reconciliations/` | CRUD with system balance |
| GET | `reports/agm/` | AGM financial report |
| GET | `reports/headwise/` | Income/expense by category |
| GET | `reports/monthly/` | Monthly breakdown |
| GET | `reports/audit/` | Full transaction list |
| GET | `reports/defaulter/` | Defaulter report |

**Logic & Features:**
- **Transactions are immutable** — no update, no delete. Cancel creates automatic reversal entry.
- **Auto-generated reference IDs**: `RCPT-{FY}-{seq}` (income), `PV-{FY}-{seq}` (expense), `TV-{FY}-{seq}` (transfer), `TOKEN-{FY}-{seq}` (token number)
- **Fee allocation** via `PaymentAllocation` — income transactions allocate payments across fee schedules
- **Waiver support** — `_waiver_expected_amount()` computes discounted amount (CUSTOM_AMOUNT = exact, PERCENTAGE = % off)
- **Period close** — `PeriodClose` locks all transactions for a fiscal year
- **Three bank accounts** tracked: AL_RAWA_BANK (primary), GLOBAL_FORUM_BANK (secondary), CASH_IN_HAND
- **Cross-bank transfers** are classified as INCOME/EXPENSE for reporting
- **Fiscal year**: starts September (FISCAL_YEAR_START_MONTH=8), year+1 for months > Aug
- **Parent notification** — income transactions trigger push notification to student's parents

**Services:**

| File | Class/Functions | Purpose |
|------|-----------------|---------|
| `transaction_service.py` | `create_transaction()` | Creates transaction with auto-allocation, receipt counter, waiver validation, parent notify |
| `ledger_service.py` | `LedgerService` | Paginated ledger with running balance + opening balance computation |
| `fee_status_service.py` | `FeeStatusService` | Per-student fee status: schedules, waivers, paid/unpaid months |
| `defaulter_service.py` | `DefaulterService` | Defaulter report with yearly/monthly breakdowns |

**Signals:**
- `sync_transaction_class_name` — logs student class changes (does not mutate transactions)
- `invalidate_internal_accounts_cache` — clears cached bank account list on BankAccount changes

---

### 10. `academic` — Academic Structure

**Models:**

| Model | Key Fields |
|-------|-----------|
| `RoutineTemplate` | `school_class` (FK), `section`, `day` (sun-sat), `period_number`, `subject` (FK), `teacher` (FK). Unique: `(class, section, day, period)` |
| `LessonPlan` | `routine_template` (FK), `week_start`, `topic`, `learning_objectives`, `activities`, `materials`, `assessment`, `remarks`, `completed` |
| `Homework` | `school_class` (FK), `section`, `subject` (FK), `teacher` (FK), `date`, `topic`, `description`, `due_date`, `published`, `attachment` |
| `Diary` | `school_class` (FK), `section`, `subject` (FK), `teacher` (FK), `date`, `topic`, `activities`, `remarks`, `attachment` |
| `ExamRoutine` | `exam_name`, `school_class` (FK), `section`, `subject` (FK), `date`, `start_time`, `end_time`, `room`. Unique: `(exam_name, class, section, subject)` |

**Endpoints:**

| Method | Path | Purpose |
|--------|------|---------|
| GET/POST | `academic/routine-templates/` | CRUD |
| GET/PUT/DELETE | `academic/routine-templates/<pk>/` | Single |
| POST | `academic/routine-templates/publish/` | Notify parents |
| GET/POST | `academic/exam-routines/` | CRUD |
| GET/PUT | `academic/period-settings/` | Period time settings |
| GET | `teacher/routine/week/` | Teacher's week |
| POST | `teacher/routine/lesson_plan/` | Save lesson plan |
| GET/POST | `teacher/homework/` | CRUD (push on publish) |
| GET/PUT/DELETE | `teacher/homework/<pk>/` | Single |
| GET/POST | `teacher/diary/` | CRUD (push) |
| GET/PUT/DELETE | `teacher/diary/<pk>/` | Single |
| GET | `teacher/dashboard/` | Teacher dashboard |
| GET | `parents/routine/` | Parent view |
| GET | `parents/homework/` | Parent view |
| GET | `parents/diary/` | Parent view |
| GET | `parents/exam-routine/` | Parent view |

---

### 11. `parents` — Parent Portal

**Models:**

| Model | Key Fields |
|-------|-----------|
| `ParentStudentLink` | `parent` (FK User, role=parent), `student` (FK Student). Unique: `(parent, student)` |
| `PushSubscription` | `user` (FK), `endpoint`, `p256dh_key`, `auth_key`, `user_agent` |
| `NotificationLog` | `user` (FK), `event_type`, `title`, `body`, `payload` (JSON) |
| `Announcement` | `author` (FK User, nullable), `title`, `body` |

**Endpoints:** All read-only for parents.

| Method | Path | Purpose |
|--------|------|---------|
| GET | `parents/my-students/` | Parent's linked students |
| GET | `parents/attendance/<id>/` | Student attendance |
| GET | `parents/fees/<id>/` | Fee status |
| GET | `parents/results/<id>/` | Published results |
| POST | `parents/push/subscribe/` | Subscribe |
| DELETE | `parents/push/subscribe/` | Unsubscribe |
| GET | `parents/push/vapid-key/` | Public VAPID key |
| GET/POST | `parents/announcements/` | List/create (with push) |
| GET/POST/DELETE | `parents/links/` | Admin CRUD links |

**Services:** `notify()`, `notify_parents_of_student()`, `notify_parents_of_class()`, `notify_all_parents()`

---

### 12. `engagement` — Gamification

**Models:**

| Model | Key Fields |
|-------|-----------|
| `DailyQuiz` | `question`, `option_a/b/c/d`, `correct_answer`, `category`, `quiz_date` (unique), `explanation` |
| `QuizResponse` | `user` (FK), `question` (FK), `selected_answer`, `is_correct`. Unique: `(user, question)` |
| `DailyRiddle` | `question`, `hint`, `answer`, `riddle_date` (unique) |
| `RiddleResponse` | `user` (FK), `riddle` (FK), `guess`, `is_correct`. Unique: `(user, riddle)` |
| `DailyTip` | `tip`, `category`, `tip_date`. Unique: `(tip_date, category)` |
| `WeeklyChallenge` | `title`, `description`, `challenge_type` (text/emoji), `is_active`, `start_date`, `end_date` |
| `ChallengeResponse` | `user` (FK), `challenge` (FK), `text/emoji_response`. Unique: `(user, challenge)` |
| `MoodCheckin` | `user` (FK), `mood` (1-5), `checkin_date`. Unique: `(user, checkin_date)` |
| `LessonPlan` | `user` (FK), `plan_date`, `class_name`, `subject`, `notes` |
| `TeacherStreak` | `user` (OneToOne), `current_streak`, `longest_streak`, `last_active_date`, `total_days_active` |

**Endpoints:**

| Method | Path | Purpose |
|--------|------|---------|
| GET | `quiz/today/` | Get/generate today's quiz |
| POST | `quiz/answer/` | Answer quiz |
| GET | `quiz/leaderboard/` | Leaderboard |
| GET | `riddle/today/` | Get/generate riddle |
| POST | `riddle/guess/` | Guess riddle |
| GET | `tips/today/` | Get daily tips |
| GET | `challenges/active/` | Active challenge |
| POST | `challenges/<pk>/respond/` | Respond |
| POST | `mood/checkin/` | Mood check-in |
| GET | `mood/history/` | History |
| GET | `mood/aggregate/` | Admin aggregate |
| GET/POST | `lesson-plans/` | CRUD |
| GET | `lesson-plans/week/` | This week |
| GET | `streak/me/` | My streak |
| POST | `admin/regenerate/` | Regenerate AI content |

**AI Service:** Falls back to stub content when AI provider unavailable. Functions: `generate_quiz()`, `generate_riddle()`, `generate_tip()`, `generate_challenge()`.

---

### 13. `ai_query` — Natural Language AI Query

**Model:** `AIQueryLog` — `user`, `query`, `function_called`, `arguments` (JSON), `confidence`, `execution_time_ms`, `result_count`, `success`, `error_message`.

**Endpoint:** `POST /api/ai/query/` — accepts natural language, returns structured result.

**Architecture:**
1. Registry pattern — `@ai_function` decorator registers handlers
2. `filter_functions_for_user()` — role-based filtering
3. `validate_and_score()` — validate arguments + compute confidence
4. `resolve_slots()` — resolve context from session memory
5. LLM call — sends function definitions to Gemini/OpenAI-compatible provider

**25 Registered Handlers:**

| Group | Handlers |
|-------|----------|
| Students (4) | `search_student`, `student_profile`, `class_list`, `student_count_by_class` |
| Teachers (4) | `teacher_search`, `teacher_subjects`, `teacher_schedule`, `class_teachers` |
| Attendance (3) | `attendance_summary`, `absent_today`, `attendance_detail` |
| Finance (5) | `fee_status`, `defaulter_report`, `ledger_query`, `fee_collected`, `balances` |
| Results (2) | `result_summary`, `result_detail` |
| Dashboard (1) | `dashboard_summary` |
| Academic (6) | `homework_by_class`, `diary_by_class`, `weekly_routine`, `exam_routine`, `lesson_plans` |

---

## Frontend Routes

| Route | Component | Portal |
|-------|-----------|--------|
| `/login` | `Login` | Auth |
| `/register` | `Register` | Auth |
| `/verify-email` | `VerifyEmail` | Auth |
| `/` | `Dashboard` → `Layout` + mode-based sections | Admin |
| `/users` | `UserManagement` | Admin |
| `/audit` | `AuditLogs` | Admin |
| `/pin-attendance` | `PinAttendance` | Admin |
| `/teacher` | `TeacherDashboard` | Teacher |
| `/teacher/routine` | `WeeklyRoutine` | Teacher |
| `/teacher/attendance` | `AttendanceSection` | Teacher |
| `/teacher/homework` | `HomeworkPage` | Teacher |
| `/teacher/diary` | `DiaryPage` | Teacher |
| `/parent` | `ParentDashboard` | Parent |
| `/parent/attendance/:id?` | `ParentAttendance` | Parent |
| `/parent/fees/:id?` | `ParentFees` | Parent |
| `/parent/results/:id?` | `ParentResults` | Parent |
| `/parent/homework` | `ParentHomework` | Parent |
| `/parent/diary` | `ParentDiary` | Parent |
| `/parent/routine` | `ParentRoutine` | Parent |
| `/parent/exam-routine` | `ParentExamRoutine` | Parent |
| `/parent/announcements` | `ParentAnnouncements` | Parent |

### Dashboard Mode Sections (inside Layout)

| Mode | Component | Tabs |
|------|-----------|------|
| `idcard` | `IdCardSection` | — |
| `accessories` | `AccessoriesSection` | — |
| `attendance` | `AttendanceSection` | — |
| `result` | `ResultSection` | EnterBySubject, EnterByStudent, Tabulation, AllReportCards, SubjectManager, PublishResults |
| `finance` | `FinanceSection` | Transactions, Reports, OptionalFees, ExcelImport, FeeSchedule, StudentWaivers, PeriodClose, Reconciliation, Defaulter |

---

## State Management (Zustand Stores)

| Store | Key Data | Key Actions |
|-------|----------|-------------|
| `useAuthStore` | `user`, `loading` | `login()`, `logout()`, `fetchSession()` |
| `useSchoolStore` | `classes`, `students`, `teachers`, `staff`, `books`, `subjects`, `transactions`, `balances`, `settings`, `feeSchedules`, `openingBalances`, `academicYears`, `classResults`, `expenseCategories`, `dashboardSummary` | All CRUD fetches + mutations, cache invalidation |
| `useUIStore` | `activeMode`, `activeSubMode` | `setMode()`, `swipeBack()` |
| `useDarkMode` | `dark` | `toggle()` |
| `useUserManagementStore` | `users`, `roles` | `fetchUsers()`, `updateRole()`, `deleteUser()` |
| `useAIQueryStore` | `open`, `query`, `loading`, `result`, `error` | `submit()`, `close()` |

---

## Shared UI Components

| Component | Purpose |
|-----------|---------|
| `Layout` | Main chrome: header, content, footer, BottomNav |
| `BottomNav` | Mobile bottom navigation (5 icons) |
| `Toast` | Global toast (success/error/info), `toast()` function |
| `Modal` | Portal-based with focus trap |
| `Skeleton` | Loading placeholders (table/card/text) |
| `ExportMenu` | CSV/Excel/PDF/Print dropdown |
| `ClassSelect` | Class dropdown |
| `DatePicker` | Date input |
| `PhotoUpload` | Photo with preview |
| `CameraModal` | Camera capture |
| `ImportModal` | Excel/CSV import |
| `PromoteModal` | Student promotion |
| `TransactionForm` | Financial transaction form |
| `LedgerTable` | Ledger data table |
| `BalanceSummary` | Account balances |
| `ErrorBoundary` | Class-based error boundary |
| `EmptyState` | Empty state illustration |
| `IOSInstallPrompt` | PWA install for iOS |

---

## AI Query System (Cmd+K Palette)

```
Cmd+K → AICommandPalette
         ├── Text input
         ├── Pre-defined suggestions (17 queries)
         ├── Recent history
         └── Submit → POST /api/ai/query/
                       ↓
                AIResultPanel
                 ├── AIResultTable (tabular data)
                 ├── AIResultSummary (text)
                 ├── Clarification prompt
                 └── Error display
```

---

## PDF Generation

| File | Functions |
|------|-----------|
| `lib/reportPdf.ts` | `downloadReportCardPDF()` — per-student report card |
| `lib/tabulationPdf.ts` | `tabulationPDF()` — class-wide tabulation sheet |
| `lib/financeReportPdf.ts` | `pdfIncomeReport()`, `pdfExpenseReport()`, `pdfAudit()`, `pdfYearlyAGM()`, `pdfLedger()` |
| `lib/defaulterPdf.ts` | `defaulterPDF()` — defaulter fee report |

---

## Security

| Measure | Detail |
|---------|--------|
| **Auth** | JWT access (15min) + refresh (7d) in HttpOnly cookies |
| **Cookie flags** | SameSite=None (prod), Secure=True (prod), HttpOnly=True |
| **CSRF** | Trusted origins from FRONTEND_URL |
| **CORS** | Credentials allowed, restricted origins |
| **HSTS** | 1 year, includeSubdomains, preload |
| **SSL** | Redirect enabled in production |
| **XSS** | `SECURE_BROWSER_XSS_FILTER = True` |
| **Clickjacking** | `X_FRAME_OPTIONS = 'DENY'` |
| **Content-Type** | `SECURE_CONTENT_TYPE_NOSNIFF = True` |
| **Throttling** | 10 rate limit scopes (login: 10/min, ai_query: 30/hr, etc.) |
| **Permissions** | String-based role system — `students:read`, `finance:write`, etc. |

---

## Role Permissions

| Role | Access |
|------|--------|
| `admin` | Full access — all permissions |
| `teacher` | Read + write students, results, academic |
| `accountant` | Finance read/write |
| `super_viewer` | Read-only everything |
| `viewer` | None |
| `parent` | Read students, results, academic (linked children only) |

Permission strings: `students:read`, `students:write`, `teachers:read`, `teachers:write`, `staff:read`, `staff:write`, `books:read`, `books:write`, `classes:read`, `classes:write`, `subjects:read`, `subjects:write`, `subjects:admin`, `results:read`, `results:write`, `results:admin`, `finance:read`, `finance:write`, `finance:admin`, `users:read`, `users:write`, `audit:read`, `academic-years:read`, `academic-years:write`, `academic:read`, `academic:write`, `academic:admin`.

---

## Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `DJANGO_SECRET_KEY` | **(required)** | Django secret |
| `DJANGO_DEBUG` | `False` | Debug mode |
| `DJANGO_ALLOWED_HOSTS` | `localhost,127.0.0.1` | Allowed hosts |
| `DB_NAME` | `postgres` | Database name |
| `DB_USER` | `postgres` | DB user |
| `DB_PASSWORD` | `postgres` | DB password |
| `DB_HOST` | `localhost` | DB host |
| `DB_PORT` | `5432` | DB port |
| `DB_SSLMODE` | `prefer` | PostgreSQL SSL mode |
| `FRONTEND_URL` | `http://localhost:5173` | Frontend origin |
| `CORS_ORIGINS` | `` | Extra allowed origins |
| `EMAIL_HOST_USER` | `` | Gmail SMTP user |
| `EMAIL_HOST_PASSWORD` | `` | Gmail app password |
| `DEFAULT_FROM_EMAIL` | falls back to EMAIL_HOST_USER | From address |
| `AI_PROVIDER` | `gemini` | AI provider |
| `AI_MODEL` | `` | Model ID |
| `AI_API_KEY` | `` | API key |
| `AI_API_BASE_URL` | `` | Custom base URL |
| `GEMINI_API_KEY` | `` | Gemini API key |
| `AI_CONFIDENCE_THRESHOLD` | `0.6` | Confidence threshold |
| `AI_QUERY_ENABLED` | `True` | Enable AI query |
| `VAPID_PUBLIC_KEY` | `` | Web Push public key |
| `VAPID_PRIVATE_KEY` | `` | Web Push private key |
| `VAPID_CLAIM_EMAIL` | `admin@alrawa.edu` | VAPID claim |
| `SUPABASE_URL` | `` | Supabase project URL |
| `SUPABASE_SERVICE_KEY` | `` | Supabase service key |
| `SUPABASE_BUCKET` | `` | Storage bucket |

---

## Deployment

### Backend (alwaysdata)
- Push: `git push deploy main:main`
- Auto-runs: pip install, migrate, collectstatic
- WSGI restart via Alwaysdata admin panel
- Gunicorn via Procfile

### Frontend (GitHub Pages)
- GitHub Actions on push to `origin main`
- Published at `https://inightelf.github.io/school.management.django/`

### Remotes
- `origin` = GitHub
- `deploy` = Alwaysdata

### Database
- PostgreSQL on Supabase (free tier — cold start)
- Wake: `GET /api/wake-db/` (admin-only)

---

## Key Conventions

- **UUID PKs** on all models
- **Soft delete** via `deleted_at` (Student, Teacher, Staff) — never hard-deleted
- **CamelCase JSON** — all API responses use camelCase via `CamelCaseModelSerializer`
- **No server-side templates** — Django is headless API only
- **HashRouter** on frontend (not BrowserRouter)
- **Tokens in memory** — access/refresh tokens stored in module-level variables, not localStorage
- **Lazy loading** — all route components via `React.lazy()`
- **Cache TTL** — 60s on dashboard, invalidated via Django signals
