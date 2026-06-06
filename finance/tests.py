from django.test import TestCase
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from students.models import Student
from core.models import SchoolClass, AcademicYear
from .models import Transaction, FeeSchedule, PaymentAllocation, StudentFeeAssignment, OpeningBalance, PeriodClose, FeeWaiver, BankAccount

User = get_user_model()


def _auth(client):
    user = User.objects.create_superuser(email='admin@test.com', name='Admin', password='testpass123')
    refresh = RefreshToken.for_user(user)
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    return user


class FinanceTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        _auth(self.client)
        self.klass = SchoolClass.objects.create(name='Class 5', order=1)
        self.year = AcademicYear.objects.create(name='2026', start_date='2026-01-01', end_date='2026-12-31', is_active=True)
        self.student = Student.objects.create(name='Stu', student_id='S000001', school_class=self.klass, session='2026')
        self.fs = FeeSchedule.objects.create(
            academic_year=self.year, school_class=self.klass,
            category='Tuition', amount=1000, frequency='MONTHLY', applicability='AUTO'
        )
        self.bank_ar, _ = BankAccount.objects.get_or_create(name='AL_RAWA_BANK', display_name='AL RAWA Bank')
        self.bank_gf, _ = BankAccount.objects.get_or_create(name='GLOBAL_FORUM_BANK', display_name='Global Forum Bank')
        self.bank_cash, _ = BankAccount.objects.get_or_create(name='CASH_IN_HAND', display_name='Cash in Hand')

    def _tx_data(self, **kw):
        data = {
            'transaction_date': '2026-06-01',
            'transaction_type': 'INCOME',
            'amount': 500,
            'description': 'Test payment',
            'student': str(self.student.id),
            'class_name': 'Class 5',
            'destination_account': 'AL_RAWA_BANK',
            'fee_month': '2026-06',
        }
        data.update(kw)
        return data

    # ── Transactions ──

    def test_create_transaction(self):
        res = self.client.post('/api/finance/transactions/', self._tx_data())
        self.assertEqual(res.status_code, 201)
        self.assertEqual(Transaction.objects.count(), 1)

    def test_create_expense(self):
        res = self.client.post('/api/finance/transactions/', self._tx_data(transaction_type='EXPENSE', source_account='CASH_IN_HAND'))
        self.assertEqual(res.status_code, 201)

    def test_create_internal_transfer(self):
        res = self.client.post('/api/finance/transactions/', self._tx_data(
            transaction_type='INTERNAL_TRANSFER', source_account='CASH_IN_HAND',
            destination_account='AL_RAWA_BANK'
        ))
        self.assertEqual(res.status_code, 201)

    def test_list_transactions(self):
        Transaction.objects.create(
            transaction_date='2026-06-01', transaction_type='INCOME',
            amount=500, description='Test', student=self.student,
            destination_account=self.bank_ar, fiscal_year=2026
        )
        res = self.client.get('/api/finance/transactions/')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.data['results']), 1)

    def test_cancel_transaction(self):
        tx = Transaction.objects.create(
            transaction_date='2026-06-01', transaction_type='INCOME',
            amount=500, description='Test', student=self.student,
            destination_account=self.bank_ar, fiscal_year=2026,
        )
        res = self.client.post(f'/api/finance/transactions/{tx.id}/cancel/', {'reason': 'Cancelled by test'})
        self.assertEqual(res.status_code, 200)
        tx.refresh_from_db()
        self.assertTrue(tx.is_cancelled)

    def test_cancel_already_cancelled(self):
        tx = Transaction.objects.create(
            transaction_date='2026-06-01', transaction_type='INCOME',
            amount=500, description='Test', student=self.student,
            destination_account=self.bank_ar, fiscal_year=2026, is_cancelled=True,
        )
        res = self.client.post(f'/api/finance/transactions/{tx.id}/cancel/', {'reason': 'Again'})
        self.assertEqual(res.status_code, 400)

    def test_balances(self):
        Transaction.objects.create(
            transaction_date='2026-06-01', transaction_type='INCOME',
            amount=1000, description='Test', student=self.student,
            destination_account=self.bank_ar, fiscal_year=2026
        )
        res = self.client.get('/api/finance/balances/')
        self.assertEqual(res.status_code, 200)
        self.assertIsInstance(res.data, dict)
        self.assertIn('AL_RAWA_BANK', res.data)

    def test_dashboard_summary(self):
        Transaction.objects.create(
            transaction_date='2026-06-01', transaction_type='INCOME',
            amount=1000, description='Test', student=self.student,
            destination_account=self.bank_ar, fiscal_year=2026
        )
        res = self.client.get('/api/finance/dashboard-summary/?fiscal_year=2026')
        self.assertEqual(res.status_code, 200)
        self.assertIn('totalIncome', res.data)
        self.assertEqual(float(res.data['totalIncome']), 1000.0)

    def test_fee_status(self):
        Transaction.objects.create(
            transaction_date='2026-06-01', transaction_type='INCOME',
            amount=500, description='Fee', student=self.student,
            destination_account=self.bank_ar, fiscal_year=2026,
            fee_month='2026-06', category='Tuition'
        )
        res = self.client.get(f'/api/finance/fee-status/?student_id={self.student.id}')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.data), 1)

    # ── Fee Schedules ──

    def test_create_fee_schedule(self):
        res = self.client.post('/api/finance/fee-schedules/', {
            'academic_year_id': str(self.year.id),
            'class_id': str(self.klass.id),
            'category': 'Sports',
            'amount': 500,
            'frequency': 'YEARLY',
            'applicability': 'AUTO',
        }, format='json')
        self.assertEqual(res.status_code, 201)
        self.assertEqual(FeeSchedule.objects.count(), 2)

    def test_list_fee_schedules(self):
        res = self.client.get('/api/finance/fee-schedules/')
        self.assertEqual(res.status_code, 200)
        self.assertGreaterEqual(len(res.data), 1)

    def test_update_fee_schedule(self):
        res = self.client.patch(f'/api/finance/fee-schedules/{self.fs.id}/', {'amount': 2000})
        self.assertEqual(res.status_code, 200)
        self.fs.refresh_from_db()
        self.assertEqual(float(self.fs.amount), 2000)

    def test_delete_fee_schedule(self):
        res = self.client.delete(f'/api/finance/fee-schedules/{self.fs.id}/')
        self.assertEqual(res.status_code, 204)
        self.assertEqual(FeeSchedule.objects.count(), 0)

    def test_fee_schedule_serializer_has_class_rel(self):
        res = self.client.get(f'/api/finance/fee-schedules/{self.fs.id}/')
        self.assertIn('classRel', res.data)
        self.assertEqual(res.data['classRel']['name'], 'Class 5')

    def test_fee_schedule_serializer_camelcase(self):
        res = self.client.get(f'/api/finance/fee-schedules/{self.fs.id}/')
        self.assertIn('academicYearId', res.data)
        self.assertIn('classId', res.data)
        self.assertIn('frequency', res.data)

    # ── Student Fee Assignments ──

    def test_toggle_assignment(self):
        fs2 = FeeSchedule.objects.create(
            academic_year=self.year, category='Lab', amount=300,
            frequency='MONTHLY', applicability='ASSIGNED_ONLY'
        )
        res = self.client.post('/api/finance/student-fee-assignments/toggle/', {
            'studentId': str(self.student.id),
            'feeScheduleId': str(fs2.id),
            'active': True,
        })
        self.assertEqual(res.status_code, 200)
        self.assertEqual(StudentFeeAssignment.objects.count(), 1)

    def test_bulk_assign(self):
        fs2 = FeeSchedule.objects.create(
            academic_year=self.year, school_class=self.klass, category='Lab', amount=300,
            frequency='MONTHLY', applicability='ASSIGNED_ONLY'
        )
        res = self.client.post('/api/finance/student-fee-assignments/bulk/', {
            'classId': str(self.klass.id),
            'feeScheduleId': str(fs2.id),
        })
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data['assigned'], 1)

    # ── Fee Waivers ──

    def test_create_fee_waiver(self):
        res = self.client.post('/api/finance/fee-waivers/', {
            'student': str(self.student.id),
            'fee_schedule': str(self.fs.id),
            'value': 200,
            'reason': 'Discount',
        })
        self.assertEqual(res.status_code, 201)

    def test_deactivate_waiver(self):
        w = FeeWaiver.objects.create(
            student=self.student, fee_schedule=self.fs,
            value=200, reason='Discount', active=True
        )
        res = self.client.post(f'/api/finance/fee-waivers/{w.id}/deactivate/')
        self.assertEqual(res.status_code, 200)
        w.refresh_from_db()
        self.assertFalse(w.active)

    # ── Payment Allocations ──

    def test_payment_allocation_created_with_transaction(self):
        tx = Transaction.objects.create(
            transaction_date='2026-06-01', transaction_type='INCOME',
            amount=1000, description='Fee', student=self.student,
            destination_account=self.bank_ar, fiscal_year=2026
        )
        alloc = PaymentAllocation.objects.create(
            transaction=tx, fee_schedule=self.fs,
            student=self.student, period='2026-06', amount=1000
        )
        self.assertEqual(PaymentAllocation.objects.count(), 1)

    # ── Opening Balances ──

    def test_set_opening_balance(self):
        res = self.client.post('/api/finance/opening-balances/', {
            'fiscal_year': 2026, 'account': 'AL_RAWA_BANK', 'amount': 5000,
        })
        self.assertEqual(res.status_code, 201)
        self.assertEqual(OpeningBalance.objects.count(), 1)

    def test_get_opening_balances(self):
        OpeningBalance.objects.create(fiscal_year=2026, account=self.bank_ar, amount=5000)
        res = self.client.get('/api/finance/opening-balances/')
        self.assertEqual(res.status_code, 200)
        accounts = [item['account'] for item in res.data]
        self.assertIn('AL_RAWA_BANK', accounts)

    def test_opening_balance_history(self):
        ob = OpeningBalance.objects.create(fiscal_year=2026, account=self.bank_ar, amount=5000)
        res = self.client.patch(f'/api/finance/opening-balances/{ob.id}/', {'amount': 6000})
        self.assertEqual(res.status_code, 200)
        res = self.client.get('/api/finance/opening-balances/history/')
        self.assertEqual(res.status_code, 200)
        self.assertGreaterEqual(len(res.data), 1)

    def test_revert_opening_balance(self):
        from .models import OpeningBalanceHistory
        ob = OpeningBalance.objects.create(fiscal_year=2026, account=self.bank_ar, amount=5000)
        self.client.patch(f'/api/finance/opening-balances/{ob.id}/', {'amount': 6000})
        hist = OpeningBalanceHistory.objects.first()
        res = self.client.post(f'/api/finance/opening-balances/revert/{hist.id}/')
        self.assertEqual(res.status_code, 200)
        ob.refresh_from_db()
        self.assertEqual(float(ob.amount), 5000)

    # ── Period Close ──

    def test_period_close(self):
        res = self.client.post('/api/finance/period-closes/', {'fiscal_year': 2026})
        self.assertEqual(res.status_code, 201)
        self.assertEqual(PeriodClose.objects.count(), 1)

    def test_period_close_duplicate(self):
        PeriodClose.objects.create(fiscal_year=2026)
        res = self.client.post('/api/finance/period-closes/', {'fiscal_year': 2026})
        self.assertEqual(res.status_code, 400)

    # ── Defaulter ──

    def test_defaulter_endpoint(self):
        res = self.client.get('/api/finance/defaulter/?year=2026&monthFrom=2026-01&monthTo=2026-06')
        self.assertEqual(res.status_code, 200)
        self.assertIsInstance(res.data, list)

    def test_defaulter_with_class_filter(self):
        res = self.client.get('/api/finance/defaulter/?year=2026&className=Class 5')
        self.assertEqual(res.status_code, 200)

    # ── CamelCase Query Params ──

    def test_fee_status_with_camelcase_student_id(self):
        Transaction.objects.create(
            transaction_date='2026-06-01', transaction_type='INCOME',
            amount=500, description='Fee', student=self.student,
            destination_account=self.bank_ar, fiscal_year=2026,
            fee_month='2026-06', category='Tuition'
        )
        res = self.client.get(f'/api/finance/fee-status/?studentId={self.student.id}')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.data), 1)

    def test_fee_waivers_with_camelcase_params(self):
        FeeWaiver.objects.create(
            student=self.student, fee_schedule=self.fs,
            value=200, reason='Discount', active=True
        )
        res = self.client.get(f'/api/finance/fee-waivers/?studentId={self.student.id}&feeScheduleId={self.fs.id}&active=true')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.data), 1)

    def test_fee_waivers_with_snake_case_params(self):
        FeeWaiver.objects.create(
            student=self.student, fee_schedule=self.fs,
            value=200, reason='Discount', active=True
        )
        res = self.client.get(f'/api/finance/fee-waivers/?student_id={self.student.id}&fee_schedule_id={self.fs.id}')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.data), 1)

    def test_student_fee_assignments_with_camelcase(self):
        fs2 = FeeSchedule.objects.create(
            academic_year=self.year, category='Lab', amount=300,
            frequency='MONTHLY', applicability='ASSIGNED_ONLY'
        )
        StudentFeeAssignment.objects.create(
            student=self.student, fee_schedule=fs2, active=True
        )
        res = self.client.get(f'/api/finance/student-fee-assignments/?feeScheduleId={fs2.id}&active=true')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.data), 1)

    def test_dashboard_summary_with_camelcase_fiscal_year(self):
        Transaction.objects.create(
            transaction_date='2026-06-01', transaction_type='INCOME',
            amount=1000, description='Test', student=self.student,
            destination_account=self.bank_ar, fiscal_year=2026
        )
        res = self.client.get('/api/finance/dashboard-summary/?fiscalYear=2026')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(float(res.data['totalIncome']), 1000.0)

    def test_defaulter_with_camelcase_params(self):
        res = self.client.get('/api/finance/defaulter/?className=Class 5&year=2026&monthFrom=2026-01&monthTo=2026-06')
        self.assertEqual(res.status_code, 200)
        self.assertIsInstance(res.data, list)

    def test_opening_balances_with_camelcase_fiscal_year(self):
        OpeningBalance.objects.create(fiscal_year=2026, account=self.bank_ar, amount=5000)
        res = self.client.get('/api/finance/opening-balances/?fiscalYear=2026')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.data), 1)

    def test_opening_balances_history_with_camelcase_fiscal_year(self):
        ob = OpeningBalance.objects.create(fiscal_year=2026, account=self.bank_ar, amount=5000)
        self.client.patch(f'/api/finance/opening-balances/{ob.id}/', {'amount': 6000})
        res = self.client.get('/api/finance/opening-balances/history/?fiscalYear=2026')
        self.assertEqual(res.status_code, 200)
        self.assertGreaterEqual(len(res.data), 1)

    # ── Transaction Create via POST (camelCase body) ──

    def test_create_transaction_with_camelcase_body(self):
        res = self.client.post('/api/finance/transactions/', {
            'transactionDate': '2026-06-01',
            'transactionType': 'INCOME',
            'amount': 500,
            'description': 'CamelCase body test',
            'studentId': str(self.student.id),
            'className': 'Class 5',
            'destinationAccount': 'AL_RAWA_BANK',
            'feeMonth': '2026-06',
        })
        self.assertEqual(res.status_code, 201)
        self.assertEqual(Transaction.objects.count(), 1)

    def test_create_expense_with_camelcase_body(self):
        res = self.client.post('/api/finance/transactions/', {
            'transactionDate': '2026-06-01',
            'transactionType': 'EXPENSE',
            'amount': 300,
            'description': 'Expense test',
            'sourceAccount': 'CASH_IN_HAND',
            'category': 'Stationery',
        })
        self.assertEqual(res.status_code, 201)
        tx = Transaction.objects.first()
        self.assertEqual(tx.transaction_type, 'EXPENSE')
        self.assertEqual(tx.category, 'Stationery')

    def test_transaction_serializer_camelcase(self):
        tx = Transaction.objects.create(
            transaction_date='2026-06-01', transaction_type='INCOME',
            amount=500, description='Test', student=self.student,
            destination_account=self.bank_ar, fiscal_year=2026
        )
        res = self.client.get(f'/api/finance/transactions/{tx.id}/')
        self.assertIn('transactionType', res.data)
        self.assertIn('studentId', res.data)
        self.assertIn('sourceAccount', res.data)
        self.assertIn('destinationAccount', res.data)
        self.assertIn('feeMonth', res.data)
        self.assertIn('isCancelled', res.data)
        self.assertEqual(res.data['sourceAccount'], None)
        self.assertEqual(res.data['destinationAccount'], 'AL_RAWA_BANK')
