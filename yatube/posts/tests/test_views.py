import shutil
import tempfile
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings

from django.contrib.auth import get_user_model
from django.urls import reverse

from django import forms
from time import sleep

from django.core.cache import cache

from posts.models import Post, Group, Follow

User = get_user_model()


class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='StasBasov')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.posts = []
        for i in range(13):
            sleep(0.1)
            cls.posts.append(
                Post.objects.create(author=PostPagesTests.user,
                                    text='Тестовый пост' + str(i),
                                    group=cls.group)
            )
        cls.post = cls.posts[i]

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        cache.clear()
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse(
                'posts:group_list', kwargs={'slug': 'test-slug'}
            ): 'posts/group_list.html',
            reverse(
                'posts:profile', kwargs={'username': self.post.author}
            ): 'posts/profile.html',
            reverse(
                'posts:post_detail', kwargs={'post_id': self.post.id}
            ): 'posts/post_detail.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse(
                'posts:post_edit', kwargs={'post_id': self.post.id}
            ): 'posts/create_post.html',
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)
                # print("used:", template)

    def test_pagination(self):
        """паджинатор работает корректно."""
        response = self.guest_client.get(reverse('posts:index') + '?page=2')
        self.assertEqual(len(response.context['page_obj']), 3)

        response = self.guest_client.get(
            reverse('posts:group_list', kwargs={'slug': self.group.slug})
            + '?page=2')
        self.assertEqual(len(response.context['page_obj']), 3)

        response = self.guest_client.get(
            reverse('posts:profile', kwargs={'username': self.post.author})
            + '?page=2')
        self.assertEqual(len(response.context['page_obj']), 3)

    def test_index_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        cache.clear()
        response = self.guest_client.get(reverse('posts:index'))
        self.assertEqual(len(response.context['page_obj']), 10)
        post = response.context['page_obj'][0]
        self.assertEqual(self.posts[-1], post)

    def test_group_list_show_context_correct(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.guest_client.get(
            reverse('posts:group_list', kwargs={'slug': self.group.slug}))
        self.assertEqual(len(response.context['page_obj']), 10)
        self.assertEqual(self.group, response.context['group'])

    def test_profile_show_context_correct(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.guest_client.get(
            reverse('posts:profile', kwargs={'username': self.post.author}))
        self.assertEqual(len(response.context['page_obj']), 10)
        post = response.context['page_obj'][0]
        self.assertEqual(self.posts[-1], post)

    def test_post_detail_show_correct_context(self):
        response = self.guest_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.id})
        )
        self.assertEqual(response.context.get('post').author, self.post.author)
        self.assertEqual(response.context.get('post').text, self.post.text)
        self.assertEqual(response.context.get('post').group, self.post.group)

    def test_create_show_correct_context(self):
        """Шаблон create сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.models.ModelChoiceField,
        }

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_edit_post_show_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.models.ModelChoiceField,
        }

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_creation_check(self):
        """Проверка создания поста на страницах"""
        group = Group.objects.create(slug='group2',
                                     title='group2 titile',
                                     description='group2 description')
        post = Post.objects.create(text='post with group',
                                   author=PostPagesTests.user,
                                   group=group)
        cache.clear()
        form_fields = {
            reverse('posts:index'): post,
            reverse('posts:group_list', kwargs={'slug': group.slug}): post,
            reverse('posts:profile',
                    kwargs={'username': self.post.author}): post,
        }
        for url, expected in form_fields.items():
            with self.subTest(value=url):
                response = self.authorized_client.get(url)
                page_obj = response.context.get('page_obj')
                self.assertIn(expected, page_obj)

    def test_create_post_with_group(self):
        """Проверка, что пост попал в группу, для которой был предназначен."""
        group = Group.objects.create(
            slug='group2',
            title='group2 titile',
            description='group2 description')
        post = Post.objects.create(
            text='post with group',
            author=PostPagesTests.user,
            group=group)
        cache.clear()
        address = reverse('posts:index')
        response = self.guest_client.get(address)
        self.assertIn(post, response.context.get('page_obj'))
        response = self.guest_client.get(
            reverse('posts:group_list', kwargs={'slug': group.slug}))
        self.assertIn(post, response.context.get('page_obj'))
        response = self.guest_client.get(
            reverse('posts:profile', kwargs={'username': post.author.username})
        )
        self.assertIn(post, response.context.get('page_obj'))
        response = self.guest_client.get(
            reverse('posts:group_list',
                    kwargs={'slug': PostPagesTests.group.slug}))
        self.assertNotIn(post, response.context.get('page_obj'))

    def test_check_cache(self):
        """Проверка кеша.при удалении записи из базы, она остаётся в
