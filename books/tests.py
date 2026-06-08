from django.test import TestCase
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from core.models import SchoolClass
from .models import Book

User = get_user_model()


def _auth(client):
    user = User.objects.create_superuser(email='admin@test.com', name='Admin', password='testpass123')
    refresh = RefreshToken.for_user(user)
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    return user


class BookTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        _auth(self.client)
        self.klass = SchoolClass.objects.create(name='Class 5', order=1)

    def test_create_book(self):
        res = self.client.post('/api/books/', {
            'name': 'Math Book', 'publication': 'Test Pub',
            'mrp': 100, 'discounted': 90, 'sell': 85,
            'classId': str(self.klass.id),
        })
        self.assertEqual(res.status_code, 201)
        self.assertEqual(Book.objects.count(), 1)

    def test_list_books(self):
        Book.objects.create(name='Book 1', school_class=self.klass, mrp=100, discounted=90, sell=85)
        Book.objects.create(name='Book 2', school_class=self.klass, mrp=200, discounted=180, sell=170)
        res = self.client.get('/api/books/')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.data['results']), 2)

    def test_update_book(self):
        b = Book.objects.create(name='Book 1', school_class=self.klass, mrp=100, discounted=90, sell=85)
        res = self.client.patch(f'/api/books/{b.id}/', {'name': 'Updated'})
        self.assertEqual(res.status_code, 200)
        b.refresh_from_db()
        self.assertEqual(b.name, 'Updated')

    def test_delete_book(self):
        b = Book.objects.create(name='Book 1', school_class=self.klass, mrp=100, discounted=90, sell=85)
        res = self.client.delete(f'/api/books/{b.id}/')
        self.assertEqual(res.status_code, 204)

    def test_filter_books_by_class(self):
        k2 = SchoolClass.objects.create(name='Class 6', order=2)
        Book.objects.create(name='Book 1', school_class=self.klass, mrp=100, discounted=90, sell=85)
        Book.objects.create(name='Book 2', school_class=k2, mrp=200, discounted=180, sell=170)
        res = self.client.get(f'/api/books/?class_id={self.klass.id}')
        self.assertEqual(len(res.data['results']), 1)
