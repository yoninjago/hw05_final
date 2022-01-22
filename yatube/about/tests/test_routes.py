from django.test import TestCase
from django.urls import reverse


class AboutRoutesTests(TestCase):
    def test_url_uses_correct_routes(self):
        """Проверка результата расчета urls"""
        urls_names = [
            ['/about/author/', 'author'],
            ['/about/tech/', 'tech']
        ]
        for url, revers_url in urls_names:
            with self.subTest(revers_url=revers_url, url=url):
                self.assertEqual(
                    reverse(f'about:{revers_url}'), url
                )
