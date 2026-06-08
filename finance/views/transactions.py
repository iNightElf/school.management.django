from datetime import datetime, date
from decimal import Decimal
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import transaction as db_transaction
from django.db.models import Sum, Q, Case, When, Value
from django.utils import timezone

from finance.models import (
    Transaction, FeeSchedule, FeeWaiver, PaymentAllocation, 
    ReceiptCounter, BankAccount, AccountBalance, StudentFeeAssignment,
    OpeningBalance,
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

            # Generate voucher for reversal
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
        search = _param(request, 'search')

        account_filter = Q(source_account__name=account_name) | Q(destination_account__name=account_name)

        # STEP 1: FILTER FULL DATASET (include cancelled for ledger display)
        all_txs = Transaction.objects.filter(
            account_filter,
        ).select_related('student', 'source_account', 'destination_account').order_by('transaction_date', 'created_at', 'id')

        # Search filter
        if search:
            search_q = (
                Q(reference_id__icontains=search) |
                Q(description__icontains=search) |
                Q(category__icontains=search) |
                Q(student__name__icontains=search) |
                Q(class_name__icontains=search)
            )
            try:
                search_q |= Q(token_number=int(search))
            except (ValueError, TypeError):
                pass
            all_txs = all_txs.filter(search_q)

        # STEP 2: COMPUTE OPENING BALANCE (fiscal opening + all movements before dateFrom)
        opening_balance = Decimal('0')

        # Add fiscal opening balance
        if date_from:
            from_date = datetime.strptime(date_from, '%Y-%m-%d').date()
            fy = _fiscal_year_from_date(from_date)
            try:
                ob = OpeningBalance.objects.get(
                    account__name=account_name, fiscal_year=fy
                )
                opening_balance = ob.amount
            except (OpeningBalance.DoesNotExist, Exception):
                pass

        # Add all movements before dateFrom (effective: exclude cancelled)
        if date_from:
            agg = Transaction.objects.filter(
                account_filter,
                is_cancelled=False,
                transaction_date__lt=date_from,
            ).aggregate(
                total_in=Sum('amount', filter=Q(destination_account__name=account_name)),
                total_out=Sum('amount', filter=Q(source_account__name=account_name)),
            )
            opening_balance += (agg['total_in'] or Decimal('0')) - (agg['total_out'] or Decimal('0'))

        # Filter to date range for display
        if date_from:
            all_txs = all_txs.filter(transaction_date__gte=date_from)
        if date_to:
            all_txs = all_txs.filter(transaction_date__lte=date_to)

        # STEP 3: COMPUTE FULL RUNNING BALANCE + TOTALS on ALL filtered rows
        cancelled_ids = {tx.cancelled_by for tx in all_txs if tx.cancelled_by}
        from accounts.models import User
        cancelled_by_names = {str(u.id): u.name for u in User.objects.filter(id__in=cancelled_ids)} if cancelled_ids else {}

        running = opening_balance
        full_data = []
        total_debit = Decimal('0')
        total_credit = Decimal('0')

        for tx in all_txs:
            is_incoming = tx.destination_account and tx.destination_account.name == account_name
            is_outgoing = tx.source_account and tx.source_account.name == account_name
            debit = tx.amount if is_incoming else Decimal('0')
            credit = tx.amount if is_outgoing else Decimal('0')

            # Only count effective (non-cancelled) for running balance
            if not tx.is_cancelled:
                if is_outgoing:
                    running -= tx.amount
                if is_incoming:
                    running += tx.amount

            # Totals: only active transactions
            if not tx.is_cancelled and not tx.reversal_of_id:
                total_debit += debit
                total_credit += credit

            # Voucher type display
            voucher = tx.reference_id or ''
            display_type = tx.transaction_type
            if tx.transaction_type == 'INTERNAL_TRANSFER' and tx.source_account and tx.destination_account:
                src = tx.source_account.name
                dst = tx.destination_account.name
                if src == 'GLOBAL_FORUM_BANK' and dst == 'AL_RAWA_BANK':
                    display_type = 'INCOME'
                elif src == 'AL_RAWA_BANK' and dst == 'GLOBAL_FORUM_BANK':
                    display_type = 'EXPENSE'

            tx_status = 'Cancelled' if tx.is_cancelled else ('Reversal' if tx.reversal_of_id else 'Active')

            full_data.append({
                'id': str(tx.id),
                'voucher': voucher,
                'transactionDate': tx.transaction_date.isoformat(),
                'entryDate': tx.entry_date.isoformat() if tx.entry_date else tx.created_at.date().isoformat(),
                'transactionType': display_type,
                'amount': float(tx.amount),
                'debit': float(debit) if not tx.is_cancelled else 0,
                'credit': float(credit) if not tx.is_cancelled else 0,
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
                'tokenNumber': tx.token_number,
                'referenceId': tx.reference_id,
                'isCancelled': tx.is_cancelled,
                'cancelledAt': tx.cancelled_at.isoformat() if tx.cancelled_at else None,
                'cancelledBy': tx.cancelled_by,
                'cancelledByName': cancelled_by_names.get(tx.cancelled_by, tx.cancelled_by) if tx.cancelled_by else None,
                'cancelReason': tx.cancel_reason,
                'reversalOfId': str(tx.reversal_of_id) if tx.reversal_of_id else None,
                'status': tx_status,
                'createdBy': tx.created_by,
                'createdAt': tx.created_at.isoformat(),
            })

        # Closing balance = opening + total debit - total credit (from effective transactions)
        closing_balance = opening_balance + total_debit - total_credit
        total_rows = len(full_data)

        # STEP 4: APPLY PAGINATION AFTER balance is computed
        page_size = min(int(request.query_params.get('limit', 25)), 200)
        page_num = max(int(request.query_params.get('page', 1)), 1)
        start = (page_num - 1) * page_size
        end = start + page_size
        page_data = full_data[start:end]
        total_pages = max(1, (total_rows + page_size - 1) // page_size)

        return Response({
            'data': page_data,
            'page': page_num,
            'pageSize': page_size,
            'totalPages': total_pages,
            'totalRows': total_rows,
            'openingBalance': float(opening_balance),
            'closingBalance': float(closing_balance),
            'totalDebit': float(total_debit),
            'totalCredit': float(total_credit),
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

        def _months_in_range(start, end):
            months = []
            parts = start.split('-')
            y, m = int(parts[0]), int(parts[1])
            e_parts = end.split('-')
            ey, em = int(e_parts[0]), int(e_parts[1])
            while y < ey or (y == ey and m <= em):
                months.append(f"{y}-{m:02d}")
                m += 1
                if m > 12:
                    m = 1
                    y += 1
            return months

        # 1. Get all fee schedules that apply to this student (AUTO for their class + global)
        class_id = student.school_class_id
        schedules = FeeSchedule.objects.filter(
            Q(school_class_id=class_id) | Q(school_class_id__isnull=True)
        ).order_by('category')

        # 2. Separate AUTO vs ASSIGNED_ONLY
        auto_schedules = []
        assigned_only_schedules = []
        for s in schedules:
            if s.applicability == 'AUTO':
                auto_schedules.append(s)
            else:
                assigned_only_schedules.append(s)

        # 3. For ASSIGNED_ONLY: find which ones the student is assigned to
        assignment_dates = {}
        matching_assigned_ids = set()

        if assigned_only_schedules:
            query_start = fee_month or date.today().strftime('%Y-%m')
            query_end = fee_month_to or query_start

            try:
                assignments = StudentFeeAssignment.objects.filter(
                    student=student,
                    fee_schedule_id__in=[s.id for s in assigned_only_schedules],
                    active=True,
                    starts_at__lte=query_end,
                    ends_at__gte=query_start,
                )
                for a in assignments:
                    matching_assigned_ids.add(a.fee_schedule_id)
                    assignment_dates[str(a.fee_schedule_id)] = {
                        'assignmentStart': a.starts_at,
                        'assignmentEnd': a.ends_at,
                    }
            except Exception as e:
                import logging
                logging.getLogger(__name__).warning('Failed to fetch fee assignments: %s', e)

        # 4. Final schedule list: all AUTO + matched ASSIGNED_ONLY
        final_schedules = auto_schedules + [
            s for s in assigned_only_schedules if s.id in matching_assigned_ids
        ]

        # 5. Build paid lookup: PaymentAllocation per fee_schedule per period
        paid_by_schedule_period: dict[str, dict[str, Decimal]] = {}
        if final_schedules:
            alloc_filter = Q(
                student=student,
                transaction__transaction_type='INCOME',
                transaction__is_cancelled=False,
                fee_schedule_id__in=[s.id for s in final_schedules],
            )
            if fee_month:
                alloc_filter &= Q(period__gte=fee_month)
            if fee_month_to:
                alloc_filter &= Q(period__lte=fee_month_to)

            for pa in PaymentAllocation.objects.filter(alloc_filter).values(
                'fee_schedule_id', 'period'
            ).annotate(total=Sum('amount')):
                fs_id = str(pa['fee_schedule_id'])
                if fs_id not in paid_by_schedule_period:
                    paid_by_schedule_period[fs_id] = {}
                paid_by_schedule_period[fs_id][pa['period']] = pa['total']

        # 6. Fallback paid lookup: Transaction.category + fee_month (for legacy data)
        paid_by_category_month: dict[str, dict[str, Decimal]] = {}
        if final_schedules:
            tx_filter = Q(
                student_id=student_id,
                transaction_type='INCOME',
                is_cancelled=False,
            )
            if fee_month:
                tx_filter &= Q(fee_month__gte=fee_month)
            if fee_month_to:
                tx_filter &= Q(fee_month__lte=fee_month_to)

            for pt in Transaction.objects.filter(tx_filter).values(
                'category', 'fee_month'
            ).annotate(total=Sum('amount')):
                cat = pt['category']
                month = pt['fee_month'] or ''
                if cat not in paid_by_category_month:
                    paid_by_category_month[cat] = {}
                paid_by_category_month[cat][month] = pt['total']

        # 7. Build result
        result = []
        for s in final_schedules:
            fs_id = str(s.id)
            a_start = assignment_dates.get(fs_id, {}).get('assignmentStart')
            a_end = assignment_dates.get(fs_id, {}).get('assignmentEnd')

            # Determine valid months for this fee
            if s.frequency == 'MONTHLY' and fee_month and fee_month_to:
                all_months = _months_in_range(fee_month, fee_month_to)
                valid_months = []
                for m in all_months:
                    if a_start and m < a_start:
                        continue
                    if a_end and m > a_end:
                        continue
                    valid_months.append(m)
            elif s.frequency == 'MONTHLY' and fee_month:
                if (a_start and fee_month < a_start) or (a_end and fee_month > a_end):
                    valid_months = []
                else:
                    valid_months = [fee_month]
            else:
                valid_months = [fee_month or '']

            num_valid_months = len(valid_months)

            # Calculate paid per month
            unpaid_months = []
            schedule_paid = paid_by_schedule_period.get(fs_id, {})
            has_allocations = bool(schedule_paid)

            waiver = FeeWaiver.objects.filter(
                student=student, fee_schedule=s, active=True,
            ).first()
            expected_per_month = float(waiver.value) if waiver else float(s.amount)
            expected_total = expected_per_month * num_valid_months

            for month in valid_months:
                if has_allocations:
                    month_paid = schedule_paid.get(month, Decimal('0'))
                else:
                    month_paid = paid_by_category_month.get(s.category, {}).get(month, Decimal('0'))

                if float(month_paid) < expected_per_month:
                    unpaid_months.append(month)

            is_paid = len(unpaid_months) == 0 and num_valid_months > 0

            item = {
                'feeScheduleId': fs_id,
                'category': s.category,
                'feeScheduleAmount': float(s.amount),
                'amount': expected_per_month,
                'frequency': s.frequency,
                'applicability': s.applicability,
                'paid': is_paid,
                'numMonths': num_valid_months,
                'expectedTotal': expected_total,
                'unpaidMonths': unpaid_months,
            }
            if a_start:
                item['assignmentStart'] = a_start
            if a_end:
                item['assignmentEnd'] = a_end
            result.append(item)

        return Response(result)

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

    @action(detail=False, methods=['get'])
    def defaulter(self, request):
        params = request.query_params
        class_name = _param(request, 'class_name', 'className')
        student_id = _param(request, 'student_id', 'studentId')
        fee_category = _param(request, 'fee_category', 'feeCategory')
        month_from = _param(request, 'month_from', 'monthFrom')
        month_to = _param(request, 'month_to', 'monthTo')
        year_str = _param(request, 'year') or str(timezone.now().year)

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
            assn_filter = Q(
                student_id__in=student_ids,
                fee_schedule__in=monthly_schedules,
                active=True,
            )
            if month_from and month_to:
                assn_filter &= Q(starts_at__lte=month_to) & Q(ends_at__gte=month_from)
            assn = StudentFeeAssignment.objects.filter(assn_filter).values_list('student_id', 'fee_schedule_id')
            assigned = {(s, fs) for s, fs in assn}

        # Fetch assigned only
        yearly_assigned = set()
        assigned_only_yearly = [fs for fs in yearly_schedules if fs.applicability == 'ASSIGNED_ONLY']
        if assigned_only_yearly and student_ids:
            ya_filter = Q(
                student_id__in=student_ids,
                fee_schedule__in=assigned_only_yearly,
                active=True,
            )
            if month_from and month_to:
                ya_filter &= Q(starts_at__lte=month_to) & Q(ends_at__gte=month_from)
            yearly_assigned = set(
                StudentFeeAssignment.objects.filter(ya_filter).values_list('student_id', 'fee_schedule_id')
            )

        paid_allocations = PaymentAllocation.objects.filter(
            student_id__in=student_ids,
        ).values('student_id', 'fee_schedule_id', 'period').annotate(total=Sum('amount'))

        paid_map = {}
        for pa in paid_allocations:
            key = (pa['student_id'], pa['fee_schedule_id'], pa['period'] or '')
            paid_map[key] = float(pa['total'])

        waiver_map = {}
        waivers = FeeWaiver.objects.filter(
            student_id__in=student_ids, active=True,
        ).values('student_id', 'fee_schedule_id', 'value')
        for w in waivers:
            waiver_map[(w['student_id'], w['fee_schedule_id'])] = float(w['value'])

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

                amt = waiver_map.get((sid, fs.id), float(fs.amount))
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

                amt = waiver_map.get((sid, fs.id), float(fs.amount))
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
