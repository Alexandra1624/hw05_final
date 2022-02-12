from django.core.cache import cache
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from posts.models import Group, Post
from http import HTTPStatus

User = get_user_model()


class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_author = User.objects.create(username='user_author')
        cls.user_not_author = User.objects.create(username='user_not_author')
        cls.group = Group.objects.create(
            slug='test-slug',
        )
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.user_author,
            group=cls.group
        )

    def setUp(self):
        # Неавторизованный клиент
        self.guest_client = Client()
        # Авторизованный клиент, не автор
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user_not_author)
        # Автор
        self.post_author = Client()
        self.post_author.force_login(self.user_author)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        cache.clear()
        templates_url_names = {
            '/': 'posts/index.html',
            f'/group/{self.group.slug}/': 'posts/group_list.html',
            f'/profile/{self.user_author}/': 'posts/profile.html',
            f'/posts/{self.post.id}/': 'posts/post_detail.html',
            f'/posts/{self.post.id}/edit/': 'posts/create_post.html',
            '/create/': 'posts/create_post.html',
            '/follow/': 'posts/follow.html',
        }
        for url, template in templates_url_names.items():
            with self.subTest(url=url):
                response = self.post_author.get(url)
                self.assertTemplateUsed(response, template)

    def test_urls_status_code(self):
        urls_names = [
            ['/', self.guest_client, HTTPStatus.OK],
            [f'/group/{self.group.slug}/', self.guest_client, HTTPStatus.OK],
            [f'/profile/{self.user_author}/', self.guest_client,
                HTTPStatus.OK],
            [f'/posts/{self.post.id}/', self.guest_client, HTTPStatus.OK],

            [f'/posts/{self.post.id}/edit/', self.post_author, HTTPStatus.OK],
            [f'/posts/{self.post.id}/edit/', self.guest_client,
                HTTPStatus.FOUND],

            ['/create/', self.authorized_client, HTTPStatus.OK],
            ['/create/', self.guest_client, HTTPStatus.FOUND],

            [f'/posts/{self.post.id}/comment/', self.guest_client,
                HTTPStatus.FOUND],
            [f'/profile/{self.user_author}/follow/', self.guest_client,
                HTTPStatus.FOUND],
            [f'/profile/{self.user_author}/unfollow/', self.guest_client,
                HTTPStatus.FOUND]
        ]
        for url, client, status in urls_names:
            with self.subTest(url=url):
                self.assertEqual(client.get(url).status_code, status)

    def test_redirect_urls_correct(self):
        urls = [
            ['/create/', self.guest_client, '/auth/login/?next=/create/'],
            [f'/posts/{self.post.id}/edit/', self.guest_client,
                f'/auth/login/?next=/posts/{self.post.id}/edit/'],

            [f'/posts/{self.post.id}/edit/', self.authorized_client,
                f'/posts/{self.post.id}/'],

            [f'/posts/{self.post.id}/comment/', self.guest_client,
                f'/auth/login/?next=/posts/{self.post.id}/comment/'],

            [f'/profile/{self.user_author}/follow/', self.post_author,
                f'/profile/{self.user_author}/'],
            [f'/profile/{self.user_author}/unfollow/', self.post_author,
                f'/profile/{self.user_author}/']
        ]
        for url, client, redirect in urls:
            with self.subTest(url=url):
                self.assertRedirects(client.get(url), redirect)
