from django.contrib import admin
from .models import (
    BankAccount, Transaction, FeeSchedule, FeeWaiver,
    StudentFeeAssignment, PaymentAllocation, ReceiptCounter,
    OpeningBalance, OpeningBalanceHistory, PeriodClose,
    Reconciliation, AccountBalance,
)


@admin.register(BankAccount)
class BankAccountAdmin(admin.ModelAdmin):
    list_display = ('name', 'display_name', 'is_active', 'created_at')
    list_filter = ('is_active',)


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('transaction_type', 'amount', 'category', 'transaction_date',
                    'source_account', 'destination_account', 'is_cancelled')
    list_filter = ('transaction_type', 'fiscal_year', 'is_cancelled')
    search_fields = ('description', 'reference_id', 'category')
    readonly_fields = ('id', 'created_at', 'updated_at')


@admin.register(FeeSchedule)
class FeeScheduleAdmin(admin.ModelAdmin):
    list_display = ('category', 'amount', 'frequency', 'academic_year', 'school_class', 'applicability')
    list_filter = ('frequency', 'applicability', 'academic_year')
    search_fields = ('category',)


@admin.register(FeeWaiver)
class FeeWaiverAdmin(admin.ModelAdmin):
    list_display = ('student', 'fee_schedule', 'type', 'value', 'active')
    list_filter = ('active', 'type')


@admin.register(StudentFeeAssignment)
class StudentFeeAssignmentAdmin(admin.ModelAdmin):
    list_display = ('student', 'fee_schedule', 'active', 'starts_at', 'ends_at')
    list_filter = ('active',)


@admin.register(PeriodClose)
class PeriodCloseAdmin(admin.ModelAdmin):
    list_display = ('fiscal_year', 'closed_at', 'closed_by')
    readonly_fields = ('closed_at',)


@admin.register(OpeningBalance)
class OpeningBalanceAdmin(admin.ModelAdmin):
    list_display = ('account', 'fiscal_year', 'amount', 'updated_at')
    list_filter = ('fiscal_year',)


@admin.register(Reconciliation)
class ReconciliationAdmin(admin.ModelAdmin):
    list_display = ('account', 'statement_date', 'closing_balance', 'status')
    list_filter = ('status',)


@admin.register(AccountBalance)
class AccountBalanceAdmin(admin.ModelAdmin):
    list_display = ('account', 'fiscal_year', 'month', 'opening_balance',
                    'total_debits', 'total_credits', 'closing_balance')
    list_filter = ('fiscal_year',)
