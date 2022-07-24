import shutil
import tempfile

from django import forms
from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from posts.models import Comment, Group, Post, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.guest_client = Client()
        cls.user = User.objects.create_user(username='tim')
        cls.group = Group.objects.create(
            title='Тестгруппа',
            slug='gsom',
            description='тестовое описание группы',
        )
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(name='small.gif',
                                          content=cls.small_gif,
                                          content_type='image/gif')
        cls.post = Post.objects.create(
            text='Заг',
            author=cls.user,
            group=cls.group,
            image=cls.uploaded,
        )
        cls.comment = Comment.objects.create(
            post=cls.post,
            author=cls.user,
            text='комент',
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        pages_templates = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list', kwargs={'slug': self.group.slug}):
            'posts/group_list.html',
            reverse('posts:profile', kwargs={'username': self.user.username}):
            'posts/profile.html',
            reverse('posts:post_detail', kwargs={'post_id': self.post.id}):
            'posts/post_detail.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}):
            'posts/create_post.html',
        }
        for reverse_name, template in pages_templates.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_list_pages_show_correct_context(self):
        """Шаблоны страниц со списками сформированы с правильным контекстом."""
        pages = [
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': self.group.slug}),
            reverse('posts:profile', kwargs={'username': self.user.username}),
        ]
        for reverse_name in pages:
            response = self.guest_client.get(reverse_name)
            first_obj = response.context['page_obj'][0]
            context_dict = {
                first_obj.text: self.post.text,
                first_obj.author.username: self.user.username,
                first_obj.group.title: self.group.title,
                first_obj.image.name.split('/')[-1]: self.uploaded.name,
            }
            for val, expected in context_dict.items():
                with self.subTest(val=val):
                    self.assertEqual(val, expected)

    def test_post_detail_show_correct_context(self):
        """Шаблон страницы поста сформирован с правильным контекстом."""
        response = self.guest_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.id})
        )
        selected_post = response.context['post']
        selected_com = response.context['comments'][0]
        context_dict = {
            selected_post.text: self.post.text,
            selected_post.author.username: self.user.username,
            selected_post.group.title: self.group.title,
            selected_post.pk: self.post.pk,
            selected_post.image.name.split('/')[-1]: self.uploaded.name,
            selected_com.text: self.comment.text,
        }
        for val, expected in context_dict.items():
            with self.subTest(val=val):
                self.assertEqual(val, expected)

    def test_post_create_edit_show_correct_context(self):
        """Шаблон создания и правки страниц сформирован с правильным контекстом.
        """
        pages = [
            reverse('posts:post_create'),
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
        ]
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for page in pages:
            response = self.authorized_client.get(page)
            for val, expected in form_fields.items():
                with self.subTest(val=val):
                    form_field = response.context.get('form').fields.get(val)
                    self.assertIsInstance(form_field, expected)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='tim')
        cls.group = Group.objects.create(
            title='Тестгруппа',
            slug='gsom',
            description='тестовое описание группы',
        )
        cls.my_posts = {}
        for i in range(16):
            name = f'cls.post{i}'
            cls.my_posts[name] = Post.objects.create(
                text=f'Заг{i}', author=cls.user, group=cls.group)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()

    def test_paginator_contains_ten_records(self):
        """10 и 6 записей на первой и второй странице"""
        pages_posts = {
            reverse('posts:index'): 10,
            reverse('posts:group_list', kwargs={'slug': self.group.slug}): 10,
            reverse('posts:profile',
                    kwargs={'username': self.user.username}): 10,
            reverse('posts:index') + '?page=2': 6,
            reverse('posts:group_list',
                    kwargs={'slug': self.group.slug}) + '?page=2':
            6,
            reverse('posts:profile',
                    kwargs={'username': self.user.username}) + '?page=2':
            6,
        }
        for reverse_name, posts in pages_posts.items():
            response = self.authorized_client.get(reverse_name)
            self.assertEqual(len(response.context['page_obj']), posts)
