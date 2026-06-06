from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('finance', '0005_normalize_accounts_to_fk'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                # Remove old index names from state (were dropped from DB by
                # RemoveField in 0005, but state incorrectly retained them)
                migrations.RemoveIndex(
                    model_name='openingbalancehistory',
                    name='finance_ope_fiscal__d289b8_idx',
                ),
                migrations.RemoveIndex(
                    model_name='reconciliation',
                    name='finance_rec_account_ce4995_idx',
                ),
                migrations.RemoveIndex(
                    model_name='transaction',
                    name='finance_tra_transac_dd6ada_idx',
                ),
                # Add indexes with correct auto-generated names for FK fields
                migrations.AddIndex(
                    model_name='openingbalancehistory',
                    index=models.Index(
                        fields=['fiscal_year', 'account'],
                        name='finance_ope_fiscal__200b6b_idx',
                    ),
                ),
                migrations.AddIndex(
                    model_name='reconciliation',
                    index=models.Index(
                        fields=['account'],
                        name='finance_rec_account_4e8a1b_idx',
                    ),
                ),
                migrations.AddIndex(
                    model_name='transaction',
                    index=models.Index(
                        fields=['transaction_date', 'source_account', 'destination_account'],
                        name='finance_tra_transac_ccf7be_idx',
                    ),
                ),
            ],
            database_operations=[
                # Indexes were already dropped from DB by RemoveField in 0005,
                # so we only need to CREATE the new ones.
                # PostgreSQL: CREATE INDEX CONCURRENTLY not needed in a
                # migration context.
                migrations.RunSQL(
                    "CREATE INDEX finance_ope_fiscal__200b6b_idx "
                    "ON finance_openingbalancehistory (fiscal_year, account_id)",
                    migrations.RunSQL.noop,
                ),
                migrations.RunSQL(
                    "CREATE INDEX finance_rec_account_4e8a1b_idx "
                    "ON finance_reconciliation (account_id)",
                    migrations.RunSQL.noop,
                ),
                migrations.RunSQL(
                    "CREATE INDEX finance_tra_transac_ccf7be_idx "
                    "ON finance_transaction (transaction_date, source_account_id, destination_account_id)",
                    migrations.RunSQL.noop,
                ),
            ],
        ),
    ]
