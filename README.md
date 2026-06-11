# AL RAWA English School — Management System

A full-stack school management system with Django REST Framework backend and React + TypeScript frontend. Manages students, teachers, staff, finance, books, and exam results.

## Tech Stack

- **Backend:** Django 6 + DRF + JWT (simplejwt) + PostgreSQL
- **Frontend:** React 19 + TypeScript + Zustand + Vite + Tailwind CSS
- **Auth:** Email-based login with JWT (access + refresh tokens in HttpOnly cookies)
- **Deployment:** GitHub Pages (frontend) + alwaysdata (backend) + Supabase (PostgreSQL)

## Local Development

### Backend

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # fill in your credentials
python manage.py migrate
python manage.py runserver
```

### Frontend

```bash
cd client
npm install
npm run dev
```

Vite proxies `/api` to `localhost:8000` automatically.

### Run Tests

```bash
# Backend (141 tests, SQLite in-memory)
python manage.py test -v 2

# Frontend
cd client && npm test
```

## Environment Variables

Copy `.env.example` to `.env` and fill in:

| Variable | Description |
|----------|-------------|
| `DJANGO_SECRET_KEY` | Django secret key |
| `DJANGO_DEBUG` | `True` for dev, `False` for production |
| `DJANGO_ALLOWED_HOSTS` | Comma-separated allowed hosts |
| `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT` | PostgreSQL credentials |
| `CORS_ORIGINS` | Comma-separated allowed origins |
| `GEMINI_API_KEY` | Google Gemini API key (optional, for AI features) |

## Project Structure

```
├── school_management/     # Django project settings, root URLs, WSGI
├── accounts/              # Custom User model, JWT auth, email verification
├── core/                  # SchoolClass, AcademicYear, Subject, Categories
├── students/              # Student model (soft delete)
├── teachers/              # Teacher, ClassTeacher, TeacherSubject
├── staff/                 # Staff model
├── finance/               # Transactions, fees, bank accounts, reconciliation
├── books/                 # Book inventory
├── results/               # Exam results
├── engagement/            # AI-powered engagement analysis
├── client/                # React frontend
│   ├── src/pages/         # Feature sections (Finance, Students, Teachers, etc.)
│   ├── src/stores/        # Zustand state management
│   ├── src/components/    # Shared UI components
│   └── src/lib/           # Types, validation, config
└── manage.py
```

## API Conventions

- All endpoints under `/api/`
- Trailing slash required on all URLs (e.g., `/api/students/`)
- List responses: `{ count, results }` — fetch with `?limit=2000` for all
- `SlugRelatedField(slug_field='name')` — API accepts/returns names, not UUIDs
- JWT auth via `Authorization` header or `access_token` cookie

## Key Features

- **Students:** CRUD, bulk import (CSV), soft delete with undo, class assignments
- **Teachers:** CRUD, class teacher & subject assignments (permission-gated for result editing)
- **Finance:** Double-entry transactions, bank reconciliation, fee schedules, fee waivers, opening balances, period closing, financial reports with PDF export
- **Results:** Per-subject marks, class/term/session filtering, CSV import
- **Books:** Inventory management, sell price tracking
- **Dashboard:** Real-time summary (income, expenses, balances) with 60s cache
- **PDF Export:** Teacher lists, ID cards, defaulter reports, financial reports
- **Dark mode:** Full dark mode support across the UI

## License

Private — AL RAWA English School
