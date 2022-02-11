from django.db import models
from django.contrib.auth import get_user_model
from django.db.models import UniqueConstraint

User = get_user_model()

NUM_SYMBOLS = 15


class Group(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=300, unique=True)
    description = models.TextField(max_length=400)

    def __str__(self):
        return self.title


class Post(models.Model):
    text = models.TextField(
        'Текст поста',
        help_text='Введите текст поста'
    )
    pub_date = models.DateTimeField(
        'Дата публикации',
        auto_now_add=True
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='posts',
        verbose_name='Автор'
    )
    group = models.ForeignKey(
        Group,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='posts',
        verbose_name='Группа',
        help_text='Выберите группу'
    )
    # Поле для картинки (необязательное)
    image = models.ImageField(
        'Картинка',
        upload_to='posts/',
        blank=True
    )

    class Meta:
        ordering = ['-pub_date']
        verbose_name = 'Пост'
        verbose_name_plural = 'Посты'

    def __str__(self):
        return self.text[:NUM_SYMBOLS]


class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE,
                             related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE,
                               related_name='comments')

    text = models.TextField(
        help_text='Здесь следует ввести текст комментария'
    )

    created = models.DateTimeField(auto_now_add=True)
    active = models.BooleanField(default=False)

    class Meta:
        ordering = ['created']


class Follow(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE,
                               verbose_name='Подписка',
                               related_name='following',
                               help_text='Подписан на')
    user = models.ForeignKey(User, on_delete=models.CASCADE,
                             verbose_name='Подписчик',
                             related_name='follower',
                             help_text='Подписчик',
                             null=True)

    class Meta:
        UniqueConstraint(fields=['author', 'user'], name='follow_unique')
