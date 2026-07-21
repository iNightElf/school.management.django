# Test-only settings override.
#
# Parity-first: if DB_* env vars are set (e.g. local Postgres or Docker Compose),
# the suite runs against REAL Postgres — this is what actually catches prod bugs.
# Only if no DB_* vars are present does it fall back to in-memory SQLite
# (e.g. in a CI sandbox with no database available).
#
# Usage:
#   manage.py test --settings=test_settings            # uses DB_* env (Postgres)
#   DB_NAME=... DB_USER=... manage.py test --settings=test_settings
import os

from school_management.settings import *  # noqa: F401,F403

if os.environ.get('DB_NAME') and os.environ.get('DB_HOST'):
    # Use the real database config from the base settings (already built from env).
    pass  # DATABASES is already correct from the imported settings.
else:
    # Fallback: in-memory SQLite when no database is reachable.
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': ':memory:',
        }
    }

# Avoid hitting the real email infra during tests.
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
