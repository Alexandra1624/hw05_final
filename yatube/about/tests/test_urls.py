from django.test import Client, TestCase
from http import HTTPStatus


class AboutPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.guest_client = Client()

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            '/about/author/': 'about/author.html',
            '/about/tech/': 'about/tech.html',
        }
        for url, template in templates_url_names.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertTemplateUsed(response, template)

    def test_urls_status_code(self):
        urls_names = [
            ['/about/author/', self.guest_client, HTTPStatus.OK],
            ['/about/tech/', self.guest_client, HTTPStatus.OK],
        ]
        for url, client, status in urls_names:
            with self.subTest(url=url):
                self.assertEqual(client.get(url).status_code, status)
