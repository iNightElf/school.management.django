from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('finance', '0007_transaction_finance_tra_is_canc_3aa585_idx_and_more'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                # Remove redundant FK duplicate indexes from state
                migrations.RemoveIndex(model_name='feewaiver', name='finance_fee_student_9dd6de_idx'),
                migrations.RemoveIndex(model_name='feewaiver', name='finance_fee_fee_sch_633846_idx'),
                migrations.RemoveIndex(model_name='studentfeeassignment', name='finance_stu_student_1171ec_idx'),
                migrations.RemoveIndex(model_name='studentfeeassignment', name='finance_stu_fee_sch_995361_idx'),
                migrations.RemoveIndex(model_name='paymentallocation', name='finance_pay_transac_2ab2b1_idx'),
                migrations.RemoveIndex(model_name='paymentallocation', name='finance_pay_fee_sch_086134_idx'),
                migrations.RemoveIndex(model_name='reconciliation', name='finance_rec_account_4e8a1b_idx'),
                migrations.RemoveIndex(model_name='accountbalance', name='finance_acc_account_cda07a_idx'),
                # Remove redundant Transaction indexes from state
                migrations.RemoveIndex(model_name='transaction', name='finance_tra_student_764438_idx'),
                migrations.RemoveIndex(model_name='transaction', name='finance_tra_class_n_243748_idx'),
                migrations.RemoveIndex(model_name='transaction', name='finance_tra_reversa_83ed13_idx'),
                migrations.RemoveIndex(model_name='transaction', name='finance_tra_transac_ccf7be_idx'),
                migrations.RemoveIndex(model_name='transaction', name='finance_tra_is_canc_3aa585_idx'),
                # Remove deprecated unique_together from state (already gone from DB)
                migrations.AlterUniqueTogether(name='accountbalance', unique_together=set()),
                migrations.AlterUniqueTogether(name='feewaiver', unique_together=set()),
                migrations.AlterUniqueTogether(name='openingbalance', unique_together=set()),
                migrations.AlterUniqueTogether(name='receiptcounter', unique_together=set()),
                # Add new UniqueConstraints to state
                migrations.AddConstraint(
                    model_name='accountbalance',
                    constraint=models.UniqueConstraint(fields=['account', 'fiscal_year', 'month'], name='unique_account_balance'),
                ),
                migrations.AddConstraint(
                    model_name='feewaiver',
                    constraint=models.UniqueConstraint(fields=['student', 'fee_schedule'], name='unique_waiver_per_student_schedule'),
                ),
                migrations.AddConstraint(
                    model_name='openingbalance',
                    constraint=models.UniqueConstraint(fields=['fiscal_year', 'account'], name='unique_opening_balance'),
                ),
                migrations.AddConstraint(
                    model_name='receiptcounter',
                    constraint=models.UniqueConstraint(fields=['fiscal_year', 'receipt_type'], name='unique_receipt_counter'),
                ),
                # Add new Transaction report index to state
                migrations.AddIndex(
                    model_name='transaction',
                    index=models.Index(fields=['is_cancelled', 'fiscal_year', 'transaction_type'], name='tx_report_idx'),
                ),
            ],
            database_operations=[
                # Drop redundant FK indexes from DB
                migrations.RunSQL("DROP INDEX IF EXISTS finance_fee_student_9dd6de_idx", migrations.RunSQL.noop),
                migrations.RunSQL("DROP INDEX IF EXISTS finance_fee_fee_sch_633846_idx", migrations.RunSQL.noop),
                migrations.RunSQL("DROP INDEX IF EXISTS finance_stu_student_1171ec_idx", migrations.RunSQL.noop),
                migrations.RunSQL("DROP INDEX IF EXISTS finance_stu_fee_sch_995361_idx", migrations.RunSQL.noop),
                migrations.RunSQL("DROP INDEX IF EXISTS finance_pay_transac_2ab2b1_idx", migrations.RunSQL.noop),
                migrations.RunSQL("DROP INDEX IF EXISTS finance_pay_fee_sch_086134_idx", migrations.RunSQL.noop),
                migrations.RunSQL("DROP INDEX IF EXISTS finance_rec_account_4e8a1b_idx", migrations.RunSQL.noop),
                migrations.RunSQL("DROP INDEX IF EXISTS finance_acc_account_cda07a_idx", migrations.RunSQL.noop),
                # Drop redundant Transaction indexes from DB
                migrations.RunSQL("DROP INDEX IF EXISTS finance_tra_student_764438_idx", migrations.RunSQL.noop),
                migrations.RunSQL("DROP INDEX IF EXISTS finance_tra_class_n_243748_idx", migrations.RunSQL.noop),
                migrations.RunSQL("DROP INDEX IF EXISTS finance_tra_reversa_83ed13_idx", migrations.RunSQL.noop),
                migrations.RunSQL("DROP INDEX IF EXISTS finance_tra_transac_ccf7be_idx", migrations.RunSQL.noop),
                migrations.RunSQL("DROP INDEX IF EXISTS finance_tra_is_canc_3aa585_idx", migrations.RunSQL.noop),
                # Add new report index to DB
                migrations.RunSQL(
                    "CREATE INDEX tx_report_idx ON finance_transaction (is_cancelled, fiscal_year, transaction_type)",
                    migrations.RunSQL.noop,
                ),
            ],
        ),
    ]
