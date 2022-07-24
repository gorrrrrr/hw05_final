from django.test import TestCase

from ..models import Group, Post, User


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        group = PostModelTest.group
        post = PostModelTest.post
        models_str = {
            group: group.title,
            post: post.text[0:15],
        }
        for model, value in models_str.items():
            with self.subTest(model=model):
                self.assertEqual(str(model), value,
                                 f'_str_ не та в {model}')

    def test_models_have_correct_verbose_and_help_text(self):
        """Проверяем, что у моделей корректно работает verbose и help."""
        fields_verbose_help = {
            'verbose_name': {
                'text': 'Текст поста',
                'pub_date': 'Дата публикации',
                'author': 'Автор',
                'group': 'Группа'
            },
            'help_text': {
                'text': 'Текст нового поста',
                'group': 'Группа, к которой будет относиться пост',
            },
        }
        for field_type, fields in fields_verbose_help.items():
            for field, expected_value in fields.items():
                with self.subTest(field=field):
                    self.assertEqual(
                        getattr(PostModelTest.post._meta.get_field(field),
                                field_type),
                        expected_value
                    )
