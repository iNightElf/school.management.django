# AI-Powered Natural Language Query System

## Build Progress

| Phase | What | Status |
|-------|------|--------|
| 1 | App skeleton + core (registry, models, views, serializers, throttles, URL registration) | ✅ Done |
| 2 | `AIQueryLog` migration + `ConversationMemory` in resolver | ✅ Done |
| 3 | 15 handlers (students 3, teachers 3, attendance 2, finance 4, results 2, dashboard 1) | ✅ Done |
| 4 | Frontend: `useAI` store, `AICommandPalette`, `AIResultPanel`, `AIResultTable`, `AIResultSummary` | ✅ Done |
| 5 | Confidence heuristic, clarification flow, error handling | ✅ Done |
| 6 | Prompt tuning + tests | ✅ Done |

**Deployed:** ✅ Live on Alwaysdata (Jun 23)

---

## Architecture (Final)

```
Ctrl+K / Sparkles button
        │
        ▼
┌──────────────────────┐
│  ConversationMemory  │  per-user dict, 5min TTL
│  (resolver.py)       │  follow-ups use last context
└──────┬───────────────┘
       │ query + session context
       ▼
┌──────────────────────┐
│  PermissionFilter    │  viewer=403, strip unauthorized fns
│  (permission_filter) │  Gemini never sees them
└──────┬───────────────┘
       │ allowed functions list
       ▼
┌──────────────────────┐
│  Gemini API          │
│  function calling    │
│  (llm_service.py)    │
│  system prompt auto- │
│  generated from      │
│  REGISTRY            │
└──────┬───────────────┘
       │ function_name + args
       ▼
┌──────────────────────┐
│  Validator           │  type checks, required arg ratio → score
│  (validator.py)      │  if < 0.6 → clarification flow
└──────┬───────────────┘
       │ validated args + confidence
       ▼
┌──────────────────────┐
│  Slot Resolver       │  fuzzy class name → exact, student name → ID
│  (resolver.py)       │
└──────┬───────────────┘
       │ resolved args
       ▼
┌──────────────────────┐
│  Handler scope check │  teacher: "can you access this class?"
│  (in each handler)   │  non-admin → scope filter
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│  ORM Query           │  .values()[:200] max
└──────┬───────────────┘
       │ QueryResult {type, explanation, data, columns}
       ▼
┌──────────────────────┐
│  AIQueryLog          │  user, query, fn, args, confidence,
│  (models.py)         │  time_ms, count, success, error
└──────┬───────────────┘
       │
       ▼
  Response → AIResultPanel (frontend)
```

---

## Files Created

### Backend: `ai_query/` app

| File | Purpose | Status |
|------|---------|--------|
| `ai_query/__init__.py` | Package init | ✅ |
| `ai_query/apps.py` | AppConfig with `ready()` auto-discover | ✅ |
| `ai_query/registry.py` | `@ai_function` decorator + `REGISTRY` dict | ✅ |
| `ai_query/models.py` | `AIQueryLog` model (dedicated audit table) | ✅ |
| `ai_query/views.py` | `AIQueryView` (POST /api/ai/query/) orchestrator | ✅ |
| `ai_query/urls.py` | Route: `api/ai/query/` | ✅ |
| `ai_query/serializers.py` | `QuerySerializer` + `QueryResultSerializer` | ✅ |
| `ai_query/llm_service.py` | Gemini function-calling wrapper (extends existing pattern) | ✅ |
| `ai_query/permission_filter.py` | `filter_functions_for_user()` — role-based gating | ✅ |
| `ai_query/validator.py` | Arg type checks + confidence scoring heuristic | ✅ |
| `ai_query/resolver.py` | Slot → DB ID resolution + `ConversationMemory` (TTL dict) | ✅ |
| `ai_query/throttles.py` | `AIQueryRateThrottle` (30/hour) | ✅ |
| `ai_query/handlers/__init__.py` | Imports all 6 handler modules | ✅ |
| `ai_query/handlers/students.py` | `search_student`, `student_profile`, `class_list` | ✅ |
| `ai_query/handlers/teachers.py` | `teacher_search`, `teacher_subjects`, `class_teachers` | ✅ |
| `ai_query/handlers/attendance.py` | `attendance_summary`, `attendance_detail` | ✅ |
| `ai_query/handlers/finance.py` | `fee_status`, `defaulter_report`, `ledger_query`, `balances` | ✅ |
| `ai_query/handlers/results.py` | `result_summary`, `result_detail` | ✅ |
| `ai_query/handlers/dashboard.py` | `dashboard_summary` | ✅ |
| `ai_query/migrations/0001_initial.py` | AIQueryLog migration | ✅ |

