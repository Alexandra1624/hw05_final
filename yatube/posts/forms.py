from django import forms
# from django.forms import ModelForm
from posts.models import Post, Comment


class PostForm(forms.ModelForm):

    class Meta:
        model = Post
        fields = ['text', 'group', 'image']
        labels = {
            'text': 'Текст поста',
            'group': 'Группа'}
        help_texts = {
            'text': 'Текст нового поста',
            'group': 'Группа, к которой будет относиться пост'}


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['text']