from time import sleep

from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse
from posts.models import Post, User

from yatube.settings import CACHE_TIMEOUT


class CachePagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.guest_client = Client()
        cls.user = User.objects.create_user(username='tim')
        cls.post1 = Post.objects.create(
            text='тестовый',
            author=cls.user
        )
        cls.post2 = Post.objects.create(
            text='удаляемый',
            author=cls.user
        )

    def exp(self, responce):
        return responce._headers['expires'][1]

    def test_cashe_timeout(self):
        """Cache обновляется раз в CACHE_TIMEOUT секунд."""
        response = self.guest_client.get(reverse('posts:index'))
        sleep(CACHE_TIMEOUT * 0.95)
        response2 = self.guest_client.get(reverse('posts:index'))
        sleep(CACHE_TIMEOUT * 0.1)
        response3 = self.guest_client.get(reverse('posts:index'))
        self.assertEqual(
            self.exp(response), self.exp(response2), 'кэш стёрт слишком рано'
        )
        self.assertLess(
            self.exp(response), self.exp(response3), 'кэш стёрт слишком поздно'
        )

    def test_index_page_cashe_shows_deleted_post(self):
        """Свежеудалённый пост остаётся в cashe"""
        self.guest_client.get(reverse('posts:index'))
        Post.objects.filter(id=2).delete()
        delete_response = self.guest_client.get(reverse('posts:index'))
        self.assertContains(delete_response, self.post2.text)
        cache.clear()
        clear_response = self.guest_client.get(reverse('posts:index'))
        self.assertEqual(
            clear_response.context['page_obj'][0].text, self.post1.text
        )