response.content главной страницы до тех пор, пока кэш не будет очищен
принудительно."""
        response = self.guest_client.get(reverse('posts:index') + "?page=2")
        content1 = response.content
        Post.objects.get(id=1).delete()
        response = self.guest_client.get(reverse('posts:index') + "?page=2")
        content2 = response.content
        self.assertEqual(content1, content2)

        cache.clear()
        response = self.guest_client.get(reverse('posts:index') + "?page=2")
        content2 = response.content
        self.assertNotEqual(content1, content2)

    def test_404_custom_template(self):
        """страница 404 отдаёт кастомный шаблон"""
        self.assertTemplateUsed(self.guest_client.get(
            "not_existing_page"), 'core/404.html')


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

    def assert_image_from_page(self, image_path, url):
        response = self.guest_client.get(url)
        context = response.context
        page_obj = context.get("page_obj")
        post = page_obj[0]
        self.assert_post_image(image_path, post)

    def assert_post_image(self, image_path, post):
        self.assertEquals(image_path, post.image.name[:len("posts/small")])

    def test_image_is_in_context(self):
        """При выводе поста с картинкой изображение передаётся в словаре
context"""

        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        file = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        new_post = Post.objects.create(
            image=file,
            author=self.user,
            group=self.group
        )
        new_post.save()

        image_path = "posts/small"
        response = self.guest_client.get(reverse(
            'posts:post_detail', kwargs={"post_id": new_post.id}))
        context = response.context
        post = context.get("post")
        self.assert_post_image(image_path, post)
        cache.clear()
        urls = {
            reverse('posts:index'),
            reverse('posts:profile', kwargs={'username': self.user.username}),
            reverse('posts:group_list', kwargs={"slug": self.group.slug}),
        }

        for url in urls:
            with self.subTest(value=url):
                self.assert_image_from_page(image_path, url)


class FollowersTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user1 = User.objects.create(username="user1")
        cls.user2 = User.objects.create(username="user2")
        cls.user3 = User.objects.create(username="user3")

    def setUp(self):
        self.guest_client = Client()
        self.user1_client = Client()
        self.user1_client.force_login(self.user1)
        self.user2_client = Client()
        self.user2_client.force_login(self.user2)
        self.user3_client = Client()
        self.user3_client.force_login(self.user3)

    def test_guest_cant_follow_unfollow(self):
        """Неавторизованный пользователь не может подписываться на других
        пользователей и удалять их из подписок."""
        url = reverse('posts:profile_follow',
                      kwargs={"username": self.user1.username})
        response = self.guest_client.get(url)
        self.assertRedirects(response, reverse('users:login') + '?next=' + url)
        url = reverse('posts:profile_unfollow',
                      kwargs={"username": self.user1.username})
        response = self.guest_client.get(url)
        self.assertRedirects(response, reverse('users:login') + '?next=' + url)

    def test_authorized_can_follow_unfollow(self):
        """Авторизованный пользователь может подписываться на других
        пользователей и удалять их из подписок."""
        url = reverse('posts:profile_follow',
                      kwargs={"username": self.user1.username})
        response = self.user2_client.get(url)
        self.assertRedirects(response, reverse('posts:follow_index'))
        self.assertTrue(Follow.objects.filter(
            author=self.user1, user=self.user2).exists())
        url = reverse('posts:profile_unfollow',
                      kwargs={"username": self.user1.username})
        response = self.user2_client.get(url)
        self.assertRedirects(response, reverse('posts:follow_index'))
        self.assertFalse(Follow.objects.filter(
            author=self.user1, user=self.user2).exists())

    def test_follow_index(self):
        """Новая запись пользователя появляется в ленте тех,
        кто на него подписан и не появляется в ленте тех, кто не подписан."""
        post1 = Post.objects.create(author=self.user1, text="post 1")
        Follow.objects.create(author=self.user1, user=self.user2)
        url = reverse('posts:follow_index')
        response = self.user2_client.get(url)
        page_obj = response.context.get('page_obj')
        self.assertEqual(post1, page_obj[0])
        response = self.user3_client.get(url)
        page_obj = response.context.get('page_obj')
        self.assertEqual(0, len(page_obj))
