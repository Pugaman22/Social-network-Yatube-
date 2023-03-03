from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.core.cache import cache

from posts.models import Post, Group


User = get_user_model()


class PostURLTests(TestCase):
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
            author=PostURLTests.user,
            text='Тестовый пост',
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(PostURLTests.user)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            '/': 'posts/index.html',
            f'/group/{self.group.slug}/': 'posts/group_list.html',
            f'/profile/{self.user.username}/': 'posts/profile.html',
            f'/posts/{self.post.id}/': 'posts/post_detail.html',
            '/create/': 'posts/create_post.html',
            f'/posts/{self.post.id}/edit/': 'posts/create_post.html',
        }

        cache.clear()
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_guest_client_url_exists_at_desired_location(self):
        """Страницы из списка доступны любому пользователю."""
        adress = [
            '/',
            '/group/test-slug/',
            '/profile/no_name/',
            '/posts/1/'
        ]
        for url in adress:
            with self.subTest(url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, 200)

    def test_authorized_client_url_exists_at_desired_location(self):
        """Страница /create/ доступна авторизованному пользователю."""
        response = self.authorized_client.get('/create/')
        self.assertEqual(response.status_code, 200)
        response = self.guest_client.get('/create/')
        self.assertEqual(response.status_code, 302)

    def test_nonexistent_page_exists_at_desired_location(self):
        """Страница /nonexistent_page/ выдает ошибку 404."""
        response = self.guest_client.get('/nonexistent_page/')
        self.assertEqual(response.status_code, 404)

    def test_posts_post_id_edit_url_exists_at_author(self):
        """Страница /posts/post_id/edit/ доступна только автору."""
        user = User.objects.create(username='name')
        client = Client()
        client.force_login(user)
        response = client.get('/posts/1/edit/')
        self.assertEqual(response.status_code, 302)
        response = self.authorized_client.get('/posts/1/edit/')
        self.assertEqual(response.status_code, 200)
