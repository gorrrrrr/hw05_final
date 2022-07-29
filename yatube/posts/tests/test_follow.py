from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Follow, Post, User


class FollowTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_author = User.objects.create_user(username='timon')
        cls.user_reader = User.objects.create_user(username='pumba')

    def setUp(self):
        self.guest_client = Client()
        self.client_reader = Client()
        self.client_reader.force_login(self.user_reader)
        self.client_author = Client()
        self.client_author.force_login(self.user_author)
        cache.clear()

    def test_authorized_user_can_follow(self):
        """Авторизованный пользователь может подписываться на других
        пользователей и удалять их из подписок."""
        self.client_reader.get(reverse('posts:profile_follow', kwargs={
            'username': self.user_author.username})
        )
        follow_check = self.client_reader.get(
            reverse('posts:profile', kwargs={'username':
                                             self.user_author.username})
        )
        self.assertContains(follow_check, 'Отписаться')
        self.assertEqual(Follow.objects.count(), 1)

        self.client_reader.get(reverse('posts:profile_unfollow', kwargs={
            'username': self.user_author.username})
        )
        unfollow_check = self.client_reader.get(
            reverse('posts:profile', kwargs={'username':
                                             self.user_author.username})
        )
        self.assertContains(unfollow_check, 'Подписаться')
        self.assertEqual(Follow.objects.count(), 0)

    def test_follow_page(self):
        """Новая запись пользователя появляется в ленте тех, кто
        на него подписан и не появляется в ленте тех, кто не подписан."""
        Post.objects.create(text='тестовый', author=self.user_author)
        self.client_reader.get(reverse('posts:profile_follow', kwargs={
            'username': self.user_author.username})
        )
        follow_check = self.client_reader.get(reverse('posts:follow_index'))
        self.assertContains(follow_check, 'тестовый')
        unfollow_check = self.client_author.get(reverse('posts:follow_index'))
        self.assertNotContains(unfollow_check, 'тестовый')
