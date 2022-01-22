from django.test import TestCase
from django.urls import reverse


class PostsRoutesTests(TestCase):
    def test_url_uses_correct_routes(self):
        """Проверка результата расчета urls"""
        UIDB64 = 'test-uidb64'
        TOKEN = 'test-token'
        urls_names = [
            ['/auth/signup/', 'signup', []],
            ['/auth/logout/', 'logout', []],
            ['/auth/login/', 'login', []],
            ['/auth/password_change/', 'password_change_form', []],
            ['/auth/password_change/done/', 'password_change_done', []],
            ['/auth/password_reset/', 'password_reset_form', []],
            ['/auth/password_reset/done/', 'password_reset_done', []],
            [f'/auth/reset/{UIDB64}/{TOKEN}/',
             'password_reset_confirm', [UIDB64, TOKEN]],
            ['/auth/reset/done/', 'password_reset_complete', []]
        ]
        for url, revers_url, args in urls_names:
            with self.subTest(revers_url=revers_url, url=url):
                self.assertEqual(
                    reverse(f'users:{revers_url}', args=args), url
                )
