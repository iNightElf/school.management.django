
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

## Deployment

See `PRIVATE_APP_INFO.md` for full details.

- **Frontend:** GitHub Actions → GitHub Pages (`https://inightelf.github.io/school.management.django/`). Push to `origin main`, Actions auto-deploy if build passes.
- **Backend:** Alwaysdata via `git push deploy main:main` (auto-runs `pip install`, `migrate`, `collectstatic`). WSGI restart: `touch /home/ares/school_management.wsgi`.
- **Remotes:** `origin` = GitHub, `deploy` = Alwaysdata.
- **SSH:** `ares_ssh@ssh-ares.alwaysdata.net`
- **DB:** PostgreSQL on Supabase (cold-starts after inactivity → hit `/api/wake-db/`).
- **Env:** `.env` file on server. After updating it, touch WSGI to reload.

## Active Feature: AI Natural Language Query

See `AI_QUERY_FEATURE.md` for full design, status, and build order.

- Architecture: `AIProvider` abstraction in `ai_query/provider.py`
  - `GeminiProvider` — Google Gemini API
  - `OpenAICompatibleProvider` — DeepSeek, OpenRouter, etc.
  - Switched via `AI_PROVIDER` env var ('gemini' | 'openai')
- New `ai_query/` Django app (additive, no existing code changes)
- 15 functions in v1, permission-filtered before LLM call
- Frontend: `client/src/ai/` (4 components + Zustand store)
- Bandwidth: ~2MB/month at 1000 queries (negligible)
