from datetime import date
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from students.models import Student
from core.models import SchoolClass, SchoolSetting
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
            'records': {str(self.s1.id): 'late'},
        }, format='json')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(
            AttendanceRecord.objects.get(student=self.s1).status, 'late',
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
