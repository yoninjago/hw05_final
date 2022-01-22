from django.test import Client, TestCase
from django.urls import reverse

from posts.models import User

SIGNUP = reverse('users:signup')
INDEX = reverse('posts:index')


class UsersFormsTests(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_create_user(self):
        """Валидная форма создает запись в User."""
        users_count = User.objects.count()
        user_fields = {
            'first_name': 'Дед',
            'last_name': 'Мороз',
            'username': 'dedmoroz',
            'email': 'dedmoroz@vustyug.ru',
            'password1': 'test-password2022',
            'password2': 'test-password2022'
        }
        self.assertRedirects(self.guest_client.post(
            SIGNUP, data=user_fields, follow=True), INDEX
        )
        self.assertEqual(User.objects.count(), users_count + 1)
        self.assertTrue(User.objects.filter(
            username=user_fields['username'],
            first_name=user_fields['first_name'],
            last_name=user_fields['last_name'],
            email=user_fields['email']
        ).exists())