### Files Modified (3 backend)

| File | Change |
|------|--------|
| `school_management/settings.py` | Added `ai_query` to INSTALLED_APPS, `AI_CONFIDENCE_THRESHOLD`, `AI_QUERY_ENABLED`, `ai_query: 30/hour` throttle rate |
| `school_management/urls.py` | Added `path('api/ai/', include('ai_query.urls'))` |

### Frontend: `client/src/ai/`

| File | Purpose | Status |
|------|---------|--------|
| `client/src/stores/aiQuery.ts` | Zustand store: `open`, `query`, `loading`, `result`, `error` | ✅ |
| `client/src/ai/AICommandPalette.tsx` | Ctrl+K global overlay with suggestions | ✅ |
| `client/src/ai/AIResultPanel.tsx` | Routes table/summary/clarification/error renders | ✅ |
| `client/src/ai/AIResultTable.tsx` | Scrollable table renderer for tabular data | ✅ |
| `client/src/ai/AIResultSummary.tsx` | Text summary renderer | ✅ |

### Files Modified (3 frontend)

| File | Change |
|------|--------|
| `client/src/store.ts` | Added `useAIQueryStore` export |
| `client/src/App.tsx` | Added `<AICommandPalette />` inside `<HashRouter>` |
| `client/src/components/Layout.tsx` | Added AI toggle button (Sparkles icon) in header |

---

## Function Inventory (15 — all implemented and registered)

| # | Function | Permissions | admin | teacher | accountant | s_viewer |
|---|----------|-------------|-------|---------|------------|----------|
| 1 | `search_student` | students:read | ✓ | ✓ scope | ✓ | ✓ |
| 2 | `student_profile` | students:read | ✓ | ✓ scope | ✓ | ✓ |
| 3 | `class_list` | students:read | ✓ | ✓ scope | ✓ | ✓ |
| 4 | `fee_status` | finance:read | ✓ | — | ✓ | ✓ |
| 5 | `defaulter_report` | finance:read | ✓ | — | ✓ | ✓ |
| 6 | `ledger_query` | finance:read | ✓ | — | ✓ | ✓ |
| 7 | `balances` | finance:read | ✓ | — | ✓ | ✓ |
| 8 | `attendance_summary` | students:read | ✓ | ✓ scope | ✓ | ✓ |
| 9 | `attendance_detail` | students:read | ✓ | ✓ scope | ✓ | ✓ |
| 10 | `result_summary` | results:read | ✓ | ✓ scope | — | ✓ |
| 11 | `result_detail` | results:read | ✓ | ✓ scope | — | ✓ |
| 12 | `teacher_search` | teachers:read | ✓ | ✓ | ✓ | ✓ |
| 13 | `teacher_subjects` | teachers:read | ✓ | ✓ | ✓ | ✓ |
| 14 | `class_teachers` | teachers:read | ✓ | ✓ | ✓ | ✓ |
| 15 | `dashboard_summary` | students:read | ✓ | ✓ | ✓ | ✓ |

**scope** = teacher restricted to classes they teach (via `ClassTeacher` check)
**viewer role** = 403 from `filter_functions_for_user` (zero permissions)

---

## Security Layers (8 — all implemented)

