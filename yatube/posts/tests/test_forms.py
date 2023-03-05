import shutil
import tempfile
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model
from posts.models import Comment, Post, Group


User = get_user_model()


class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='no_name')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый текст',
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(PostFormTests.user)

    def test_create_post(self):
        """Валидная форма создает запись в Post."""
        form_data = {
            'text': 'Тестовый текст2',
            'group': self.group.id
        }
        posts_count = Post.objects.count()
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response, reverse('posts:profile',
                              kwargs={'username': self.user.username})
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)
        new_post = Post.objects.filter(text='Тестовый текст2').get()
        self.assertEqual(self.group.id, new_post.group.id)
        self.assertEqual(self.user.id, new_post.author.id)

    def test_edit_post(self):
        """Валидная форма изменяет запись в Post."""
        form_data = {
            'text': 'Новый текст',
            'group': self.group.id
        }
        post = self.post
        posts_count = Post.objects.count()
        response = self.authorized_client.post(
            reverse('posts:post_edit', args=(post.id,)),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response, reverse('posts:post_detail',
                              kwargs={'post_id': post.id})
        )
        self.assertEqual(Post.objects.count(), posts_count)
        edited_post = Post.objects.get(id=post.id)
        self.assertEqual(edited_post.text, 'Новый текст')
        self.assertEqual(edited_post.group.id, self.group.id)
        self.assertEqual(edited_post.author.id, self.user.id)

    def test_edit_post_guest(self):
        """Валидная форма гостя не изменяет запись в Post."""
        form_data = {
            'text': 'Новый текст',
            'group': self.group.id
        }
        post = self.post
        posts_count = Post.objects.count()
        response = self.guest_client.post(
            reverse('posts:post_edit', args=(post.id,)),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response, reverse('users:login') + '?next=' + reverse(
                'posts:post_edit', args=(post.id,))
        )
        self.assertEqual(Post.objects.count(), posts_count)


TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class ImageTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='no_name')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(user=self.user)

    def test_create_post_with_image(self):
        """при отправке поста с картинкой через форму PostForm создаётся
запись в базе данных"""
        posts_count = Post.objects.count()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        form_data = {
            'text': 'post with image',
            'image': uploaded,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response, reverse('posts:profile',
                              kwargs={'username': self.user.username})
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)
        new_post = Post.objects.get(
            text=form_data['text'],
            author_id=self.user.id,
            image='posts/small.gif'
        )
        self.assertEqual('posts/small.gif', new_post.image.name)


class CommentsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username="user1")
        cls.post = Post.objects.create(author=cls.user, text="post1 text")

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_only_authorized_user_can_comment(self):
        """комментировать посты может только авторизованный пользователь"""
        url = reverse('posts:add_comment', kwargs={"post_id": self.post.id})
        response = self.guest_client.get(url)
        self.assertRedirects(response, reverse('users:login') + '?next=' + url)
        count = Comment.objects.count()
        form_data = {
            'text': 'comment1',
            'post': self.post,
        }
        response = self.authorized_client.post(
            reverse('posts:add_comment', kwargs={"post_id": self.post.id}),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response, reverse('posts:post_detail',
                              kwargs={'post_id': self.post.id})
        )
        self.assertEqual(Comment.objects.count(), count + 1)
        new_comment = Comment.objects.get(
            text=form_data['text'],
            author_id=self.user.id,
            post=self.post
        )

        """после успешной отправки комментарий появляется на странице
поста"""
        response = self.guest_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.id}))
        comments = response.context.get("comments")
        self.assertEquals(comments.count(), count + 1)
        self.assertEquals(comments[0], new_comment)
