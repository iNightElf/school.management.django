from django.test import TestCase
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from students.models import Student
from core.models import SchoolClass
from .models import Result

User = get_user_model()


def _auth(client):
    user = User.objects.create_superuser(email='admin@test.com', name='Admin', password='testpass123')
    refresh = RefreshToken.for_user(user)
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    return user


class ResultTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        _auth(self.client)
        self.klass = SchoolClass.objects.create(name='Class 5', order=1)
        self.student = Student.objects.create(name='Stu', student_id='S000001', school_class=self.klass, session='2026')

    def test_save_result(self):
        res = self.client.post(f'/api/students/{self.student.id}/results/', {
            'term': 'First Term', 'session': '2026',
            'marks': {'Math': 85, 'English': 90}
        }, format='json')
        self.assertEqual(res.status_code, 201)
        self.assertEqual(Result.objects.count(), 1)

    def test_get_results(self):
        Result.objects.create(
            student=self.student, term='First Term', session='2026',
            marks={'Math': 85, 'English': 90}
        )
        res = self.client.get(f'/api/students/{self.student.id}/results/?session=2026')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.data['results']), 1)

    def test_get_results_no_session(self):
        res = self.client.get(f'/api/students/{self.student.id}/results/')
        # Session is not required by the view, returns all results for the student
        self.assertEqual(res.status_code, 200)

    def test_class_results(self):
        Result.objects.create(
            student=self.student, term='First Term', session='2026',
            marks={'Math': 85, 'English': 90}
        )
        res = self.client.get(f'/api/classes/{self.klass.id}/results/?session=2026&term=First Term')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.data), 1)

    def test_result_with_attendance(self):
        res = self.client.post(f'/api/students/{self.student.id}/results/', {
            'term': 'First Term', 'session': '2026',
            'marks': {'Math': 85},
            'attendance': {'days': 100, 'present': 95}
        }, format='json')
        self.assertEqual(res.status_code, 201)
        r = Result.objects.first()
        self.assertEqual(r.attendance['present'], 95)

    def test_result_with_comment(self):
        res = self.client.post(f'/api/students/{self.student.id}/results/', {
            'term': 'First Term', 'session': '2026',
            'marks': {'Math': 85}, 'comment': 'Good progress'
        }, format='json')
        self.assertEqual(res.status_code, 201)
        r = Result.objects.first()
        self.assertEqual(r.comment, 'Good progress')
