from django.test import Client, TestCase
from django.urls import reverse

from posts.models import User

SIGNUP = reverse('users:signup')
LOGOUT = reverse('users:logout')
LOGIN = reverse('users:login')
PASSWORD_CHANGE = reverse('users:password_change_form')
PASSWORD_CHANGE_DONE = reverse('users:password_change_done')
PASSWORD_RESET = reverse('users:password_reset_form')
PASSWORD_RESET_DONE = reverse('users:password_reset_done')
PASSWORD_RESET_CONFIRM = reverse('users:password_reset_confirm', args=[
    'test-uidb64', 'test-token'])
PASSWORD_RESET_COMPLETE = reverse('users:password_reset_complete')


class UsersURLTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='test-user')
        self.authorized = Client()
        self.authorized.force_login(self.user)

    def test_urls_uses_correct_templates(self):
        """URL-адреса используют соответствующие шаблоны."""
        url_templates_names = {
            SIGNUP: 'users/signup.html',
            LOGIN: 'users/login.html',
            PASSWORD_CHANGE: 'users/password_change_form.html',
            PASSWORD_CHANGE_DONE: 'users/password_change_done.html',
            PASSWORD_RESET: 'users/password_reset_form.html',
            PASSWORD_RESET_DONE: 'users/password_reset_done.html',
            PASSWORD_RESET_CONFIRM: 'users/password_reset_confirm.html',
            PASSWORD_RESET_COMPLETE: 'users/password_reset_complete.html',
            LOGOUT: 'users/logged_out.html',
        }
        for url, template in url_templates_names.items():
            with self.subTest(url=url):
                self.assertTemplateUsed(
                    self.authorized.get(url), template
                )
