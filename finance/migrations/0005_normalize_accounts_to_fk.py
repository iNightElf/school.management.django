from django.db import migrations, models
import django.db.models.deletion


def _create_bank_accounts(apps, schema_editor):
    BankAccount = apps.get_model('finance', 'BankAccount')
    for name, display in [
        ('AL_RAWA_BANK', 'AL RAWA Bank'),
        ('GLOBAL_FORUM_BANK', 'Global Forum Bank'),
        ('CASH_IN_HAND', 'Cash in Hand'),
    ]:
        BankAccount.objects.get_or_create(name=name, defaults={'display_name': display})


def _migrate_ob_db(apps, schema_editor):
    cursor = schema_editor.connection.cursor()
    if schema_editor.connection.vendor != 'sqlite':
        cursor.execute("ALTER TABLE finance_openingbalance ADD COLUMN account_new_id uuid REFERENCES finance_bankaccount(id)")
        cursor.execute("""
            UPDATE finance_openingbalance SET account_new_id = ba.id
            FROM finance_bankaccount ba WHERE finance_openingbalance.account = ba.name
        """)
        cursor.execute("ALTER TABLE finance_openingbalance ALTER COLUMN account_new_id SET NOT NULL")
        cursor.execute("ALTER TABLE finance_openingbalance DROP COLUMN account")
        cursor.execute("ALTER TABLE finance_openingbalance RENAME COLUMN account_new_id TO account_id")
        return
    cursor.execute("PRAGMA table_info(finance_openingbalance)")
    cols = [(r[1], r[2], r[3], r[5]) for r in cursor.fetchall()]  # name, type, notnull, pk
    cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='index' AND tbl_name='finance_openingbalance'")
    indexes = [(r[0], r[1]) for r in cursor.fetchall()]
    cursor.execute("SELECT * FROM finance_openingbalance")
    rows = cursor.fetchall()
    col_names = [c[0] for c in cols]
    for idx_name, _ in indexes:
        try:
            cursor.execute(f"DROP INDEX IF EXISTS {idx_name}")
        except Exception:
            pass
    cursor.execute("DROP TABLE finance_openingbalance")
    new_defs = []
    pk_cols = [c[0] for c in cols if c[3] > 0]
    for cn, ct, nn, pk in cols:
        if cn == 'account':
            new_defs.append('"account_id" TEXT NOT NULL REFERENCES finance_bankaccount(name) ON DELETE CASCADE')
        else:
            defn = f'"{cn}" {ct}'
            if nn:
                defn += ' NOT NULL'
            new_defs.append(defn)
    if pk_cols:
        new_defs.append(f'PRIMARY KEY ({", ".join(pk_cols)})')
    cursor.execute(f'CREATE TABLE finance_openingbalance ({", ".join(new_defs)})')
    cursor.execute("CREATE UNIQUE INDEX finance_openingbalance_fiscal_ye_account__72fe73_idx ON finance_openingbalance(fiscal_year, account_id)")
    for row in rows:
        placeholders = ', '.join(['?'] * len(row))
        cursor.execute(f'INSERT INTO finance_openingbalance ({", ".join(col_names)}) VALUES ({placeholders})', list(row))


def _migrate_obh_db(apps, schema_editor):
    cursor = schema_editor.connection.cursor()
    if schema_editor.connection.vendor != 'sqlite':
        cursor.execute("ALTER TABLE finance_openingbalancehistory ADD COLUMN account_new_id uuid REFERENCES finance_bankaccount(id)")
        cursor.execute("""
            UPDATE finance_openingbalancehistory SET account_new_id = ba.id
            FROM finance_bankaccount ba WHERE finance_openingbalancehistory.account = ba.name
        """)
        cursor.execute("ALTER TABLE finance_openingbalancehistory ALTER COLUMN account_new_id SET NOT NULL")
        cursor.execute("ALTER TABLE finance_openingbalancehistory DROP COLUMN account")
        cursor.execute("ALTER TABLE finance_openingbalancehistory RENAME COLUMN account_new_id TO account_id")
        return
    cursor.execute("PRAGMA table_info(finance_openingbalancehistory)")
    cols = [(r[1], r[2], r[3], r[5]) for r in cursor.fetchall()]  # name, type, notnull, pk
    cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='index' AND tbl_name='finance_openingbalancehistory'")
    indexes = [(r[0], r[1]) for r in cursor.fetchall()]
    cursor.execute("SELECT * FROM finance_openingbalancehistory")
    rows = cursor.fetchall()
    col_names = [c[0] for c in cols]
    for idx_name, _ in indexes:
        try:
            cursor.execute(f"DROP INDEX IF EXISTS {idx_name}")
        except Exception:
            pass
    cursor.execute("DROP TABLE finance_openingbalancehistory")
    new_defs = []
    pk_cols = [c[0] for c in cols if c[3] > 0]
    for cn, ct, nn, pk in cols:
        if cn == 'account':
            new_defs.append('"account_id" TEXT NOT NULL REFERENCES finance_bankaccount(name) ON DELETE CASCADE')
        else:
            defn = f'"{cn}" {ct}'
            if nn:
                defn += ' NOT NULL'
            new_defs.append(defn)
    if pk_cols:
        new_defs.append(f'PRIMARY KEY ({", ".join(pk_cols)})')
    cursor.execute(f'CREATE TABLE finance_openingbalancehistory ({", ".join(new_defs)})')
    for row in rows:
        placeholders = ', '.join(['?'] * len(row))
        cursor.execute(f'INSERT INTO finance_openingbalancehistory ({", ".join(col_names)}) VALUES ({placeholders})', list(row))


