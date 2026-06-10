from datetime import datetime, date
from decimal import Decimal
from django.db.models import Sum, Q
from django.utils import timezone
from rest_framework.decorators import action
from rest_framework.response import Response

from finance.models import (
    Transaction, FeeSchedule, FeeWaiver, PaymentAllocation,
    StudentFeeAssignment, OpeningBalance, BankAccount,
)
from core.models import AcademicYear
from students.models import Student
from finance.serializers import TransactionSerializer
from .base import (
    _internal_accounts, _param, _fiscal_year_from_date,
)


class LedgerActionsMixin:
    """Ledger, fee_status, and defaulter actions for TransactionViewSet."""

    @action(detail=False, methods=['get'])
    def ledger(self, request):
        account_name = _param(request, 'account')
        if account_name not in _internal_accounts():
            return Response({'error': 'Invalid account'}, status=400)

        date_from = _param(request, 'date_from', 'dateFrom')
        date_to = _param(request, 'date_to', 'dateTo')
        search = _param(request, 'search')

        account_filter = Q(source_account__name=account_name) | Q(destination_account__name=account_name)

        all_txs = Transaction.objects.filter(
            account_filter,
        ).select_related('student', 'source_account', 'destination_account').order_by('transaction_date', 'created_at', 'id')

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

        opening_balance = Decimal('0')

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

        if date_from:
            all_txs = all_txs.filter(transaction_date__gte=date_from)
        if date_to:
            all_txs = all_txs.filter(transaction_date__lte=date_to)

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

            if not tx.is_cancelled and not tx.reversal_of_id:
                if is_outgoing:
                    running -= tx.amount
                if is_incoming:
                    running += tx.amount

            if not tx.is_cancelled and not tx.reversal_of_id:
                total_debit += debit
                total_credit += credit

            is_cancelled_or_reversal = tx.is_cancelled or bool(tx.reversal_of_id)

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

        closing_balance = opening_balance + total_debit - total_credit
        total_rows = len(full_data)

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

        class_id = student.school_class_id
        schedules = FeeSchedule.objects.filter(
            Q(school_class_id=class_id) | Q(school_class_id__isnull=True)
        ).order_by('category')

        auto_schedules = []
        assigned_only_schedules = []
        for s in schedules:
            if s.applicability == 'AUTO':
                auto_schedules.append(s)
            else:
                assigned_only_schedules.append(s)

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

        final_schedules = auto_schedules + [
            s for s in assigned_only_schedules if s.id in matching_assigned_ids
        ]

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

        result = []
        for s in final_schedules:
            fs_id = str(s.id)
            a_start = assignment_dates.get(fs_id, {}).get('assignmentStart')
            a_end = assignment_dates.get(fs_id, {}).get('assignmentEnd')

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
    def defaulter(self, request):
        params = request.query_params
        class_name = _param(request, 'class_name', 'className')
        student_id = _param(request, 'student_id', 'studentId')
        fee_category = _param(request, 'fee_category', 'feeCategory')
        month_from = _param(request, 'month_from', 'monthFrom')
        month_to = _param(request, 'month_to', 'monthTo')
        year_str = _param(request, 'year')
        if year_str:
            exact = AcademicYear.objects.filter(name=year_str).first()
            if exact:
                year_str = exact.name
            else:
                match = AcademicYear.objects.filter(name__icontains=year_str).first()
                year_str = match.name if match else year_str
        else:
            active_year = AcademicYear.objects.filter(is_active=True).first()
            year_str = active_year.name if active_year else str(timezone.now().year)

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
