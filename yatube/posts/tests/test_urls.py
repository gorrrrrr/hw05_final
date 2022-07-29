from http import HTTPStatus

from django.core.cache import cache
from django.test import Client, TestCase

from posts.models import Group, Post, User


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='HasNoName')
        cls.group = Group.objects.create(
            title='Тестгруппа',
            slug='testgroup',
            description='тестовое описание группы'
        )
        cls.post = Post.objects.create(
            text='Заг',
            author=cls.user,
            group=cls.group,
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        url_templates_names = {
            '/': 'posts/index.html',
            f'/group/{self.group.slug}/': 'posts/group_list.html',
            f'/profile/{self.user.username}/': 'posts/profile.html',
            f'/posts/{self.post.id}/': 'posts/post_detail.html',
            f'/posts/{self.post.id}/edit/': 'posts/create_post.html',
            '/create/': 'posts/create_post.html',
        }
        for address, template in url_templates_names.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_urls_unexisted_page(self):
        """URL-адрес несуществующей страницы ничего не выдаёт."""
        resps = (
            self.guest_client.get('/unexisting_page/'),
            self.authorized_client.get('/unexisting_page/'),
        )
        for response in resps:
            self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_urls_for_authorised(self):
        """Страницы доступны авторизованному пользователю."""
        urls = (
            '/',
            f'/group/{self.group.slug}/',
            f'/profile/{self.user.username}/',
            f'/posts/{self.post.id}/',
            f'/posts/{self.post.id}/edit/',
            '/create/',
        )
        for url in urls:
            response = self.authorized_client.get(url)
            self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_access_for_guest(self):
        """Страницы доступны гостю."""
        urls = (
            '/',
            f'/group/{self.group.slug}/',
            f'/profile/{self.user.username}/',
            f'/posts/{self.post.id}/',
        )
        for url in urls:
            response = self.guest_client.get(url)
            self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_redirect_for_guest(self):
        """Страницы перенаправляют гостя."""
        urls = (
            f'/posts/{self.post.id}/edit/',
            '/create/',
        )
        for url in urls:
            response = self.guest_client.get(url)
            self.assertEqual(response.status_code, HTTPStatus.FOUND)
