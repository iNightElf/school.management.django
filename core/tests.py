from django.test import TestCase
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from django.core.cache import cache
from .models import SchoolClass, Subject, AcademicYear, Category
from students.models import Student

User = get_user_model()


def _auth(client):
    user = User.objects.create_superuser(email='admin@test.com', name='Admin', password='testpass123')
    refresh = RefreshToken.for_user(user)
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    return user


class ClassTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        _auth(self.client)

    def test_create_class(self):
        res = self.client.post('/api/classes/', {'name': 'Class 5'})
        self.assertEqual(res.status_code, 201)
        self.assertEqual(SchoolClass.objects.count(), 1)

    def test_list_classes(self):
        SchoolClass.objects.create(name='Class 5', order=1)
        SchoolClass.objects.create(name='Class 6', order=2)
        res = self.client.get('/api/classes/')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.data['results']), 2)

    def test_delete_class(self):
        c = SchoolClass.objects.create(name='Class 5', order=1)
        res = self.client.delete(f'/api/classes/{c.id}/')
        self.assertEqual(res.status_code, 204)
        self.assertEqual(SchoolClass.objects.count(), 0)

    def test_reorder_classes(self):
        c1 = SchoolClass.objects.create(name='Class 5', order=2)
        c2 = SchoolClass.objects.create(name='Class 6', order=1)
        res = self.client.post('/api/classes/reorder/', {'order': [str(c1.id), str(c2.id)]})
        self.assertEqual(res.status_code, 200)

    def test_class_serializer_fields(self):
        c = SchoolClass.objects.create(name='Class 5', order=1)
        res = self.client.get(f'/api/classes/{c.id}/')
        self.assertIn('studentCount', res.data)
        self.assertIn('order', res.data)


class SubjectTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        _auth(self.client)
        self.klass = SchoolClass.objects.create(name='Class 5', order=1)

    def test_create_subject(self):
        res = self.client.post(f'/api/classes/{self.klass.id}/subjects/', {'name': 'Math', 'fullMarks': 100})
        self.assertEqual(res.status_code, 201)
        self.assertEqual(Subject.objects.count(), 1)

    def test_list_subjects(self):
        Subject.objects.create(name='Math', full_marks=100, school_class=self.klass)
        Subject.objects.create(name='English', full_marks=100, school_class=self.klass)
        res = self.client.get(f'/api/classes/{self.klass.id}/subjects/')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.data['results']), 2)

    def test_update_subject(self):
        s = Subject.objects.create(name='Math', full_marks=100, school_class=self.klass)
        res = self.client.put(f'/api/subjects/{s.id}/', {'name': 'Advanced Math', 'fullMarks': 150})
        self.assertEqual(res.status_code, 200)
        s.refresh_from_db()
        self.assertEqual(s.name, 'Advanced Math')

    def test_delete_subject(self):
        s = Subject.objects.create(name='Math', full_marks=100, school_class=self.klass)
        res = self.client.delete(f'/api/subjects/{s.id}/')
        self.assertEqual(res.status_code, 204)

    def test_subject_serializer_fields(self):
        s = Subject.objects.create(name='Math', full_marks=100, school_class=self.klass)
        res = self.client.get(f'/api/subjects/{s.id}/')
        self.assertIn('fullMarks', res.data)
        self.assertIn('classId', res.data)


class AcademicYearTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        _auth(self.client)

    def test_create_academic_year(self):
        res = self.client.post('/api/academic-years/', {
            'name': '2027', 'isActive': True,
            'startDate': '2027-01-01', 'endDate': '2027-12-31'
        })
        self.assertEqual(res.status_code, 201)
        self.assertEqual(AcademicYear.objects.count(), 1)
        self.assertTrue(res.data['isActive'])

    def test_list_academic_years(self):
        AcademicYear.objects.create(name='2026', start_date='2026-01-01', end_date='2026-12-31')
        res = self.client.get('/api/academic-years/')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.data['results']), 1)

    def test_serializer_camelcase(self):
        y = AcademicYear.objects.create(name='2026', start_date='2026-01-01', end_date='2026-12-31', is_active=True)
        res = self.client.get(f'/api/academic-years/{y.id}/')
        self.assertIn('isActive', res.data)
        self.assertIn('startDate', res.data)
        self.assertIn('endDate', res.data)
        self.assertIn('createdAt', res.data)

    def test_set_active_year(self):
        y1 = AcademicYear.objects.create(name='2026', start_date='2026-01-01', end_date='2026-12-31', is_active=True)
        y2 = AcademicYear.objects.create(name='2027', start_date='2027-01-01', end_date='2027-12-31')
        res = self.client.patch(f'/api/academic-years/{y2.id}/', {'isActive': True})
        self.assertEqual(res.status_code, 200)
        y1.refresh_from_db()
        y2.refresh_from_db()
        self.assertFalse(y1.is_active)
        self.assertTrue(y2.is_active)


class CategoryTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        _auth(self.client)

    def test_create_category(self):
        res = self.client.post('/api/categories/', {'type': 'INCOME', 'name': 'Tuition Fee'})
        self.assertEqual(res.status_code, 201)
        self.assertEqual(Category.objects.count(), 1)

    def test_list_categories(self):
        Category.objects.create(type='INCOME', name='Tuition')
        Category.objects.create(type='EXPENSE', name='Salary')
        res = self.client.get('/api/categories/')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.data['results']), 2)

    def test_filter_categories(self):
        Category.objects.create(type='INCOME', name='Tuition')
        Category.objects.create(type='EXPENSE', name='Salary')
        res = self.client.get('/api/categories/?type=INCOME')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.data['results']), 1)


class SettingsTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        _auth(self.client)

    def test_get_settings(self):
        from .models import SchoolSetting
        SchoolSetting.objects.create(key='school_name', value='Test School')
        SchoolSetting.objects.create(key='address', value='123 Main St')
        res = self.client.get('/api/settings/')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data['school_name'], 'Test School')
        self.assertEqual(res.data['address'], '123 Main St')

    def test_get_settings_default(self):
        res = self.client.get('/api/settings/')
        self.assertEqual(res.status_code, 200)
        self.assertIn('school_name', res.data)

    def test_get_settings_by_key(self):
        from .models import SchoolSetting
        SchoolSetting.objects.create(key='school_name', value='Test School')
        res = self.client.get('/api/settings/?key=school_name')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data['key'], 'school_name')
        self.assertEqual(res.data['value'], 'Test School')

    def test_update_settings(self):
        from .models import SchoolSetting
        SchoolSetting.objects.create(key='school_name', value='Old Name')
        res = self.client.put(
            '/api/settings/',
            {'school_name': 'New Name', 'address': '456 Oak Ave'},
            format='json',
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data['school_name'], 'New Name')
        self.assertEqual(res.data['address'], '456 Oak Ave')
        self.assertEqual(SchoolSetting.objects.get(key='school_name').value, 'New Name')
        self.assertEqual(SchoolSetting.objects.get(key='address').value, '456 Oak Ave')


class PromoteAllTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        _auth(self.client)
        self.c1 = SchoolClass.objects.create(name='Test Class 1', order=8)
        self.c2 = SchoolClass.objects.create(name='Test Class 2', order=9)
        self.c3 = SchoolClass.objects.create(name='Test Class 3', order=10)
        self.s1 = Student.objects.create(name='Alice', student_id='r9998001', school_class=self.c1, session='old')
        self.s2 = Student.objects.create(name='Bob', student_id='r9998101', school_class=self.c2, session='old')
        self.s3 = Student.objects.create(name='Charlie', student_id='r9998201', school_class=self.c3, session='old')

    def tearDown(self):
        Student.objects.filter(id__in=[self.s1.id, self.s2.id, self.s3.id]).delete()
        SchoolClass.objects.filter(order__in=[8, 9, 10, 11, 12]).delete()

    def test_dry_run_does_not_modify(self):
        self.client.post('/api/classes/promote-all/?dryRun=true', {'targetYearName': '2027'}, format='json')
        self.s1.refresh_from_db()
        self.assertEqual(self.s1.school_class, self.c1)
        self.assertEqual(self.s1.student_id, 'r9998001')

    def test_promote_moves_students(self):
        self.client.post('/api/classes/promote-all/', {'targetYearName': '2027'}, format='json')
        self.s1.refresh_from_db()
        self.s2.refresh_from_db()
        self.s3.refresh_from_db()
        self.assertEqual(self.s1.school_class, self.c2)
        self.assertEqual(self.s2.school_class, self.c3)
        self.assertEqual(self.s3.school_class.order, 11)
        self.assertIsNone(self.s3.graduated_at)

    def test_session_updated(self):
        self.client.post('/api/classes/promote-all/', {'targetYearName': '2027'}, format='json')
        self.s1.refresh_from_db()
        self.assertEqual(self.s1.session, '2027')

    def test_roll_numbers_updated(self):
        self.client.post('/api/classes/promote-all/', {'targetYearName': '2027'}, format='json')
        self.s1.refresh_from_db()
        self.s2.refresh_from_db()
        self.assertEqual(self.s1.student_id, 'r20270101')
        self.assertEqual(self.s2.student_id, 'r20270201')

    def test_empty_body_rejected(self):
        res = self.client.post('/api/classes/promote-all/', {}, format='json')
        self.assertEqual(res.status_code, 400)

    def test_hyphen_url_works(self):
        res = self.client.post('/api/classes/promote-all/?dryRun=true', {'targetYearName': '2027'}, format='json')
        self.assertEqual(res.status_code, 200)

    def test_auto_create_class(self):
        SchoolClass.objects.filter(order__gte=8).delete()
        c = SchoolClass.objects.create(name='Test Eleven', order=11)
        s = Student.objects.create(name='AutoTest', student_id='r9998301', school_class=c, session='old')
        res = self.client.post('/api/classes/promote-all/?dryRun=true', {'targetYearName': '2027'}, format='json')
        self.assertEqual(res.status_code, 200)
        created = res.data.get('classesCreated', [])
        self.assertTrue(any('Class' in c for c in created))
        s.delete()
        c.delete()

    def test_graduation_at_max_class(self):
        SchoolClass.objects.filter(order__gte=8).delete()
        c = SchoolClass.objects.create(name='Test Twelve', order=12)
        s = Student.objects.create(name='GradTest', student_id='r9998401', school_class=c, session='old')
        res = self.client.post('/api/classes/promote-all/', {'targetYearName': '2027'}, format='json')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.data['graduated']), 1)
        s.refresh_from_db()
        self.assertIsNone(s.school_class)
        self.assertIsNotNone(s.graduated_at)


class DashboardCacheTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        _auth(self.client)
        self.klass = SchoolClass.objects.create(name='Class 5', order=1)

    def test_dashboard_cache_invalidated_on_student_create(self):
        cache.set('dashboard_summary', {'stale': True}, 60)
        Student.objects.create(name='Test', student_id='S999001', school_class=self.klass, session='2026')
        self.assertIsNone(cache.get('dashboard_summary'))

    def test_dashboard_cache_invalidated_on_student_delete(self):
        s = Student.objects.create(name='Test', student_id='S999002', school_class=self.klass, session='2026')
        cache.set('dashboard_summary', {'stale': True}, 60)
        s.delete()
        self.assertIsNone(cache.get('dashboard_summary'))
