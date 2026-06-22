from datetime import datetime
from decimal import Decimal
from rest_framework import viewsets, status, generics
from rest_framework.exceptions import PermissionDenied
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import transaction as db_transaction
from django.db.models import Sum, Q
from django.utils import timezone
from django.core.cache import cache
from finance.models import (
    Transaction, FeeSchedule, FeeWaiver, StudentFeeAssignment,
    PaymentAllocation, ReceiptCounter, OpeningBalance,
    OpeningBalanceHistory, PeriodClose, Reconciliation,
    BankAccount, AccountBalance,
)
from students.models import Student
from finance.serializers import (
    TransactionSerializer, TransactionCancelSerializer,
    FeeScheduleSerializer, FeeScheduleCopySerializer,
    FeeWaiverSerializer, StudentFeeAssignmentSerializer,
    StudentFeeAssignmentToggleSerializer, BulkAssignSerializer,
    OpeningBalanceSerializer, OpeningBalanceHistorySerializer,
    PeriodCloseSerializer, ReconciliationSerializer,
    PaymentAllocationSerializer, BalanceSerializer,
)
from accounts.permissions import require_permission


def _waiver_expected_amount(waiver, fee_schedule_amount):
    """Compute the expected payment amount given a waiver and fee schedule amount.

    For CUSTOM_AMOUNT waivers, `value` is the exact amount to pay.
    For PERCENTAGE waivers, `value` is the percentage discount applied to the base amount.
    Returns `fee_schedule_amount` if no waiver is provided.
    Accepts waiver as either a model instance or a dict (from .values()).
    """
    if not waiver:
        return fee_schedule_amount
    waiver_type = waiver.type if hasattr(waiver, 'type') else waiver.get('type')
    waiver_value = waiver.value if hasattr(waiver, 'value') else waiver.get('value')
    if waiver_type == 'PERCENTAGE':
        discount = fee_schedule_amount * (Decimal(str(waiver_value)) / Decimal('100'))
        return (fee_schedule_amount - discount).quantize(Decimal('0.01'))
    return Decimal(str(waiver_value))


PRIMARY_BANK = 'AL_RAWA_BANK'
SECONDARY_BANK = 'GLOBAL_FORUM_BANK'
CASH_BANK = 'CASH_IN_HAND'

CROSS_BANK_INCOME = Q(transaction_type='INCOME') | (
    Q(transaction_type='INTERNAL_TRANSFER',
      source_account__name=SECONDARY_BANK,
      destination_account__name=PRIMARY_BANK)
)
CROSS_BANK_EXPENSE = Q(transaction_type='EXPENSE') | (
    Q(transaction_type='INTERNAL_TRANSFER',
      source_account__name=PRIMARY_BANK,
      destination_account__name=SECONDARY_BANK)
)

def _internal_accounts():
    """Get active bank account names, cached for performance."""
    cache_key = 'active_bank_account_names'
    names = cache.get(cache_key)
    if names is None:
        names = list(BankAccount.objects.filter(
            is_active=True
        ).values_list('name', flat=True))
        cache.set(cache_key, names, 300)  # 5 minutes
    return names


def _invalidate_internal_accounts_cache():
    """Invalidate the bank account names cache."""
    cache.delete('active_bank_account_names')


def _account_balances_update(transaction):
    """Update AccountBalance cache for a transaction's accounts."""
    with db_transaction.atomic():
        for account_field in ('source_account', 'destination_account'):
            account = getattr(transaction, account_field, None)
            if not account:
                continue
            fy = transaction.fiscal_year
            if not fy:
                continue
            month = transaction.transaction_date.month
            bal, _ = AccountBalance.objects.select_for_update().get_or_create(
                account=account,
                fiscal_year=fy,
                month=month,
                defaults={'opening_balance': 0},
            )
            is_source = (account_field == 'source_account')
            if transaction.is_cancelled:
                if is_source:
                    bal.total_debits -= transaction.amount
                else:
                    bal.total_credits -= transaction.amount
            else:
                if is_source:
                    bal.total_debits += transaction.amount
                else:
                    bal.total_credits += transaction.amount
            bal.closing_balance = bal.opening_balance + bal.total_credits - bal.total_debits
            bal.save()


def _param(request, *names):
    """Get query param by any of the given names (e.g., snake_case and camelCase)."""
    for name in names:
        val = request.query_params.get(name)
        if val is not None:
            return val
    return None


def _invalidate_dashboard_cache(fiscal_year=None):
    """Invalidate dashboard summary cache for one or all fiscal years."""
    if fiscal_year is not None:
        cache.delete(f'finance_dashboard_{fiscal_year}')
    else:
        for y in range(timezone.now().year - 2, timezone.now().year + 2):
            cache.delete(f'finance_dashboard_{y}')


def _check_period_open(fiscal_year):
    if PeriodClose.objects.filter(fiscal_year=fiscal_year).exists():
        raise PermissionDenied(f"Transactions cannot be modified for fiscal year {fiscal_year}. Period is closed.")


def _fiscal_year_from_date(dt):
    """Calculate fiscal year from a date using September start (month > 8 → fy = year+1).
    FISCAL_YEAR_START_MONTH is 0-indexed (8=Sep in JS), so compare with dt.month (> not >=)."""
    from school_management.settings import FISCAL_YEAR_START_MONTH
    return dt.year + 1 if dt.month > FISCAL_YEAR_START_MONTH else dt.year


class PeriodClosedMixin:
    def perform_create(self, serializer):
        fiscal_year = serializer.validated_data.get('fiscal_year')
        if fiscal_year:
            _check_period_open(fiscal_year)
        serializer.save()

    def perform_update(self, serializer):
        if serializer.instance and hasattr(serializer.instance, 'fiscal_year'):
            _check_period_open(serializer.instance.fiscal_year)
        serializer.save()

    def perform_destroy(self, instance):
        if hasattr(instance, 'fiscal_year') and instance.fiscal_year:
            _check_period_open(instance.fiscal_year)
        instance.delete()
