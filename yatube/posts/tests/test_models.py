from django.test import TestCase

from posts.models import Comment, Follow, Group, Post, User


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test-user')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            text='Тест' * 5,
            author=cls.user,
            group=cls.group
        )
        cls.comment = Comment.objects.create(
            post=cls.post,
            author=cls.user,
            text='Комментарий' * 5
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        self.assertEqual(self.group.title, str(self.group))
        self.assertEqual(self.comment.text[:15], str(self.comment))
        self.assertEqual(Post.STR_METOD_TEMPLATE.format(
            text=self.post.text,
            date=self.post.pub_date,
            author=self.post.author,
            group=self.post.group
        ), str(self.post))

    def test_fields_verbose_name(self):
        """verbose_name в полях совпадает с ожидаемым."""
        field_verboses = {
            Group: {
                'title': 'Заголовок',
                'slug': 'Идентификатор',
                'description': 'Описание',
            },
            Post: {
                'text': 'Содержание',
                'pub_date': 'Дата публикации',
                'author': 'Автор',
                'group': 'Группа',
                'image': 'Изображение',
            },
            Comment: {
                'post': 'Пост',
                'author': 'Автор',
                'text': 'Текст комментария',
                'pub_date': 'Дата публикации',
            },
            Follow: {
                'user': 'Подписчик',
                'author': 'Автор',
            }
        }
        for model in field_verboses.keys():
            for value, expected in field_verboses[model].items():
                with self.subTest(value=value):
                    self.assertEqual(
                        model._meta.get_field(value).verbose_name, expected
                    )