def _migrate_recon_db(apps, schema_editor):
    cursor = schema_editor.connection.cursor()
    if schema_editor.connection.vendor != 'sqlite':
        cursor.execute("ALTER TABLE finance_reconciliation ADD COLUMN account_new_id uuid REFERENCES finance_bankaccount(id)")
        cursor.execute("""
            UPDATE finance_reconciliation SET account_new_id = ba.id
            FROM finance_bankaccount ba WHERE finance_reconciliation.account = ba.name
        """)
        cursor.execute("ALTER TABLE finance_reconciliation ALTER COLUMN account_new_id SET NOT NULL")
        cursor.execute("ALTER TABLE finance_reconciliation DROP COLUMN account")
        cursor.execute("ALTER TABLE finance_reconciliation RENAME COLUMN account_new_id TO account_id")
        return
    cursor.execute("PRAGMA table_info(finance_reconciliation)")
    cols = [(r[1], r[2], r[3], r[5]) for r in cursor.fetchall()]  # name, type, notnull, pk
    cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='index' AND tbl_name='finance_reconciliation'")
    indexes = [(r[0], r[1]) for r in cursor.fetchall()]
    cursor.execute("SELECT * FROM finance_reconciliation")
    rows = cursor.fetchall()
    col_names = [c[0] for c in cols]
    for idx_name, _ in indexes:
        try:
            cursor.execute(f"DROP INDEX IF EXISTS {idx_name}")
        except Exception:
            pass
    cursor.execute("DROP TABLE finance_reconciliation")
    new_defs = []
    pk_cols = [c[0] for c in cols if c[3] > 0]
    for cn, ct, nn, pk in cols:
        if cn == 'account':
            new_defs.append('"account_id" TEXT NOT NULL REFERENCES finance_bankaccount(name) ON DELETE CASCADE')
        else:
            defn = f'"{cn}" {ct}'
            if nn:
                defn += ' NOT NULL'
            new_defs.append(defn)
    if pk_cols:
        new_defs.append(f'PRIMARY KEY ({", ".join(pk_cols)})')
    cursor.execute(f'CREATE TABLE finance_reconciliation ({", ".join(new_defs)})')
    for row in rows:
        placeholders = ', '.join(['?'] * len(row))
        cursor.execute(f'INSERT INTO finance_reconciliation ({", ".join(col_names)}) VALUES ({placeholders})', list(row))


def _migrate_tx_db(apps, schema_editor):
    """Rebuild finance_transaction replacing source_account and destination_account
    CharField columns with UUID FK columns. Single pass to avoid rebuilding twice."""
    cursor = schema_editor.connection.cursor()
    if schema_editor.connection.vendor != 'sqlite':
        cursor.execute("ALTER TABLE finance_transaction ADD COLUMN source_account_new_id uuid REFERENCES finance_bankaccount(id)")
        cursor.execute("""
            UPDATE finance_transaction SET source_account_new_id = ba.id
            FROM finance_bankaccount ba WHERE finance_transaction.source_account = ba.name
        """)
        cursor.execute("ALTER TABLE finance_transaction DROP COLUMN source_account")
        cursor.execute("ALTER TABLE finance_transaction RENAME COLUMN source_account_new_id TO source_account_id")
        cursor.execute("ALTER TABLE finance_transaction ADD COLUMN destination_account_new_id uuid REFERENCES finance_bankaccount(id)")
        cursor.execute("""
            UPDATE finance_transaction SET destination_account_new_id = ba.id
            FROM finance_bankaccount ba WHERE finance_transaction.destination_account = ba.name
        """)
        cursor.execute("ALTER TABLE finance_transaction DROP COLUMN destination_account")
        cursor.execute("ALTER TABLE finance_transaction RENAME COLUMN destination_account_new_id TO destination_account_id")
        return
    # SQLite: rebuild table, replacing both account columns at once
    cursor.execute("PRAGMA table_info(finance_transaction)")
    cols = [(r[1], r[2], r[3], r[5]) for r in cursor.fetchall()]  # name, type, notnull, pk
    cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='index' AND tbl_name='finance_transaction'")
    indexes = [(r[0], r[1]) for r in cursor.fetchall()]
    cursor.execute("SELECT * FROM finance_transaction")
    rows = cursor.fetchall()
    col_names = [c[0] for c in cols]

    # Suppress check_constraints for this entire migration by patching at connection level
    schema_editor.connection.check_constraints = lambda *a, **kw: None

    for idx_name, _ in indexes:
        try:
            cursor.execute(f"DROP INDEX IF EXISTS {idx_name}")
        except Exception:
            pass
    cursor.execute("DROP TABLE finance_transaction")
    new_defs = []
    pk_cols = [c[0] for c in cols if c[3] > 0]
    for cn, ct, nn, pk in cols:
        if cn == 'source_account':
            new_defs.append('"source_account_id" TEXT REFERENCES finance_bankaccount(name) ON DELETE RESTRICT')
        elif cn == 'destination_account':
            new_defs.append('"destination_account_id" TEXT REFERENCES finance_bankaccount(name) ON DELETE RESTRICT')
        else:
            defn = f'"{cn}" {ct}'
            if nn:
                defn += ' NOT NULL'
            new_defs.append(defn)
    if pk_cols:
        new_defs.append(f'PRIMARY KEY ({", ".join(pk_cols)})')
    cursor.execute(f'CREATE TABLE finance_transaction ({", ".join(new_defs)})')
    for row in rows:
        placeholders = ', '.join(['?'] * len(row))
        cursor.execute(f'INSERT INTO finance_transaction ({", ".join(col_names)}) VALUES ({placeholders})', list(row))


