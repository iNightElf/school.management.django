from datetime import datetime
from decimal import Decimal
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import transaction as db_transaction
from django.db.models import Sum, Q, Case, When, Value
from django.utils import timezone

from finance.models import (
    Transaction, FeeSchedule, FeeWaiver, PaymentAllocation, 
    ReceiptCounter, BankAccount, AccountBalance
)
from students.models import Student
from finance.serializers import (
    TransactionSerializer, TransactionCancelSerializer
)
from accounts.permissions import require_permission
from .base import (
    PeriodClosedMixin, CROSS_BANK_INCOME, CROSS_BANK_EXPENSE,
    _internal_accounts, _account_balances_update, _param,
    _check_period_open, _fiscal_year_from_date
)

class TransactionViewSet(PeriodClosedMixin, viewsets.ModelViewSet):
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
            tx_date = serializer.validated_data.get('transaction_date') or datetime.now().date()
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
                    if a.get('feeScheduleId') or a.get('fee_schedule_id')
                ]
                fee_map = {
                    str(fs.id): fs
                    for fs in FeeSchedule.objects.filter(id__in=fee_ids)
                }
                alloc_objects = []
                for alloc in allocations:
                    fs_id = alloc.get('feeScheduleId') or alloc.get('fee_schedule_id')
                    if not fs_id or str(fs_id) not in fee_map:
                        continue
                    fs = fee_map[str(fs_id)]
                    alloc_amount = Decimal(str(alloc.get('amount', 0)))

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

            if tx_type == 'INCOME' and tx.destination_account and tx.destination_account.name in _internal_accounts():
                tx.affects_income_ledger = True
                fy = tx.fiscal_year or datetime.now().year
                counter, _ = ReceiptCounter.objects.select_for_update().get_or_create(
                    fiscal_year=fy,
                    receipt_type='INCOME',
                    defaults={'next_sequence': 1}
                )
                tx.receipt_sequence = counter.next_sequence
                tx.reference_id = f"RCP-{fy}-{counter.next_sequence:06d}"
                counter.next_sequence += 1
                counter.save(update_fields=['next_sequence'])

            if tx_type == 'EXPENSE' and tx.source_account and tx.source_account.name in _internal_accounts():
                tx.affects_expense_ledger = True
                fy = tx.fiscal_year or datetime.now().year
                counter, _ = ReceiptCounter.objects.select_for_update().get_or_create(
                    fiscal_year=fy,
                    receipt_type='EXPENSE',
                    defaults={'next_sequence': 1}
                )
                tx.receipt_sequence = counter.next_sequence
                tx.reference_id = f"VCH-{fy}-{counter.next_sequence:06d}"
                counter.next_sequence += 1
                counter.save(update_fields=['next_sequence'])

            if not tx.token_number and tx_type in ('INCOME', 'EXPENSE'):
                fy = tx.fiscal_year or datetime.now().year
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

    @action(detail=False, methods=['post'])
    def bulk(self, request):
        with db_transaction.atomic():
            results = []
            for item in request.data:
                serializer = self.get_serializer(data=item)
                serializer.is_valid(raise_exception=True)
                
                fiscal_year = serializer.validated_data.get('fiscal_year')
                if fiscal_year:
                    _check_period_open(fiscal_year)
                
                tx_date = serializer.validated_data.get('transaction_date') or datetime.now().date()
                tx = serializer.save(
                    created_by=str(self.request.user.id),
                    fiscal_year=fiscal_year or _fiscal_year_from_date(tx_date),
                )
                _account_balances_update(tx)
                results.append(TransactionSerializer(tx).data)
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
                transaction_type='INTERNAL_TRANSFER' if tx.transaction_type == 'INTERNAL_TRANSFER'
                else tx.transaction_type,
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
            reversal.save()
            _account_balances_update(reversal)

        return Response(TransactionSerializer(tx).data)

    @action(detail=False, methods=['get'])
    def balances(self, request):
        date_from = _param(request, 'date_from', 'dateFrom')
        date_to = _param(request, 'date_to', 'dateTo')

        qs = Transaction.objects.filter(is_cancelled=False)
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

        results = {}
        for account in accounts:
            income = income_map.get(account, Decimal('0'))
            expense = expense_map.get(account, Decimal('0'))
            transfer_in = transfer_in_map.get(account, Decimal('0'))
            transfer_out = transfer_out_map.get(account, Decimal('0'))
            results[account] = income + transfer_in - expense - transfer_out

        return Response(results)

    @action(detail=False, methods=['get'])
    def ledger(self, request):
        account_name = _param(request, 'account')
        if account_name not in _internal_accounts():
            return Response({'error': 'Invalid account'}, status=400)

        date_from = _param(request, 'date_from', 'dateFrom')
        date_to = _param(request, 'date_to', 'dateTo')

        account_filter = Q(source_account__name=account_name) | Q(destination_account__name=account_name)

        all_txs = Transaction.objects.filter(
            account_filter, is_cancelled=False,
        ).select_related('student', 'source_account', 'destination_account').order_by('transaction_date', 'created_at')

        # Compute pre-range opening balance from AccountBalance cache
        opening_balance = Decimal('0')
        if date_from:
            from_date = datetime.strptime(date_from, '%Y-%m-%d').date()
            fy = from_date.year
            if from_date.month >= 9:
                fy = from_date.year + 1
            prev_month = from_date.month - 1 or 12
            prev_fy = fy - 1 if prev_month == 12 else fy
            try:
                account_obj = BankAccount.objects.get(name=account_name)
                bal = AccountBalance.objects.filter(
                    account=account_obj,
                    fiscal_year=prev_fy,
                    month=prev_month,
                ).first()
                if bal:
                    opening_balance = bal.closing_balance
            except BankAccount.DoesNotExist:
                pass

        # Fallback: compute opening balance from prior transactions before date_from
        if date_from and opening_balance == 0:
            agg = Transaction.objects.filter(
                account_filter,
                is_cancelled=False,
                transaction_date__lt=date_from,
            ).aggregate(
                total_in=Sum('amount', filter=Q(destination_account__name=account_name)),
                total_out=Sum('amount', filter=Q(source_account__name=account_name)),
            )
            opening_balance = (agg['total_in'] or Decimal('0')) - (agg['total_out'] or Decimal('0'))

        # Filter to date range for display
        if date_from:
            all_txs = all_txs.filter(transaction_date__gte=date_from)
        if date_to:
            all_txs = all_txs.filter(transaction_date__lte=date_to)

        # Compute running balances and totals
        running = opening_balance
        data = []
        total_debits = Decimal('0')
        total_credits = Decimal('0')
        for tx in all_txs:
            is_incoming = tx.destination_account and tx.destination_account.name == account_name
            is_outgoing = tx.source_account and tx.source_account.name == account_name
            debit = tx.amount if is_incoming else Decimal('0')
            credit = tx.amount if is_outgoing else Decimal('0')
            if is_outgoing:
                running -= tx.amount
            if is_incoming:
                running += tx.amount

            display_type = tx.transaction_type
            if tx.transaction_type == 'INTERNAL_TRANSFER' and tx.source_account and tx.destination_account:
                src = tx.source_account.name
                dst = tx.destination_account.name
                if src == 'GLOBAL_FORUM_BANK' and dst == 'AL_RAWA_BANK':
                    display_type = 'INCOME'
                elif src == 'AL_RAWA_BANK' and dst == 'GLOBAL_FORUM_BANK':
                    display_type = 'EXPENSE'
            total_debits += debit
            total_credits += credit
            data.append({
                'id': str(tx.id),
                'transactionDate': tx.transaction_date.isoformat(),
                'createdAt': tx.created_at.isoformat(),
                'transactionType': display_type,
                'amount': float(tx.amount),
                'debit': float(debit),
                'credit': float(credit),
                'runningBalance': float(running),
                'description': tx.description or (
                    tx.destination_account.name
                    if tx.transaction_type == 'INTERNAL_TRANSFER' and tx.destination_account
                    else ''
                ),
                'category': tx.category,
                'sourceAccount': tx.source_account.name if tx.source_account else None,
                'destinationAccount': tx.destination_account.name if tx.destination_account else None,
                'studentId': str(tx.student_id) if tx.student_id else None,
                'studentName': tx.student.name if tx.student else None,
                'className': tx.class_name,
                'feeMonth': tx.fee_month,
                'fiscalYear': tx.fiscal_year,
                'receiptSequence': tx.receipt_sequence,
                'tokenNumber': tx.token_number,
                'referenceId': tx.reference_id,
                'isCancelled': tx.is_cancelled,
                'reversalOfId': str(tx.reversal_of_id) if tx.reversal_of_id else None,
            })

        # Manual pagination for computed results
        page_size = int(self.request.query_params.get('limit', 50))
        page_num = int(self.request.query_params.get('page', 1))
        start = (page_num - 1) * page_size
        end = start + page_size
        page_data = data[start:end]
        total_pages = max(1, (len(data) + page_size - 1) // page_size)

        return Response({
            'data': page_data,
            'total': len(data),
            'totalPages': total_pages,
            'openingBalance': float(opening_balance),
            'closingBalance': float(running),
            'totalDebits': float(total_debits),
            'totalCredits': float(total_credits),
        })

    @action(detail=False, methods=['get'])
    def fee_status(self, request):
        student_id = request.query_params.get('student_id') or request.query_params.get('studentId')
        if not student_id:
            return Response({'error': 'student_id required'}, status=400)

        fee_month = request.query_params.get('fee_month') or request.query_params.get('feeMonth')
        fee_month_to = request.query_params.get('fee_month_to') or request.query_params.get('feeMonthTo')

        try:
            student = Student.objects.get(id=student_id)
        except Student.DoesNotExist:
            return Response({'error': 'Student not found'}, status=404)

        # Find fee schedules for this student's class (or All Classes)
        class_id = student.school_class_id
        schedule_filter = Q(school_class_id=class_id) | Q(school_class_id__isnull=True)
        schedules = FeeSchedule.objects.filter(schedule_filter).order_by('category')

        # Build paid lookup: (fee_schedule_id, month) -> paid
        tx_filter = Q(student_id=student_id, transaction_type='INCOME', is_cancelled=False)
        if fee_month:
            tx_filter &= Q(fee_month__gte=fee_month)
        if fee_month_to:
            tx_filter &= Q(fee_month__lte=fee_month_to)

        paid_txs = Transaction.objects.filter(tx_filter).values('fee_month', 'category').annotate(
            total=Sum('amount')
        )
        paid_by_category = {}
        for pt in paid_txs:
            key = pt['category']
            paid_by_category[key] = paid_by_category.get(key, Decimal('0')) + pt['total']

        result = []
        for s in schedules:
            total_paid = paid_by_category.get(s.category, Decimal('0'))
            result.append({
                'feeScheduleId': str(s.id),
                'category': s.category,
                'amount': float(s.amount),
                'frequency': s.frequency,
                'applicability': s.applicability,
                'paid': float(total_paid) >= float(s.amount),
            })

        return Response(result)

    @action(detail=False, methods=['get'])
    def dashboard_summary(self, request):
        fy = _param(request, 'fiscal_year', 'fiscalYear') or datetime.now().year
        try:
            fy = int(fy)
        except ValueError:
            fy = datetime.now().year

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

    @action(detail=False, methods=['get'])
    def defaulter(self, request):
        params = request.query_params
        class_name = _param(request, 'class_name', 'className')
        student_id = _param(request, 'student_id', 'studentId')
        fee_category = _param(request, 'fee_category', 'feeCategory')
        month_from = _param(request, 'month_from', 'monthFrom')
        month_to = _param(request, 'month_to', 'monthTo')
        year_str = _param(request, 'year') or str(datetime.now().year)

        students_qs = Student.objects.filter(deleted_at__isnull=True)
        if class_name:
            students_qs = students_qs.filter(school_class__name=class_name)
        if student_id:
            students_qs = students_qs.filter(id=student_id)

        students = list(students_qs.select_related('school_class').only('id', 'name', 'school_class__name'))
        if not students:
            return Response([])

        student_ids = [s.id for s in students]
        student_map = {s.id: s for s in students}

        fee_schedules = FeeSchedule.objects.filter(
            academic_year__name=year_str,
        ).select_related('academic_year', 'school_class')
        if fee_category:
            fee_schedules = fee_schedules.filter(category=fee_category)

        yearly_schedules = [fs for fs in fee_schedules if fs.frequency in ('YEARLY', 'ONE_TIME')]
        monthly_schedules = [fs for fs in fee_schedules if fs.frequency == 'MONTHLY']

        assigned = set()
        if monthly_schedules and student_ids:
            assn = StudentFeeAssignment.objects.filter(
                student_id__in=student_ids,
                fee_schedule__in=monthly_schedules,
                active=True,
            ).values_list('student_id', 'fee_schedule_id')
            assigned = {(s, fs) for s, fs in assn}
            print(f"[DEBUG] Monthly assigned set: {assigned}")

        # Fetch assigned only
        yearly_assigned = set()
        assigned_only_yearly = [fs for fs in yearly_schedules if fs.applicability == 'ASSIGNED_ONLY']
        if assigned_only_yearly and student_ids:
            yearly_assigned = set(
                StudentFeeAssignment.objects.filter(
                    student_id__in=student_ids,
                    fee_schedule__in=assigned_only_yearly,
                    active=True,
                ).values_list('student_id', 'fee_schedule_id')
            )
        print(f"[DEBUG] Assigned-only yearly set: {yearly_assigned}")

        paid_allocations = PaymentAllocation.objects.filter(
            student_id__in=student_ids,
        ).values('student_id', 'fee_schedule_id', 'period').annotate(total=Sum('amount'))

        paid_map = {}
        for pa in paid_allocations:
            key = (pa['student_id'], pa['fee_schedule_id'], pa['period'] or '')
            paid_map[key] = float(pa['total'])

        result = []
        for student in students:
            sid = student.id
            class_name_str = student.school_class.name if student.school_class else ''

            fees = []
            total_due = 0
            total_paid = 0

            for fs in yearly_schedules:
                if fs.school_class and fs.school_class.name != class_name_str:
                    continue
                if fs.applicability == 'ASSIGNED_ONLY':
                    if (sid, fs.id) not in yearly_assigned:
                        continue

                amt = float(fs.amount)
                paid_amt = paid_map.get((sid, fs.id, ''), 0)

                fees.append({
                    'name': fs.category,
                    'amount': amt,
                    'paid': paid_amt >= amt,
                    'type': 'onetime' if fs.frequency == 'ONE_TIME' else 'global',
                })
                total_due += amt
                total_paid += paid_amt

            for fs in monthly_schedules:
                if fs.school_class and fs.school_class.name != class_name_str:
                    continue
                if fs.applicability == 'ASSIGNED_ONLY':
                    if (sid, fs.id) not in assigned:
                        continue

                months_list = []
                months_to_check = []
                if month_from and month_to:
                    parts_from = month_from.split('-')
                    parts_to = month_to.split('-')
                    if len(parts_from) == 2 and len(parts_to) == 2:
                        y, m = int(parts_from[0]), int(parts_from[1])
                        ey, em = int(parts_to[0]), int(parts_to[1])
                        while y < ey or (y == ey and m <= em):
                            label = f"{y}-{m:02d}"
                            months_to_check.append(label)
                            m += 1
                            if m > 12:
                                m = 1
                                y += 1

                amt = float(fs.amount)
                for month_label in months_to_check:
                    paid_amt = paid_map.get((sid, fs.id, month_label), 0)
                    months_list.append({
                        'month': month_label,
                        'amount': amt,
                        'paid': paid_amt >= amt,
                    })
                    total_due += amt
                    total_paid += paid_amt

                fees.append({
                    'name': fs.category,
                    'amount': amt,
                    'paid': total_paid >= total_due and len(months_to_check) > 0,
                    'type': 'recurring',
                    'months': months_list,
                })

            balance = total_due - total_paid

            result.append({
                'studentId': str(sid),
                'name': student.name,
                'class': class_name_str,
                'totalDue': total_due,
                'totalPaid': total_paid,
                'balance': balance,
                'fees': fees,
            })

        return Response(result)
