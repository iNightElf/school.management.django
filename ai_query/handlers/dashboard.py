from ai_query.registry import ai_function
from accounts.permissions import is_admin_or_superuser


@ai_function(
    name="dashboard_summary",
    description="Get a quick dashboard summary of key school metrics — student counts, teacher counts, attendance, fee status.",
    permissions=["students:read"],
    parameters={
        "type": "object",
        "properties": {},
        "required": [],
    },
    result_columns=["Metric", "Value"],
)
def dashboard_summary_handler(user, **kwargs):
    from students.models import Student
    from teachers.models import Teacher
    from django.utils import timezone
    total_students = Student.objects.filter(deleted_at__isnull=True).count()
    active_students = Student.objects.filter(deleted_at__isnull=True, graduated_at__isnull=True).count()
    total_teachers = Teacher.objects.filter(deleted_at__isnull=True).count()
    
    from attendance.models import AttendanceRecord
    today = timezone.now().date()
    today_attendance = AttendanceRecord.objects.filter(date=today).count()
    today_present = AttendanceRecord.objects.filter(date=today, status='present').count()

    from finance.models import Transaction
    from core.models import AcademicYear
    yr = AcademicYear.objects.filter(is_active=True).first()
    fy = yr.name if yr else str(timezone.now().year)
    total_income = 0
    total_expense = 0
    income_qs = Transaction.objects.filter(
        transaction_type='INCOME', is_cancelled=False, fiscal_year=fy,
    )
    for t in income_qs.only('amount')[:5000]:
        total_income += float(t.amount)
    expense_qs = Transaction.objects.filter(
        transaction_type='EXPENSE', is_cancelled=False, fiscal_year=fy,
    )
    for t in expense_qs.only('amount')[:5000]:
        total_expense += float(t.amount)

    data = [
        {"Metric": "Total Students", "Value": str(total_students)},
        {"Metric": "Active Students", "Value": str(active_students)},
        {"Metric": "Total Teachers", "Value": str(total_teachers)},
        {"Metric": "Today's Attendance", "Value": str(today_attendance)},
        {"Metric": "Today's Present", "Value": str(today_present)},
        {"Metric": "Total Income FY", "Value": str(total_income)},
        {"Metric": "Total Expense FY", "Value": str(total_expense)},
    ]
    return {
        "type": "table",
        "explanation": "School dashboard summary",
        "data": data,
        "columns": ["Metric", "Value"],
    }
