from django import forms
from django.forms import Textarea
from .models import Post, Comment


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('text', 'group', 'image')
        labels = {
            'text': 'Текст поста',
            'group': 'Группа',
        }
        help_texts = {
            'text': 'Текст нового поста',
            'group': 'Группа, к которой будет относиться пост'
        }
        widgets = {
            'name': Textarea(attrs={'cols': 80, 'rows': 20})
        }
        error_messages = {
            'text': {
                'required': 'Заполните поле'
            },
        }


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)
        widgets = {
            'text': Textarea(attrs={'cols': 1, 'rows': 5})
        }
