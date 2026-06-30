from datetime import date
from django.db import models
from ai_query.registry import ai_function
from accounts.permissions import is_admin_or_superuser


@ai_function(
    name="fee_status",
    description="Get fee payment status for a student including schedules, payments, and waivers.",
    permissions=["finance:read"],
    parameters={
        "type": "object",
        "properties": {
            "student_id": {
                "type": "string",
                "description": "Student ID to check fee status for",
            },
            "month_from": {
                "type": "string",
                "description": "Start month (YYYY-MM)",
            },
            "month_to": {
                "type": "string",
                "description": "End month (YYYY-MM)",
            },
        },
        "required": ["student_id"],
    },
    result_columns=["Category", "Amount", "Paid", "Due", "Waiver", "Status"],
)
def fee_status_handler(user, student_id="", month_from=None, month_to=None):
    from students.models import Student
    from finance.services.fee_status_service import FeeStatusService
    student = Student.objects.filter(deleted_at__isnull=True, student_id__iexact=student_id).first()
    if not student:
        return {
            "type": "summary",
            "explanation": f"No student found with ID '{student_id}'",
            "data": [], "columns": [],
        }
    svc = FeeStatusService(str(student.id), month_from, month_to)
    status_data = svc.get_status()
    if not status_data:
        return {
            "type": "summary",
            "explanation": f"No fee data for {student.name}",
            "data": [], "columns": [],
        }
    data = []
    for item in status_data.get('schedules', []):
        data.append({
            "Category": item.get('category', ''),
            "Amount": str(item.get('expected', 0)),
            "Paid": str(item.get('paid', 0)),
            "Due": str(item.get('due', 0)),
            "Waiver": str(item.get('waiver', 0)),
            "Status": item.get('status', ''),
        })
    return {
        "type": "table",
        "explanation": f"Fee status for {student.name} ({student.student_id})",
        "data": data,
        "columns": ["Category", "Amount", "Paid", "Due", "Waiver", "Status"],
    }


@ai_function(
    name="defaulter_report",
    description="Get a report of students with unpaid fee balances, filtered by class or month.",
    permissions=["finance:read"],
    parameters={
        "type": "object",
        "properties": {
            "class_name": {
                "type": "string",
                "description": "Class name to filter (e.g. 'Class 7', 'Seven')",
            },
            "month_from": {
                "type": "string",
                "description": "Start month (YYYY-MM)",
            },
            "month_to": {
                "type": "string",
                "description": "End month (YYYY-MM)",
            },
        },
        "required": [],
    },
    result_columns=["Student", "Class", "Category", "Expected", "Paid", "Due"],
)
def defaulter_report_handler(user, class_name=None, month_from=None, month_to=None):
    from finance.services.defaulter_service import DefaulterService
    svc = DefaulterService(
        class_name=class_name, month_from=month_from, month_to=month_to,
    )
    svc.resolve_year()
    qs = svc.get_student_queryset()
    students = list(qs.select_related('school_class').only('id', 'name', 'school_class__name')[:100])
    student_ids = [s.id for s in students]
    if not student_ids:
        return {
            "type": "summary",
            "explanation": "No students found",
            "data": [], "columns": [],
        }
    result_list = svc.compute(students, student_ids)
    data = []
    for entry in result_list:
        for fee_entry in entry.get('fee_details', []):
            due = float(fee_entry.get('due', 0) or 0)
            if due > 0:
                data.append({
                    "Student": entry.get('name', ''),
                    "Class": entry.get('class_name', ''),
                    "Category": fee_entry.get('category', ''),
                    "Expected": str(fee_entry.get('expected', 0)),
                    "Paid": str(fee_entry.get('paid', 0)),
                    "Due": str(due),
                })
    return {
        "type": "table",
        "explanation": f"Defaulter report — {len(data)} unpaid items found",
        "data": data[:200],
        "columns": ["Student", "Class", "Category", "Expected", "Paid", "Due"],
    }


