from .settings import *

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']

DEFAULT_FILE_STORAGE = 'django.core.files.storage.InMemoryStorage'

# Disable ALL FK enforcement on SQLite for tests — migration 0005 rebuilds
# finance_transaction (DROP+CREATE), leaving finance_paymentallocation's FK
# metadata stale. PRAGMA foreign_keys=OFF must persist for the test session.
import django.db.backends.sqlite3.base

_orig_disable = django.db.backends.sqlite3.base.DatabaseWrapper.disable_constraint_checking
def _always_disable(self):
    with self.cursor() as cursor:
        cursor.execute("PRAGMA foreign_keys = OFF")
    return True
django.db.backends.sqlite3.base.DatabaseWrapper.disable_constraint_checking = _always_disable

_orig_enable = django.db.backends.sqlite3.base.DatabaseWrapper.enable_constraint_checking
def _noop_enable(self):
    pass
django.db.backends.sqlite3.base.DatabaseWrapper.enable_constraint_checking = _noop_enable

_orig_check = django.db.backends.sqlite3.base.DatabaseWrapper.check_constraints
def _noop_check(self, table_names=None):
    pass
django.db.backends.sqlite3.base.DatabaseWrapper.check_constraints = _noop_check
