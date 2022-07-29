import shutil
import tempfile

from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.models import Comment, Post, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='tim')
        cls.test_post = Post.objects.create(
            text='Заг',
            author=cls.user,
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()

    def test_create_post(self):
        """Валидная форма создает запись в Post."""
        post_count = Post.objects.count()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(name='small.gif',
                                      content=small_gif,
                                      content_type='image/gif')
        form_data = {
            'text': 'Заг2',
            'author': self.user,
            'image': uploaded,
        }
        self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True,
        )
        self.assertEqual(Post.objects.count(), post_count + 1)

    def test_edit_post(self):
        """Валидная форма правит запись в Post."""
        post_count = Post.objects.count()
        form_data = {
            'text': 'Заг3',
            'author': self.user,
        }
        self.authorized_client.post(
            reverse('posts:post_edit', args={self.test_post.id}),
            data=form_data,
            follow=True,
        )
        self.test_post = Post.objects.get(id=self.test_post.id)
        self.assertEqual(Post.objects.count(),
                         post_count, 'менятся число постов!')
        self.assertTrue(
            Post.objects.filter(text=form_data['text']).exists(),
            'изменённый пост не появился в БД!'
        )
        for field, val in form_data.items():
            with self.subTest(val=val):
                self.assertEqual(
                    getattr(self.test_post, field),
                    val, 'номер поста не остался прежним!'
                )


class CommentFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.guest_client = Client()
        cls.user = User.objects.create_user(username='tim')
        cls.post = Post.objects.create(text='Заг',
                                       author=cls.user)
        cls.test_comment = Comment.objects.create(text='ком',
                                                  author=cls.user,
                                                  post=cls.post)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_comment(self):
        """Валидная форма создает запись в Comment."""
        com_count = Comment.objects.count()
        form_data = {'text': 'ком2'}
        self.authorized_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True
        )
        self.assertEqual(Comment.objects.count(), com_count + 1)

    def test_guest_do_not_create_comment(self):
        """Неавторизованый пользователь не может создать запись в Comment."""
        com_count = Comment.objects.count()
        form_data = {'text': 'ком2'}
        self.guest_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True
        )
        self.assertEqual(Comment.objects.count(), com_count)
