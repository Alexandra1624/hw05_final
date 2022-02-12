from django.test import Client, TestCase
from http import HTTPStatus


class CorePagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.guest_client = Client()

    def test_error_page(self):
        """При запросе несуществующей страницы сервер возвращает код 404."""
        response = self.guest_client.get('/nonexist-page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertTemplateUsed(response, 'core/404.html')