@ai_function(
    name="ledger_query",
    description="View financial ledger transactions for a bank account with optional date range.",
    permissions=["finance:read"],
    parameters={
        "type": "object",
        "properties": {
            "account_name": {
                "type": "string",
                "description": "Bank account name",
            },
            "date_from": {
                "type": "string",
                "description": "Start date (YYYY-MM-DD)",
            },
            "date_to": {
                "type": "string",
                "description": "End date (YYYY-MM-DD)",
            },
        },
        "required": ["account_name"],
    },
    result_columns=["Date", "Description", "Category", "In", "Out", "Type"],
)
def ledger_query_handler(user, account_name="", date_from=None, date_to=None):
    from finance.services.ledger_service import LedgerService
    svc = LedgerService(account_name, date_from, date_to)
    qs = svc.build_base_queryset().filter(is_cancelled=False)
    transactions = list(qs.values(
        'transaction_date', 'description', 'category',
        'source_account__name', 'destination_account__name',
        'transaction_type', 'amount',
    ).order_by('-transaction_date')[:200])
    data = []
    for t in transactions:
        is_in = t['destination_account__name'] == account_name
        data.append({
            "Date": str(t['transaction_date']),
            "Description": (t['description'] or '')[:60],
            "Category": t['category'] or '',
            "In": str(t['amount']) if is_in else '',
            "Out": str(t['amount']) if not is_in else '',
            "Type": t['transaction_type'] or '',
        })
    return {
        "type": "table",
        "explanation": f"Ledger for {account_name} ({len(data)} entries)",
        "data": data,
        "columns": ["Date", "Description", "Category", "In", "Out", "Type"],
    }


@ai_function(
    name="fee_collected",
    description="Get total fee collection summary for current fiscal year, optionally filtered by class or month.",
    permissions=["finance:read"],
    parameters={
        "type": "object",
        "properties": {
            "class_name": {
                "type": "string",
                "description": "Class name filter (e.g. 'Class 7', 'Seven')",
            },
            "month": {
                "type": "string",
                "description": "Month filter (YYYY-MM)",
            },
        },
        "required": [],
    },
    result_columns=["Month", "Amount", "Count"],
)
def fee_collected_handler(user, class_name=None, month=None):
    from finance.models import Transaction
    from core.models import AcademicYear
    yr = AcademicYear.objects.filter(is_active=True).first()
    fy = yr.name if yr else str(date.today().year)
    qs = Transaction.objects.filter(transaction_type='INCOME', is_cancelled=False, fiscal_year=fy, category__icontains='fee')
    if class_name:
        from core.models import SchoolClass
        cls = SchoolClass.objects.filter(name__iexact=class_name).first()
        if cls:
            qs = qs.filter(school_class=cls)
        else:
            return {"type": "summary", "explanation": f"No class found with name '{class_name}'", "data": [], "columns": []}
    if month:
        qs = qs.filter(transaction_date__startswith=month)
    from django.db.models import Sum, Count
    agg = qs.values('transaction_date__startswith').annotate(total=Sum('amount'), cnt=Count('id')).order_by('-transaction_date__startswith')[:24]
    data = [{"Month": str(a['transaction_date__startswith'])[:7], "Amount": str(a['total']), "Count": str(a['cnt'])} for a in agg]
    return {"type": "table", "explanation": f"Fee collection for {fy}" + (f" — {class_name}" if class_name else ""), "data": data, "columns": ["Month", "Amount", "Count"]}


@ai_function(
    name="balances",
    description="Get current bank account balances.",
    permissions=["finance:read"],
    parameters={
        "type": "object",
        "properties": {},
        "required": [],
    },
    result_columns=["Account", "Balance"],
)
def balances_handler(user, **kwargs):
    from finance.models import BankAccount, AccountBalance
    from core.models import AcademicYear
    from decimal import Decimal
    acs = AcademicYear.objects.filter(is_active=True).first()
    year = acs.name if acs else ''
    accounts = BankAccount.objects.filter(is_active=True)
    data = []
    for acct in accounts:
        bal = AccountBalance.objects.filter(
            account=acct, fiscal_year=year,
        ).order_by('-fiscal_year', '-month').first()
        closing = bal.closing_balance if bal else Decimal('0')
        data.append({
            "Account": acct.display_name or acct.name,
            "Balance": str(closing),
        })
    return {
        "type": "table",
        "explanation": "Current bank account balances",
        "data": data,
        "columns": ["Account", "Balance"],
    }