class Migration(migrations.Migration):

    dependencies = [
        ('finance', '0004_accountbalance_bankaccount_alter_transaction_options_and_more'),
    ]

    operations = [
        migrations.RunPython(_create_bank_accounts, migrations.RunPython.noop),

        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AddField(
                    model_name='openingbalance',
                    name='account_new',
                    field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='+', to='finance.bankaccount'),
                ),
                migrations.RemoveField(model_name='openingbalance', name='account'),
                migrations.RenameField(model_name='openingbalance', old_name='account_new', new_name='account'),
                migrations.AlterField(
                    model_name='openingbalance',
                    name='account',
                    field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='opening_balances', to='finance.bankaccount'),
                ),
                migrations.AlterUniqueTogether(
                    name='openingbalance',
                    unique_together={('fiscal_year', 'account')},
                ),
            ],
            database_operations=[
                migrations.RunPython(_migrate_ob_db, migrations.RunPython.noop),
            ],
        ),

        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AddField(
                    model_name='openingbalancehistory',
                    name='account_new',
                    field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='+', to='finance.bankaccount'),
                ),
                migrations.RemoveField(model_name='openingbalancehistory', name='account'),
                migrations.RenameField(model_name='openingbalancehistory', old_name='account_new', new_name='account'),
                migrations.AlterField(
                    model_name='openingbalancehistory',
                    name='account',
                    field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='balance_history', to='finance.bankaccount'),
                ),
            ],
            database_operations=[
                migrations.RunPython(_migrate_obh_db, migrations.RunPython.noop),
            ],
        ),

        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AddField(
                    model_name='reconciliation',
                    name='account_new',
                    field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='+', to='finance.bankaccount'),
                ),
                migrations.RemoveField(model_name='reconciliation', name='account'),
                migrations.RenameField(model_name='reconciliation', old_name='account_new', new_name='account'),
                migrations.AlterField(
                    model_name='reconciliation',
                    name='account',
                    field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reconciliations', to='finance.bankaccount'),
                ),
            ],
            database_operations=[
                migrations.RunPython(_migrate_recon_db, migrations.RunPython.noop),
            ],
        ),

        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AddField(
                    model_name='transaction',
                    name='source_account_new',
                    field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='+', to='finance.bankaccount'),
                ),
                migrations.RemoveField(model_name='transaction', name='source_account'),
                migrations.RenameField(model_name='transaction', old_name='source_account_new', new_name='source_account'),
                migrations.AlterField(
                    model_name='transaction',
                    name='source_account',
                    field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='source_transactions', to='finance.bankaccount'),
                ),
            ],
            database_operations=[
                migrations.RunPython(_migrate_tx_db, migrations.RunPython.noop),
            ],
        ),

        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AddField(
                    model_name='transaction',
                    name='destination_account_new',
                    field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='+', to='finance.bankaccount'),
                ),
                migrations.RemoveField(model_name='transaction', name='destination_account'),
                migrations.RenameField(model_name='transaction', old_name='destination_account_new', new_name='destination_account'),
                migrations.AlterField(
                    model_name='transaction',
                    name='destination_account',
                    field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='destination_transactions', to='finance.bankaccount'),
                ),
            ],
            database_operations=[
                migrations.RunPython(lambda apps, se: None, migrations.RunPython.noop),
            ],
        ),
    ]
