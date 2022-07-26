# Generated by Django 2.2.16 on 2022-07-20 15:00

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    replaces = [('posts', '0001_initial'),
                ('posts', '0002_auto_20220614_1513'),
                ('posts', '0003_auto_20220711_1815')]

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Group',
            fields=[
                ('id', models.AutoField(auto_created=True,
                                        primary_key=True,
                                        serialize=False,
                                        verbose_name='ID')),
                ('title', models.CharField(max_length=200,
                                           verbose_name='Название')),
                ('slug', models.SlugField(unique=True,
                                          verbose_name='Текст для ссылки')),
                ('description', models.TextField(verbose_name='Описание')),
            ],
        ),
        migrations.CreateModel(
            name='Post',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True,
                 serialize=False, verbose_name='ID')),
                ('text', models.TextField(help_text='Введите текст поста',
                 verbose_name='Текст поста')),
                ('pub_date', models.DateTimeField(auto_now_add=True,
                 verbose_name='Дата публикации')),
                ('author', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='posts', to=settings.AUTH_USER_MODEL,
                    verbose_name='Автор')),
                ('group', models.ForeignKey(
                    blank=True,
                    help_text='Группа, к которой будет относиться пост',
                    null=True, on_delete=django.db.models.deletion.SET_NULL,
                    related_name='posts', to='posts.Group',
                    verbose_name='Группа')),
            ],
            options={
                'ordering': ['-pub_date'],
            },
        ),
    ]
