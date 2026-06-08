from django.test import TestCase
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from .models import SchoolClass, Subject, AcademicYear, Category

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
        res = self.client.get('/api/settings/')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data['key'], 'school_name')
        self.assertEqual(res.data['value'], 'Test School')

    def test_update_settings(self):
        from .models import SchoolSetting
        SchoolSetting.objects.create(key='school_name', value='Old Name')
        res = self.client.patch('/api/settings/', {'value': 'New Name'})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data['value'], 'New Name')
