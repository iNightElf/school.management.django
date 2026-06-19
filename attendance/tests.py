from datetime import date, timedelta
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken
from students.models import Student
from core.models import SchoolClass, SchoolSetting
from teachers.models import Teacher, ClassTeacher
from .models import AttendanceRecord, Holiday

User = get_user_model()


def _auth(client, role='admin'):
    user = User.objects.create_superuser(
        email='admin@test.com', name='Admin', password='testpass123',
    )
    refresh = RefreshToken.for_user(user)
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    return user


class AttendanceTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = _auth(self.client)
        self.klass = SchoolClass.objects.create(name='Class 5', order=1)
        self.s1 = Student.objects.create(
            name='Alice', student_id='S000001',
            school_class=self.klass, session='2026',
        )
        self.s2 = Student.objects.create(
            name='Bob', student_id='S000002',
            school_class=self.klass, session='2026',
        )

    def _today(self):
        t = timezone.now().date()
        # Make sure it's not a weekend
        while t.weekday() in (4, 5):
            t = t.replace(day=t.day - 1)
        return t

    def test_batch_mark_all_present(self):
        today = self._today()
        res = self.client.post('/api/attendance/batch/', {
            'school_class': str(self.klass.id),
            'date': today.isoformat(),
            'term': '1',
            'session': '2026',
            'records': {
                str(self.s1.id): 'present',
                str(self.s2.id): 'present',
            },
        }, format='json')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data['count'], 2)
        self.assertEqual(AttendanceRecord.objects.count(), 2)

    def test_batch_mixed_statuses(self):
        today = self._today()
        res = self.client.post('/api/attendance/batch/', {
            'school_class': str(self.klass.id),
            'date': today.isoformat(),
            'term': '1',
            'session': '2026',
            'records': {
                str(self.s1.id): 'present',
                str(self.s2.id): 'absent',
            },
        }, format='json')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(
            AttendanceRecord.objects.get(student=self.s1).status, 'present',
        )
        self.assertEqual(
            AttendanceRecord.objects.get(student=self.s2).status, 'absent',
        )

    def test_batch_upsert_updates_existing(self):
        today = self._today()
        self.client.post('/api/attendance/batch/', {
            'school_class': str(self.klass.id),
            'date': today.isoformat(),
            'term': '1',
            'session': '2026',
            'records': {str(self.s1.id): 'present'},
        }, format='json')
        res = self.client.post('/api/attendance/batch/', {
            'school_class': str(self.klass.id),
            'date': today.isoformat(),
            'term': '1',
            'session': '2026',
            'records': {str(self.s1.id): 'absent'},
        }, format='json')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(
            AttendanceRecord.objects.get(student=self.s1).status, 'absent',
        )
        self.assertEqual(AttendanceRecord.objects.count(), 1)

    def test_batch_rejects_weekend(self):
        # Find a Saturday (weekday=5)
        sat = date(2026, 6, 13)  # Saturday
        res = self.client.post('/api/attendance/batch/', {
            'school_class': str(self.klass.id),
            'date': sat.isoformat(),
            'term': '1',
            'session': '2026',
            'records': {str(self.s1.id): 'present'},
        }, format='json')
        self.assertEqual(res.status_code, 400)
        self.assertIn('weekend', res.data['error'].lower())

    def test_batch_rejects_holiday(self):
        Holiday.objects.create(date=date(2026, 6, 16), name='Eid')
        res = self.client.post('/api/attendance/batch/', {
            'school_class': str(self.klass.id),
            'date': '2026-06-16',
            'term': '1',
            'session': '2026',
            'records': {str(self.s1.id): 'present'},
        }, format='json')
        self.assertEqual(res.status_code, 400)
        self.assertIn('holiday', res.data['error'].lower())

    def test_list_by_class_and_date(self):
        today = self._today()
        self.client.post('/api/attendance/batch/', {
            'school_class': str(self.klass.id),
            'date': today.isoformat(),
            'term': '1',
            'session': '2026',
            'records': {
                str(self.s1.id): 'present',
                str(self.s2.id): 'absent',
            },
        }, format='json')
        res = self.client.get(
            f'/api/attendance/?class_id={self.klass.id}&date={today.isoformat()}',
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.data), 2)

    def test_summary_counts(self):
        today = self._today()
        self.client.post('/api/attendance/batch/', {
            'school_class': str(self.klass.id),
            'date': today.isoformat(),
            'term': '1',
            'session': '2026',
            'records': {
                str(self.s1.id): 'present',
                str(self.s2.id): 'absent',
            },
        }, format='json')
        res = self.client.get(
            f'/api/attendance/summary/'
            f'?student={self.s1.id}&term=1&session=2026',
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data['present'], 1)
        self.assertEqual(res.data['absent'], 0)
        self.assertEqual(res.data['total_school_days'], 1)

    def test_student_month_endpoint(self):
        today = self._today()
        self.client.post('/api/attendance/batch/', {
            'school_class': str(self.klass.id),
            'date': today.isoformat(),
            'term': '1',
            'session': '2026',
            'records': {str(self.s1.id): 'present'},
        }, format='json')
        res = self.client.get(
            f'/api/attendance/student/{self.s1.id}/'
            f'?year={today.year}&month={today.month}',
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data['student']['name'], 'Alice')
        marked = [d for d in res.data['days'] if d['type'] == 'marked']
        self.assertTrue(any(d['status'] == 'present' for d in marked))

    def test_holiday_crud(self):
        res = self.client.post('/api/holidays/', {
            'date': '2026-12-25',
            'name': 'Christmas',
            'type': 'public',
        }, format='json')
        self.assertEqual(res.status_code, 201)
        self.assertEqual(Holiday.objects.count(), 1)

        res = self.client.get('/api/holidays/?limit=50')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.data['results']), 1)

        hid = res.data['results'][0]['id']
        res = self.client.delete(f'/api/holidays/{hid}/')
        self.assertEqual(res.status_code, 204)
        self.assertEqual(Holiday.objects.count(), 0)


class MobileRangeReportTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.klass = SchoolClass.objects.create(name='RR Class', order=2)
        self.teacher = Teacher.objects.create(name='PIN Teacher', designation='T')
        ClassTeacher.objects.create(teacher=self.teacher, school_class=self.klass)
        self.s1 = Student.objects.create(
            name='Alice', student_id='RR0001',
            school_class=self.klass, session='2026',
        )
        self.s2 = Student.objects.create(
            name='Bob', student_id='RR0002',
            school_class=self.klass, session='2026',
        )
        today = timezone.now().date()
        while today.weekday() in (4, 5):
            today = today.replace(day=today.day - 1)
        self.at_day = today

    def _pin_token(self):
        tok = AccessToken()
        tok['teacher_id'] = str(self.teacher.id)
        tok['pin_auth'] = True
        tok.set_exp('exp', lifetime=timedelta(hours=1))
        return str(tok)

    def test_mobile_class_report_empty(self):
        token = self._pin_token()
        url = (
            '/api/m/attendance/class-report/'
            f'?class_id={self.klass.id}&from=2026-01-01&to=2026-12-31&term=1&session=2026'
        )
        res = self.client.get(url, HTTP_AUTHORIZATION=f'Bearer {token}')
        self.assertEqual(res.status_code, 200, msg=res.content[:500])
        self.assertIn('students', res.data)
        self.assertIn('dates', res.data)
        self.assertEqual(len(res.data['students']), 2)

    def test_mobile_class_report_with_records(self):
        AttendanceRecord.objects.create(
            student=self.s1, school_class=self.klass,
            date=self.at_day, term='1', session='2026', status='present',
        )
        AttendanceRecord.objects.create(
            student=self.s2, school_class=self.klass,
            date=self.at_day, term='1', session='2026', status='absent',
        )
        token = self._pin_token()
        url = (
            '/api/m/attendance/class-report/'
            f'?class_id={self.klass.id}'
            f'&from=2026-01-01&to={self.at_day.year + 1}-12-31&term=1&session=2026'
        )
        res = self.client.get(url, HTTP_AUTHORIZATION=f'Bearer {token}')
        self.assertEqual(res.status_code, 200, msg=res.content[:500])
        self.assertIn(str(self.s1.id), res.data['grid'])
        self.assertEqual(res.data['grid'][str(self.s1.id)][str(self.at_day)], 'present')
        self.assertEqual(res.data['grid'][str(self.s2.id)][str(self.at_day)], 'absent')

    def test_mobile_batch_then_class_report(self):
        token = self._pin_token()
        batch_url = '/api/m/attendance/batch/'
        batch_res = self.client.post(
            batch_url,
            {
                'school_class': str(self.klass.id),
                'date': self.at_day.isoformat(),
                'term': '1',
                'session': '2026',
                'records': {str(self.s1.id): 'present', str(self.s2.id): 'absent'},
            },
            format='json',
            HTTP_AUTHORIZATION=f'Bearer {token}',
        )
        self.assertEqual(batch_res.status_code, 200, msg=batch_res.content[:500])
        report_url = (
            '/api/m/attendance/class-report/'
            f'?class_id={self.klass.id}'
            f'&from=2026-01-01&to={self.at_day.year + 1}-12-31&term=1&session=2026'
        )
        report_res = self.client.get(report_url, HTTP_AUTHORIZATION=f'Bearer {token}')
        self.assertEqual(report_res.status_code, 200, msg=report_res.content[:500])
        self.assertEqual(report_res.data['summary'][str(self.s1.id)]['present'], 1)
        self.assertEqual(report_res.data['summary'][str(self.s2.id)]['absent'], 1)

