from datetime import date
from decimal import Decimal
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import transaction as db_transaction
from django.db.models import Sum, Q
from django.utils import timezone

from finance.models import (
    Transaction, FeeSchedule, FeeWaiver, PaymentAllocation,
    ReceiptCounter, StudentFeeAssignment,
)
from finance.serializers import (
    TransactionSerializer, TransactionCancelSerializer
)
from accounts.permissions import require_permission
from .base import (
    PeriodClosedMixin, CROSS_BANK_INCOME, CROSS_BANK_EXPENSE,
    _internal_accounts, _account_balances_update, _param,
    _check_period_open, _fiscal_year_from_date
)
from .ledger import LedgerActionsMixin
from core.audit import log_audit


class TransactionViewSet(LedgerActionsMixin, PeriodClosedMixin, viewsets.ModelViewSet):
    queryset = Transaction.objects.select_related('student', 'source_account', 'destination_account').all()
    serializer_class = TransactionSerializer
    filterset_fields = {
        'transaction_type': ['exact'],
        'category': ['exact'],
        'student_id': ['exact'],
        'class_name': ['exact'],
        'fiscal_year': ['exact'],
        'fee_month': ['exact'],
        'transaction_date': ['gte', 'lte'],
    }

    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'balances', 'ledger', 'fee_status']:
            return [require_permission('finance:read')()]
        return [require_permission('finance:write')()]

    def get_queryset(self):
        qs = super().get_queryset()
        account = _param(self.request, 'account')
        start_date = _param(self.request, 'start_date', 'startDate')
        end_date = _param(self.request, 'end_date', 'endDate')
        if account:
            qs = qs.filter(
                Q(source_account__name=account) | Q(destination_account__name=account)
            )
        if start_date:
            qs = qs.filter(transaction_date__gte=start_date)
        if end_date:
            qs = qs.filter(transaction_date__lte=end_date)
        return qs

    def perform_create(self, serializer):
        fiscal_year = serializer.validated_data.get('fiscal_year')
        if fiscal_year:
            _check_period_open(fiscal_year)
        tx_type = serializer.validated_data.get('transaction_type')

        if tx_type == 'INCOME':
            fee_month = serializer.validated_data.get('fee_month') or self.request.data.get('feeMonth')
            if not fee_month:
                from rest_framework.exceptions import ValidationError
                raise ValidationError({'feeMonth': 'Fee month is required for income transactions.'})

        with db_transaction.atomic():
            tx_date = serializer.validated_data.get('transaction_date') or timezone.now().date()
            tx = serializer.save(
                created_by=str(self.request.user.id),
                fiscal_year=fiscal_year or _fiscal_year_from_date(tx_date),
            )

            allocations = self.request.data.get('allocations')
            if allocations and tx_type == 'INCOME':
                from rest_framework.exceptions import ValidationError
                fee_ids = [
                    a.get('feeScheduleId') or a.get('fee_schedule_id')
                    for a in allocations
                    if (a.get('feeScheduleId') or a.get('fee_schedule_id')) and (a.get('feeScheduleId') or a.get('fee_schedule_id')) != '__other__'
                ]
                fee_map = {
                    str(fs.id): fs
                    for fs in FeeSchedule.objects.filter(id__in=fee_ids)
                }
                alloc_objects = []
                for alloc in allocations:
                    fs_id = alloc.get('feeScheduleId') or alloc.get('fee_schedule_id')
                    if not fs_id:
                        continue
                    if fs_id == '__other__':
                        continue
                    if str(fs_id) not in fee_map:
                        continue
                    fs = fee_map[str(fs_id)]
                    alloc_amount = Decimal(str(alloc.get('amount', 0)))

                    if fs.applicability == 'ASSIGNED_ONLY':
                        assignment = StudentFeeAssignment.objects.filter(
                            student=tx.student, fee_schedule=fs, active=True,
                        ).first()
                        if not assignment:
                            raise ValidationError({
                                'allocations': f'You are not assigned to fee "{fs.category}".'
                            })
                        if fee_month:
                            if assignment.starts_at and fee_month < assignment.starts_at:
                                raise ValidationError({
                                    'allocations': f'Fee "{fs.category}" is not yet active. Starts on {assignment.starts_at}.'
                                })
                            if assignment.ends_at and fee_month > assignment.ends_at:
                                raise ValidationError({
                                    'allocations': f'Fee "{fs.category}" has expired. Ended on {assignment.ends_at}.'
                                })

                    waiver = FeeWaiver.objects.filter(
                        student=tx.student, fee_schedule=fs, active=True,
                    ).first()
                    if waiver:
                        expected = waiver.value
                    else:
                        expected = fs.amount

                    if alloc_amount != expected:
                        raise ValidationError({
                            'allocations': f'Amount {alloc_amount} for fee "{fs.category}" does not match expected amount {expected}{f" (waiver applied)" if waiver else ""}.'
                        })
                    alloc_objects.append(PaymentAllocation(
                        transaction=tx,
                        fee_schedule=fs,
                        student=tx.student,
                        period=alloc.get('period', ''),
                        amount=alloc_amount,
                    ))
                PaymentAllocation.objects.bulk_create(alloc_objects)
                if not tx.category and alloc_objects:
                    cats = FeeSchedule.objects.filter(id__in=fee_ids).values_list('category', flat=True)
                    tx.category = ', '.join(sorted(set(cats)))
                    tx.save(update_fields=['category'])
            elif tx_type == 'INCOME':
                fee_schedule_id = self.request.data.get('feeScheduleId') or self.request.data.get('fee_schedule_id')
                if fee_schedule_id and tx.student_id:
                    from rest_framework.exceptions import ValidationError
                    try:
                        fs = FeeSchedule.objects.get(id=fee_schedule_id)
                    except FeeSchedule.DoesNotExist:
                        raise ValidationError({'feeScheduleId': 'Fee schedule not found.'})
                    waiver = FeeWaiver.objects.filter(
                        student=tx.student, fee_schedule=fs, active=True,
                    ).first()
                    expected = waiver.value if waiver else fs.amount
                    if tx.amount != expected:
                        raise ValidationError({
                            'amount': f'Amount {tx.amount} does not match expected fee amount {expected}{f" (waiver applied)" if waiver else ""} for "{fs.category}".'
                        })
                    fee_month = self.request.data.get('feeMonth') or self.request.data.get('fee_month') or serializer.validated_data.get('fee_month')
                    PaymentAllocation.objects.create(
                        transaction=tx,
                        fee_schedule=fs,
                        student=tx.student,
                        period=fee_month or '',
                        amount=tx.amount,
                    )

            if tx_type == 'INCOME' and tx.destination_account and tx.destination_account.name in _internal_accounts():
                tx.affects_income_ledger = True
                fy = tx.fiscal_year or _fiscal_year_from_date(tx.transaction_date)
                counter, _ = ReceiptCounter.objects.select_for_update().get_or_create(
                    fiscal_year=fy,
                    receipt_type='RCPT',
                    defaults={'next_sequence': 1}
                )
                tx.receipt_sequence = counter.next_sequence
                tx.reference_id = f"RCPT-{fy}-{counter.next_sequence:04d}"
                counter.next_sequence += 1
                counter.save(update_fields=['next_sequence'])

            if tx_type == 'EXPENSE' and tx.source_account and tx.source_account.name in _internal_accounts():
                tx.affects_expense_ledger = True
                fy = tx.fiscal_year or _fiscal_year_from_date(tx.transaction_date)
                counter, _ = ReceiptCounter.objects.select_for_update().get_or_create(
                    fiscal_year=fy,
                    receipt_type='PV',
                    defaults={'next_sequence': 1}
                )
                tx.receipt_sequence = counter.next_sequence
                tx.reference_id = f"PV-{fy}-{counter.next_sequence:04d}"
                counter.next_sequence += 1
                counter.save(update_fields=['next_sequence'])

            if tx_type == 'INTERNAL_TRANSFER' and tx.source_account and tx.destination_account:
                src_internal = tx.source_account.name in _internal_accounts()
                dst_internal = tx.destination_account.name in _internal_accounts()
                if src_internal and dst_internal:
                    fy = tx.fiscal_year or _fiscal_year_from_date(tx.transaction_date)
                    counter, _ = ReceiptCounter.objects.select_for_update().get_or_create(
                        fiscal_year=fy,
                        receipt_type='TV',
                        defaults={'next_sequence': 1}
                    )
                    tx.receipt_sequence = counter.next_sequence
                    tx.reference_id = f"TV-{fy}-{counter.next_sequence:04d}"
                    counter.next_sequence += 1
                    counter.save(update_fields=['next_sequence'])

            if not tx.token_number and tx_type in ('INCOME', 'EXPENSE'):
                fy = tx.fiscal_year or _fiscal_year_from_date(tx.transaction_date)
                token_counter, _ = ReceiptCounter.objects.select_for_update().get_or_create(
                    fiscal_year=fy,
                    receipt_type='TOKEN',
                    defaults={'next_sequence': 1}
                )
                tx.token_number = token_counter.next_sequence
                token_counter.next_sequence += 1
                token_counter.save(update_fields=['next_sequence'])

            tx.save()
            _account_balances_update(tx)
        log_audit('create', 'transaction', entity_id=tx.pk,
                  details={'type': tx_type, 'amount': str(tx.amount),
                           'source_account': tx.source_account.name if tx.source_account else None,
                           'destination_account': tx.destination_account.name if tx.destination_account else None,
                           'student': tx.student.name if tx.student else None,
                           'fee_month': tx.fee_month}, request=self.request)

    @action(detail=False, methods=['post'])
    def bulk(self, request):
        with db_transaction.atomic():
            results = []
            errors = []
            seen_paid = set()

            for idx, item in enumerate(request.data):
                serializer = self.get_serializer(data=item)
                serializer.is_valid(raise_exception=True)

                fiscal_year = serializer.validated_data.get('fiscal_year')
                if fiscal_year:
                    _check_period_open(fiscal_year)

                student = serializer.validated_data.get('student')
                fee_month = serializer.validated_data.get('fee_month')
                category = serializer.validated_data.get('category')

                if student and fee_month and category:
                    dup_key = (str(student.id), fee_month, category)
                    if dup_key in seen_paid:
                        errors.append({'index': idx, 'student': str(student.id), 'feeMonth': fee_month, 'category': category, 'error': f'Fee month {fee_month} already imported for this student in {category}'})
                        continue
                    exists = Transaction.objects.filter(
                        student=student, fee_month=fee_month, category=category,
                        is_cancelled=False,
                    ).exists()
                    if exists:
                        errors.append({'index': idx, 'student': str(student.id), 'feeMonth': fee_month, 'category': category, 'error': f'Fee month {fee_month} already paid for {student.name} in {category}'})
                        continue
                    seen_paid.add(dup_key)

                tx_date = serializer.validated_data.get('transaction_date') or timezone.now().date()
                tx = serializer.save(
                    created_by=str(self.request.user.id),
                    fiscal_year=fiscal_year or _fiscal_year_from_date(tx_date),
                )
                _account_balances_update(tx)
                results.append(TransactionSerializer(tx).data)

            if errors and not results:
                return Response({'error': 'All rows have duplicate fee months', 'details': errors}, status=status.HTTP_400_BAD_REQUEST)
            if errors:
                return Response({'created': results, 'skipped': errors}, status=status.HTTP_201_CREATED)
            return Response(results, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        tx = self.get_object()
        if tx.is_cancelled:
            return Response({'error': 'Already cancelled'}, status=400)
        if tx.fiscal_year:
            _check_period_open(tx.fiscal_year)

        serializer = TransactionCancelSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        with db_transaction.atomic():
            tx.is_cancelled = True
            tx.cancelled_at = timezone.now()
            tx.cancelled_by = str(request.user.id)
            tx.cancel_reason = serializer.validated_data['reason']
            tx.save()
            _account_balances_update(tx)

            reversal = Transaction.objects.create(
                transaction_date=tx.transaction_date,
                entry_date=date.today(),
                transaction_type=tx.transaction_type,
                source_account=tx.destination_account,
                destination_account=tx.source_account,
                amount=tx.amount,
                description=f"Reversal of {tx.reference_id or tx.id}: {tx.cancel_reason}",
                student=tx.student,
                class_name=tx.class_name,
                category=tx.category,
                created_by=str(request.user.id),
                fiscal_year=tx.fiscal_year,
                reversal_of_id=tx.id,
            )
            if tx.transaction_type == 'INCOME':
                reversal.transaction_type = 'EXPENSE'
                reversal.affects_expense_ledger = True
            elif tx.transaction_type == 'EXPENSE':
                reversal.transaction_type = 'INCOME'
                reversal.affects_income_ledger = True

            if reversal.transaction_type == 'INCOME':
                reversal_type = 'RCPT'
            elif reversal.transaction_type == 'EXPENSE':
                reversal_type = 'PV'
            else:
                reversal_type = 'TV'
            fy = reversal.fiscal_year or _fiscal_year_from_date(reversal.transaction_date)
            counter, _ = ReceiptCounter.objects.select_for_update().get_or_create(
                fiscal_year=fy, receipt_type=reversal_type,
                defaults={'next_sequence': 1},
            )
            seq = counter.next_sequence
            counter.next_sequence = seq + 1
            counter.save(update_fields=['next_sequence'])
            reversal.reference_id = f"{reversal_type}-{fy}-{seq:04d}"
            reversal.save()

        log_audit('cancel', 'transaction', entity_id=tx.pk,
                  details={'reason': tx.cancel_reason, 'amount': str(tx.amount),
                           'source_account': tx.source_account.name if tx.source_account else None,
                           'destination_account': tx.destination_account.name if tx.destination_account else None}, request=request)
        return Response(TransactionSerializer(tx).data)

    @action(detail=False, methods=['get'])
    def balances(self, request):
        date_from = _param(request, 'date_from', 'dateFrom')
        date_to = _param(request, 'date_to', 'dateTo')

        qs = Transaction.objects.filter(is_cancelled=False, reversal_of_id__isnull=True)
        if date_from:
            qs = qs.filter(transaction_date__gte=date_from)
        if date_to:
            qs = qs.filter(transaction_date__lte=date_to)

        accounts = _internal_accounts()

        income_qs = qs.filter(transaction_type='INCOME').values(
            'destination_account__name'
        ).annotate(total=Sum('amount')).values_list('destination_account__name', 'total')
        income_map = dict(income_qs)

        expense_qs = qs.filter(transaction_type='EXPENSE').values(
            'source_account__name'
        ).annotate(total=Sum('amount')).values_list('source_account__name', 'total')
        expense_map = dict(expense_qs)

        transfer_in_qs = qs.filter(transaction_type='INTERNAL_TRANSFER').values(
            'destination_account__name'
        ).annotate(total=Sum('amount')).values_list('destination_account__name', 'total')
        transfer_in_map = dict(transfer_in_qs)

        transfer_out_qs = qs.filter(transaction_type='INTERNAL_TRANSFER').values(
            'source_account__name'
        ).annotate(total=Sum('amount')).values_list('source_account__name', 'total')
        transfer_out_map = dict(transfer_out_qs)

        from finance.models import OpeningBalance
        fy = _fiscal_year_from_date(timezone.now().date())
        opening_qs = OpeningBalance.objects.filter(
            fiscal_year=fy, account__name__in=accounts
        ).select_related('account').values_list('account__name', 'amount')
        opening_map = dict(opening_qs)

        results = {}
        for account in accounts:
            opening = opening_map.get(account, Decimal('0'))
            income = income_map.get(account, Decimal('0'))
            expense = expense_map.get(account, Decimal('0'))
            transfer_in = transfer_in_map.get(account, Decimal('0'))
            transfer_out = transfer_out_map.get(account, Decimal('0'))
            results[account] = opening + income + transfer_in - expense - transfer_out

        return Response(results)

    @action(detail=False, methods=['get'])
    def dashboard_summary(self, request):
        fy = _param(request, 'fiscal_year', 'fiscalYear') or timezone.now().year
        try:
            fy = int(fy)
        except ValueError:
            fy = timezone.now().year

        agg = Transaction.objects.filter(
            fiscal_year=fy, is_cancelled=False,
        ).aggregate(
            income=Sum('amount', filter=CROSS_BANK_INCOME),
            expense=Sum('amount', filter=CROSS_BANK_EXPENSE),
            deposited=Sum('amount', filter=Q(
                destination_account__name='AL_RAWA_BANK',
            )),
        )

        return Response({
            'fiscalYear': fy,
            'totalIncome': agg['income'] or Decimal('0'),
            'totalExpense': agg['expense'] or Decimal('0'),
            'totalDepositedToBank': agg['deposited'] or Decimal('0'),
            'depositRemaining': (agg['income'] or Decimal('0')) - (agg['deposited'] or Decimal('0')),
            'net': (agg['income'] or Decimal('0')) - (agg['expense'] or Decimal('0')),
        })
