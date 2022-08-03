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
        cls.user = User.objects.create_user(username='tim')
        cls.post1 = Post.objects.create(
            text='тестовый',
            author=cls.user
        )
        cls.post2 = Post.objects.create(
            text='удаляемый',
            author=cls.user
        )

    def setUp(self):
        self.guest_client = Client()
        cache.clear()

    def exp(self, response):
        """играя с get-запросом кэшируемой страницы, заметил,
        что в _headers есть элемент Expires. В нём указано время обращения,
        если запрашивается информация из БД. А если запрашивается кэш,
        то время когда кэш сформирован."""
        return response._headers['expires'][1]

    def test_cache_timeout(self):
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

    def test_index_page_cache_shows_deleted_post(self):
        """Свежеудалённый пост остаётся в cache"""
        self.guest_client.get(reverse('posts:index'))
        Post.objects.filter(id=2).delete()
        delete_response = self.guest_client.get(reverse('posts:index'))
        self.assertContains(delete_response, self.post2.text)
        """Здесь по сути то же самое. пост создан в setupslass, дальше
        делается запрос, который создаёт кэш. Мы удаляем пост и вторым
        запросом убеждаемся, что мы всё ещё видим информацию из кэша."""
        cache.clear()
        clear_response = self.guest_client.get(reverse('posts:index'))
        self.assertEqual(
            clear_response.context['page_obj'][0].text, self.post1.text
        )
        """А тут проверяем, что после очистки кэша в первом объекте страницы
        будет текст поста, предыдущего по отношению к удалённому."""
