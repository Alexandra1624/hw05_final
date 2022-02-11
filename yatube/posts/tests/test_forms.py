from django import forms
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from posts.models import Group, Post
from django.core.files.uploadedfile import SimpleUploadedFile

User = get_user_model()

INDEX = reverse('posts:main')
NEW_POST = reverse('posts:post_create')


class PostFormTests(TestCase):
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

    def setUp(self):
        # Неавторизованный клиент
        self.guest_client = Client()
        # Авторизованный клиент, не автор
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user_not_author)
        # Автор
        self.post_author = Client()
        self.post_author.force_login(self.user_author)

    def test_post_create(self):
        """Корректное отображение созданного поста."""
        post = Post.objects.first()
        post.delete()

        SMALL_GIF = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )

        UPLOADED_GIF = SimpleUploadedFile(
            name='small.gif',
            content=SMALL_GIF,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Текст формы',
            'group': self.group.id,
            'image': UPLOADED_GIF,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        post = response.context['page_obj'][0]
        image_data = form_data['image']
        self.assertEqual(len(response.context['page_obj']), 1)
        self.assertEqual(post.text, form_data['text'])
        self.assertEqual(post.group, self.group)
        self.assertEqual(post.author, self.user_not_author)
        self.assertEqual(post.image.size, image_data.size)
        self.assertRedirects(response, reverse(
            'posts:profile', kwargs={'username': 'user_not_author'})
        )

    def test_create_post_show_correct_context(self):
        """Шаблон create_post сформирован с правильным контекстом."""
        urls = [
            reverse('posts:post_create'),
            reverse('posts:post_edit', kwargs={'post_id': self.post.id})
        ]
        for url in urls:
            response = self.post_author.get(url)
            form_fields = {
                'text': forms.fields.CharField,
                'group': forms.fields.Field,
                'image': forms.fields.ImageField,
            }
            for value, expected in form_fields.items():
                with self.subTest(value=value):
                    form_field = response.context.get('form').fields.get(value)
                    self.assertIsInstance(form_field, expected)

    def test_post_edit_save(self):
        """Корректное отображение post_edit. """
        SM_GIF = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        UPLOADED2 = SimpleUploadedFile(
            name='sm.gif',
            content=SM_GIF,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Другой текст!',
            'group': self.group2.id,
            'image': UPLOADED2,
        }
        response = self.post_author.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
            data=form_data, follow=True
        )
        '''Пост должен поменяться'''
        post = response.context['post']
        image_data = form_data['image']
        self.assertEqual(post.text, form_data['text'])
        self.assertEqual(post.group, self.group2)
        self.assertEqual(post.author, self.post.author)
        self.assertEqual(post.image.size, image_data.size)
        self.assertRedirects(response, reverse(
            'posts:post_detail', kwargs={'post_id': self.post.id})
        )

    def test_comment_save(self):
        """Корректное отображение комментария."""
        form_data = {
            'text': 'Текст Комментария!',
            'post': self.post.id,
            'author': self.user_author,
        }
        response = self.post_author.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.id}),
            data=form_data, follow=True
        )
        self.assertEqual(len(response.context['comment']), 1)
        comment = response.context['comment'][0]
        self.assertEqual(comment.text, form_data['text'])
        self.assertEqual(comment.post, self.post)
        self.assertEqual(comment.author, self.user_author)
