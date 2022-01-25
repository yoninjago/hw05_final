from django.db import models
from django.contrib.auth import get_user_model

from core.models import CreatedModel

User = get_user_model()


class Group(models.Model):
    title = models.CharField(max_length=200, verbose_name='Заголовок')
    slug = models.SlugField(unique=True, verbose_name='Идентификатор')
    description = models.TextField(verbose_name='Описание')

    class Meta:
        verbose_name = 'Группа'
        verbose_name_plural = 'Группы'

    def __str__(self) -> str:
        return self.title


class Post(CreatedModel):
    text = models.TextField(
        verbose_name='Содержание',
        help_text='Текст нового поста'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='posts',
        verbose_name='Автор'
    )
    group = models.ForeignKey(
        Group,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name='posts',
        verbose_name='Группа',
        help_text='Группа, к которой будет относиться пост'
    )
    image = models.ImageField(
        upload_to='posts/',
        blank=True,
        verbose_name='Изображение',
        help_text='Прикрепите картинку к посту'
    )

    class Meta(CreatedModel.Meta):
        verbose_name = 'Пост'
        verbose_name_plural = 'Посты'

    STR_METOD_TEMPLATE = (
        'Пост: {text:.15}... '
        'Дата публикации: {date:%d %b %Y}. '
        'Автор: {author}. '
        'Группа: {group}. '
    )

    def __str__(self) -> str:
        return self.STR_METOD_TEMPLATE.format(
            text=self.text,
            date=self.pub_date,
            author=self.author.username,
            group=self.group
        )


class Comment(CreatedModel):
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Пост'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Автор'
    )
    text = models.TextField(
        verbose_name='Текст комментария',
        help_text='Введите текст комментария'
    )

    class Meta(CreatedModel.Meta):
        verbose_name = 'Комментарий'
        verbose_name_plural = 'Комментарии'

    def __str__(self) -> str:
        return self.text[:15]


class Follow(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower',
        verbose_name='Подписчик'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name='Автор'
    )

    class Meta:
        models.UniqueConstraint(
            fields=['author', 'user'], name='unique_follow'
        )
        verbose_name = 'Подписка на авторов'
        verbose_name_plural = 'Подписки на авторов'

    def __str__(self) -> str:
        return (f'Подписка пользователя {self.user.username} '
                f'на автора {self.author.username}')