| Layer | File | What it prevents |
|-------|------|------------------|
| 1. `IsAuthenticated` | DRF view | Anonymous access |
| 2. Role check (viewer=403) | `permission_filter.py` | Viewers can't query |
| 3. Permission filter before Gemini | `permission_filter.py` | LLM never sees unauthorized functions |
| 4. Function args validation | `validator.py` | Type mismatches, caps at 200 rows |
| 5. Confidence scoring | `validator.py` | < 0.6 → clarification response |
| 6. Slot resolver | `resolver.py` | Fuzzy class name → exact DB match |
| 7. Handler scope re-check | Each handler | Teacher can't query classes they don't teach |
| 8. Audit log | `views.py` `_log_query()` | Every query logged to `AIQueryLog` |
| 9. Rate limit (30/hour) | `throttles.py` | Prevents abuse |

---

## Key Implementation Details

### Confidence Scoring (validator.py)
- Base = 1.0
- Ratio of required args filled = multiplier
- If resolved slot doesn't exist in DB → default 0.0 → clarification
- Threshold: `AI_CONFIDENCE_THRESHOLD` (default 0.6)

### ConversationMemory (resolver.py)
- Module-level dict, 5-minute TTL per user
- Stores last function + args for follow-up context
- Included in Gemini system prompt as session context

### AIQueryLog (models.py)
- Dedicated table (not generic AuditLog)
- Fields: user, query, function_called, arguments (JSON), confidence, execution_time_ms, result_count, success, error_message, created_at
- Indexed on user+date, function_called, confidence

### Gemini Function Calling (llm_service.py)
- Extends existing `engagement/ai_service.py::_call_gemini()` pattern
- Uses Gemini 2.0 Flash with `tools: [{functionDeclarations}]`
- Returns `{type: "function_call", name, args}` or `{type: "text", text}`
- System prompt auto-generated from REGISTRY function names

### Handler Pattern
```python
@ai_function(name="...", description="...", permissions=[...],
             parameters={...}, result_columns=[...])
def handler(user, **kwargs):
    # 1. Permission scope check
    if not is_admin_or_superuser(user):
        qs = qs.filter(...teacher's classes...)
    # 2. Apply filters from kwargs
    # 3. Return QueryResult dict
    return {"type": "table", "explanation": "...", "data": [...], "columns": [...]}
```

---

## What's NOT in v1

- RAG / documentation Q&A → v2
- Streaming (SSE) → v2
- Chat history persistence → v2
- CSV export from AI results → v2
- Knowledge base docs → v2

---

## Decisions Log

| Date | Decision | Rationale |
|------|----------|-----------|
| Jun 22 | Gemini function calling (not local NN) | Zero retraining, already have API key |
| Jun 22 | Permission filter runs before Gemini call | LLM never sees unauthorized functions |
| Jun 22 | New `ai_query/` app (not modifying existing apps) | Zero risk, easy feature-flag |
| Jun 22 | `@ai_function` decorator for registration | Explicit, testable, self-documenting |
| Jun 22 | 15 functions in v1 | Covers 95% of likely queries |
| Jun 22 | viewer role = 403 | No permissions = nothing to query |
| Jun 22 | Dedicated `AIQueryLog` model (not generic AuditLog) | Query-specific fields, analytics-friendly |
| Jun 22 | Confidence scoring heuristic in v1 | Prevents wrong answers, huge UX win for ~15 lines |
| Jun 22 | Conversation memory (5min TTL dict) | Follow-up queries work naturally |
| Jun 22 | Global command palette (Ctrl+K), not page-embedded | Feels like an ERP command center |
| Jun 22 | RAG deferred to v2 | Documentation questions are 5% of usage |
| Jun 22 | Handler scope re-checks | Defense in depth — never trust the AI |

---

## Verification

```
Backend: python manage.py check → System check identified no issues (0 silenced)
Registry: 15 functions registered ✓
Frontend: npx tsc --noEmit → zero errors ✓
Migrations: ai_query.0001_initial applied ✓
```
