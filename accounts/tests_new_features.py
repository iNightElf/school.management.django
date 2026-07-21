from django.test import TestCase
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from students.models import Student
from core.models import SchoolClass
from parents.models import ParentStudentLink

User = get_user_model()


class NewAuthFeatureTests(TestCase):
    """Runtime tests for the ported features:
    - logout clears auth cookies
    - change-password endpoint
    - link-child self-service parent linking (+ unlink)
    """

    def setUp(self):
        self.client = APIClient()
        self.parent = User.objects.create_user(
            email='parent@test.com', name='Parent', password='oldpass123',
            role='parent', email_verified=True,
        )
        self.klass = SchoolClass.objects.create(name='Class 5')
        self.student = Student.objects.create(
            student_id='S-001', name='Jane Doe', roll='12',
            father_name='John Doe', mother_name='Mary Doe',
            contact='01800000000', school_class=self.klass,
        )

    def _auth(self, user=None):
        u = user or self.parent
        refresh = RefreshToken.for_user(u)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')

    # ---- Logout clears cookies ----
    def test_logout_clears_auth_cookies(self):
        # log in to get cookies set
        login = self.client.post('/api/auth/login/', {
            'email': 'parent@test.com', 'password': 'oldpass123',
        })
        self.assertIn('access_token', login.cookies)
        self.assertIn('refresh_token', login.cookies)

        self._auth()
        res = self.client.post('/api/auth/logout/')
        self.assertEqual(res.status_code, 200)
        # Django sets deleted cookies with empty value + expires in the past
        self.assertIn('access_token', res.cookies)
        self.assertIn('refresh_token', res.cookies)
        at = res.cookies['access_token']
        rt = res.cookies['refresh_token']
        self.assertEqual(at.value, '')
        self.assertEqual(rt.value, '')

    # ---- Change password ----
    def test_change_password_success(self):
        self._auth()
        res = self.client.post('/api/auth/change-password/', {
            'current_password': 'oldpass123',
            'new_password': 'newpass456',
        })
        self.assertEqual(res.status_code, 200, res.data)
        self.parent.refresh_from_db()
        self.assertTrue(self.parent.check_password('newpass456'))

    def test_change_password_wrong_current(self):
        self._auth()
        res = self.client.post('/api/auth/change-password/', {
            'current_password': 'wrongpass',
            'new_password': 'newpass456',
        })
        self.assertEqual(res.status_code, 400)
        self.parent.refresh_from_db()
        self.assertTrue(self.parent.check_password('oldpass123'))

    def test_change_password_requires_auth(self):
        res = self.client.post('/api/auth/change-password/', {
            'current_password': 'oldpass123', 'new_password': 'newpass456',
        })
        self.assertEqual(res.status_code, 401)

    # ---- Link child (self-service) ----
    def test_link_child_by_details(self):
        self._auth()
        res = self.client.post('/api/auth/link-child/', {
            'child_name': 'Jane Doe',
            'phone': '01800000000',
            'father_name': 'John Doe',
            'mother_name': 'Mary Doe',
        })
        self.assertEqual(res.status_code, 201, res.data)
        self.assertTrue(
            ParentStudentLink.objects.filter(parent=self.parent, student=self.student).exists()
        )

    def test_link_child_by_student_id(self):
        self._auth()
        res = self.client.post('/api/auth/link-child/', {'student_id': 'S-001'})
        self.assertEqual(res.status_code, 201, res.data)
        self.assertTrue(
            ParentStudentLink.objects.filter(parent=self.parent, student=self.student).exists()
        )

    def test_link_child_not_found(self):
        self._auth()
        res = self.client.post('/api/auth/link-child/', {
            'child_name': 'Nobody Here', 'phone': '00000000000',
        })
        self.assertEqual(res.status_code, 400)
        self.assertFalse(ParentStudentLink.objects.exists())

    def test_link_child_already_linked(self):
        ParentStudentLink.objects.create(parent=self.parent, student=self.student)
        self._auth()
        res = self.client.post('/api/auth/link-child/', {'student_id': 'S-001'})
        self.assertEqual(res.status_code, 409)

    def test_unlink_child(self):
        ParentStudentLink.objects.create(parent=self.parent, student=self.student)
        self._auth()
        res = self.client.post('/api/auth/unlink-child/', {'studentId': str(self.student.id)})
        self.assertEqual(res.status_code, 200)
        self.assertFalse(
            ParentStudentLink.objects.filter(parent=self.parent, student=self.student).exists()
        )

    def test_link_child_requires_auth(self):
        res = self.client.post('/api/auth/link-child/', {'student_id': 'S-001'})
        self.assertEqual(res.status_code, 401)
