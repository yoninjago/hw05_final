from http import HTTPStatus

from django.test import Client, TestCase
from django.urls import reverse

AUTHOR = reverse('about:author')
TECH = reverse('about:tech')


class AboutURLTests(TestCase):
    def setUp(self):
        self.guest = Client()

    URLS_TEMPLATES_NAMES = {
        AUTHOR: 'about/author.html',
        TECH: 'about/tech.html'
    }

    def test_urls_exists_and_have_correct_access_rights(self):
        for url in self.URLS_TEMPLATES_NAMES.keys():
            self.assertEqual(
                self.guest.get(url).status_code, HTTPStatus.OK.value
            )

    def test_urls_uses_correct_templates(self):
        """URL-адреса используют соответствующие шаблоны."""
        for url, template in self.URLS_TEMPLATES_NAMES.items():
            with self.subTest(url=url):
                self.assertTemplateUsed(self.guest.get(url), template)
