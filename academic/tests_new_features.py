from django.test import TestCase
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken

from core.models import SchoolClass, Subject
from students.models import Student
from parents.models import ParentStudentLink
from academic.models import Suggestion, LeaveReason

User = get_user_model()


def auth(client, user):
    refresh = RefreshToken.for_user(user)
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')


class SuggestionLeaveReasonTests(TestCase):
    """Runtime tests for the ported parent/teacher communication features:
    Suggestion, LeaveReason, and the exam_routine_notes endpoint.
    """

    def setUp(self):
        self.client = APIClient()
        self.parent = User.objects.create_user(
            email='parent@test.com', name='Parent', password='pass123',
            role='parent', email_verified=True,
        )
        self.teacher = User.objects.create_user(
            email='teacher@test.com', name='Teacher', password='pass123',
            role='teacher', email_verified=True,
        )
        self.klass = SchoolClass.objects.create(name='Class 5')
        self.subject = Subject.objects.create(name='Math', full_marks=100, school_class=self.klass)
        self.student = Student.objects.create(
            student_id='S-1', name='Jane', school_class=self.klass,
        )
        ParentStudentLink.objects.create(parent=self.parent, student=self.student)

    def test_parent_create_suggestion(self):
        auth(self.client, self.parent)
        res = self.client.post('/api/parents/suggestions/', {
            'school_class': str(self.klass.id),
            'text': 'Please add more labs.',
        }, format='json')
        self.assertEqual(res.status_code, 201, res.data)
        self.assertTrue(
            Suggestion.objects.filter(parent=self.parent, text='Please add more labs.').exists()
        )

    def test_parent_cannot_suggest_for_unrelated_class(self):
        other = SchoolClass.objects.create(name='Class 9')
        auth(self.client, self.parent)
        res = self.client.post('/api/parents/suggestions/', {
            'school_class': str(other.id),
            'text': 'nope',
        }, format='json')
        self.assertEqual(res.status_code, 400)
        # Guard must prevent persisting a suggestion for a class the parent
        # is not linked to (the create test's own suggestion is unrelated).
        self.assertFalse(
            Suggestion.objects.filter(school_class=other).exists()
        )

    def test_parent_lists_own_suggestions(self):
        Suggestion.objects.create(parent=self.parent, school_class=self.klass, text='hi')
        other_parent = User.objects.create_user(
            email='other@test.com', name='Other', password='pass123',
            role='parent', email_verified=True,
        )
        Suggestion.objects.create(parent=other_parent, school_class=self.klass, text='theirs')
        auth(self.client, self.parent)
        res = self.client.get('/api/parents/suggestions/')
        self.assertEqual(res.status_code, 200)
        results = res.data['results']
        texts = [item['text'] for item in results]
        self.assertIn('hi', texts)
        self.assertNotIn('theirs', texts)
        self.assertEqual(len(results), 1)

    def test_parent_create_leave_reason(self):
        auth(self.client, self.parent)
        res = self.client.post('/api/parents/leave-reasons/', {
            'student': str(self.student.id),
            'reason': 'Sick',
            'start_date': '2026-08-01',
            'end_date': '2026-08-03',
        }, format='json')
        self.assertEqual(res.status_code, 201, res.data)
        self.assertTrue(
            LeaveReason.objects.filter(parent=self.parent, student=self.student).exists()
        )

    def test_exam_routine_notes_endpoint(self):
        auth(self.client, self.parent)
        res = self.client.get('/api/academic/exam-routine-notes/')
        self.assertEqual(res.status_code, 200)
        self.assertIn('notes', res.data)
