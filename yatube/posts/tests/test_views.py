from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Group, Post, Follow, Comment
from django.core.cache import cache
User = get_user_model()

POSTS = 10


class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_author = User.objects.create(username='user_author')
        cls.user_not_author = User.objects.create(username='user_not_author')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.group2 = Group.objects.create(
            title='Тестовая группа2',
            slug='test-slug2',
            description='Тестовое описание2',
        )
        cls.post = Post.objects.create(
            author=cls.user_author,
            text='Текст поста',
            group=cls.group,
        )
        cls.comment = Comment.objects.create(
            post=cls.post,
            author=cls.user_author,
            text='Текст Комментария'
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

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        # Собираем в словарь пары "reverse(name):имя_html_шаблона"
        cache.clear()
        templates_pages_names = {
            reverse('posts:main'): 'posts/index.html',
            reverse('posts:group_posts', kwargs={'slug': 'test-slug'}):
                'posts/group_list.html',
            reverse('posts:profile', kwargs={'username': 'user_author'}):
                'posts/profile.html',
            reverse('posts:post_detail', kwargs={'post_id': self.post.id}):
                'posts/post_detail.html',
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}):
                'posts/create_post.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse('posts:follow_index'): 'posts/follow.html',
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.post_author.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        cache.clear()
        for post in Post.objects.all():
            response = self.guest_client.get(reverse('posts:main'))
            page_obj = response.context['page_obj']
            self.assertIn(post, page_obj)

    def test_group_list_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response_group = self.guest_client.get(
            reverse('posts:group_posts', kwargs={'slug': 'test-slug'})
        )
        group_test = response_group.context.get('group')
        self.assertEqual(group_test, self.group)

    def test_profile_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.post_author.get(
            reverse('posts:profile', kwargs={'username': 'user_author'})
        )
        author_test = response.context.get('author')
        self.assertEqual(self.user_author, author_test)

    def test_post_detail_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.post_author.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.id})
        )
        self.assertEqual(response.context['post'].text, self.post.text)
        self.assertEqual(response.context['post'].id, self.post.id)
        self.assertEqual(response.context['post'].group, self.post.group)
        self.assertEqual(response.context['post'].author, self.post.author)
        self.assertEqual(len(response.context['comment']), 1)
        self.assertEqual(self.comment, response.context.get('comment')[0])

    def test_post_create_show_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""
        response = self.post_author.get(
            reverse('posts:post_create')
        )
        self.assertIn("form", response.context)

    def test_post_edit_show_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        response = self.post_author.get(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id})
        )
        first_obj = response.context.get('post')
        post_0 = first_obj.author
        self.assertEqual(post_0, self.post.author)

    def test_post_in_url(self):
        """При создании поста с группой он появляется на всех страницах."""
        cache.clear()
        reverse_names = (
            reverse('posts:main'),
            reverse('posts:group_posts', kwargs={'slug': self.group.slug}),
            reverse('posts:profile', kwargs={'username': self.user_author}),
            reverse('posts:follow_index'),
        )
        for value in reverse_names:
            with self.subTest(value=value):
                self.authorized_client.get(
                    reverse(
                        'posts:profile_follow',
                        kwargs={'username': self.user_author}
                    )
                )
                response = self.authorized_client.get(value)
                self.assertEqual(Post.objects.count(), 1)
                self.assertEqual(self.post,
                                 response.context.get('page_obj')[0])

    def test_post_not_in_group2(self):
        """Пост не отображается в другой группе"""
        response_group = self.authorized_client.get(
            reverse('posts:group_posts', kwargs={'slug': 'test-slug2'})
        )
        self.assertNotIn(self.post, response_group.context.get('page_obj'))

    def test_unfollow_index_page_null(self):
        """Пост не отображается в ленте у отписавшегося"""
        response = self.authorized_client.get(
            reverse('posts:follow_index')
        )
        self.assertEqual(len(response.context['page_obj']), 0)

    def test_follow_user(self):
        """Проверка подписки. """
        self.authorized_client.get(
            reverse('posts:profile_follow',
                    kwargs={'username': self.user_author})
        )
        follow_exist = Follow.objects.filter(user=self.user_not_author,
                                             author=self.user_author).exists()
        self.assertTrue(follow_exist)

    def test_unfollow_user(self):
        """Проверка отписки. """
        self.authorized_client.get(
            reverse('posts:profile_follow',
                    kwargs={'username': self.user_author})
        )
        self.authorized_client.get(
            reverse('posts:profile_unfollow',
                    kwargs={'username': self.user_author})
        )
        follow_exist = Follow.objects.filter(user=self.user_not_author,
                                             author=self.user_author).exists()
        self.assertFalse(follow_exist)

    def test_cache_index_page_correct_context(self):
        """Кэш index сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:main'))
        content = response.content
        post_id = PostPagesTests.post.id
        instance = Post.objects.get(pk=post_id)
        instance.delete()
        new_response = self.authorized_client.get(reverse('posts:main'))
        new_content = new_response.content
        self.assertEqual(content, new_content)
        cache.clear()
        new_new_response = self.authorized_client.get(reverse('posts:main'))
        new_new_content = new_new_response.content
        self.assertNotEqual(content, new_new_content)

    def test_error_page(self):
        response = self.client.get('/nonexist-page/')
        # Cтатус ответа сервера - 404
        self.assertEqual(response.status_code, 404)
        # Используется шаблон core/404.html
        self.assertTemplateUsed(response, 'core/404.html')


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='test_user')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание группы',
        )
        posts = [
            Post(author=cls.user, text=str(i), group=cls.group) for i in
            range(POSTS)
        ]
        Post.objects.bulk_create(posts)

    def test_page_count_records(self):
        cache.clear()
        reverse_names = (
            reverse('posts:main'),
            reverse('posts:group_posts', kwargs={'slug': self.group.slug}),
            reverse('posts:profile', kwargs={'username': self.user.username})
        )
        for reverse_name in reverse_names:
            with self.subTest(reverse_name=reverse_name):
                response = self.client.get(reverse_name)
                self.assertEqual(
                    len(response.context.get('page_obj').object_list), POSTS
                )
