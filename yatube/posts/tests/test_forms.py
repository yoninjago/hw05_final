import shutil
import tempfile

from django import forms
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings, Client, TestCase
from django.urls import reverse

from posts.models import Comment, Group, Post, User

USERNAME = 'Author'
USERNAME_2 = 'Not-Author'
LOGIN = reverse('users:login')
POST_CREATE = reverse('posts:post_create')
POST_CREATE_TO_LOGIN_REDIRECT = f'{LOGIN}?next={POST_CREATE}'
PROFILE = reverse('posts:profile', args=[USERNAME])
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
SMALL_GIF = (
    b'\x47\x49\x46\x38\x39\x61\x01\x00'
    b'\x01\x00\x00\x00\x00\x21\xf9\x04'
    b'\x01\x0a\x00\x01\x00\x2c\x00\x00'
    b'\x00\x00\x01\x00\x01\x00\x00\x02'
    b'\x02\x4c\x01\x00\x3b'
)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsFormsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username=USERNAME)
        cls.user_2 = User.objects.create_user(username=USERNAME_2)
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.group_2 = Group.objects.create(
            title="Другая группа",
            slug='another-slug',
            description="Пустая группа",
        )
        cls.post = Post.objects.create(
            text='Тестовый пост',
            author=cls.user,
            group=cls.group,
            image=SimpleUploadedFile(
                name='small.gif',
                content=SMALL_GIF,
                content_type='image/gif'
            )
        )
        cls.guest = Client()
        cls.author = Client()
        cls.author.force_login(cls.user)
        cls.another = Client()
        cls.another.force_login(cls.user_2)

        cls.POST_EDIT = reverse('posts:post_edit', args=[cls.post.id])
        cls.POST_DETAIL = reverse('posts:post_detail', args=[cls.post.id])
        cls.COMMENT_CREATE = reverse('posts:add_comment', args=[cls.post.id])
        cls.POST_EDIT_TO_LOGIN_REDIRECT = f'{LOGIN}?next={cls.POST_EDIT}'
        cls.COMMENT_CREATE_TO_LOGIN_REDIRECT = (
            f"{LOGIN}?next={reverse('posts:add_comment', args=[cls.post.id])}"
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_create_post(self):
        """Валидная форма создает запись в Post."""
        Post.objects.all().delete()
        form_data = {
            'text': 'Тестирование формы',
            'group': self.group.id,
            'image': SimpleUploadedFile(
                name='new_post_gif.gif',
                content=SMALL_GIF,
                content_type='image/gif'
            )
        }
        response = self.author.post(
            POST_CREATE, data=form_data, follow=True
        )
        post = response.context['page_obj'][0]
        self.assertRedirects(response, PROFILE)
        self.assertEqual(Post.objects.count(), 1)
        self.assertEqual(form_data['text'], post.text)
        self.assertEqual(
            form_data['group'], post.group.id)
        self.assertEqual(self.user, post.author)
        self.assertEqual(
            form_data['image'].name, post.image.name.split('/')[-1]
        )

    def test_edit_post(self):
        """Валидная форма изменяет запись в Post и сохраняет с тем же id."""
        form_data = {
            'text': 'Отредактированный пост',
            'group': self.group_2.id,
            'image': SimpleUploadedFile(
                name='edit_post_gif.gif',
                content=SMALL_GIF,
                content_type='image/gif'
            )
        }
        response = self.author.post(
            self.POST_EDIT, data=form_data, follow=True)
        post = response.context['post']
        self.assertRedirects(response, self.POST_DETAIL)
        self.assertEqual(form_data['text'], post.text)
        self.assertEqual(form_data['group'], post.group.id)
        self.assertEqual(self.post.author, post.author)
        self.assertEqual(
            form_data['image'].name, post.image.name.split('/')[-1]
        )

    def test_create_post_page_show_correct_context(self):
        """Форма добавления поста сформирована с правильным контекстом"""
        form_data = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField
        }
        for value, expected in form_data.items():
            with self.subTest(value=value):
                self.assertIsInstance(
                    self.author.get(
                        POST_CREATE
                    ).context['form'].fields[value], expected)

    def test_edit_post_page_show_correct_context(self):
        """Форма изменения поста сформирована с правильным контекстом"""
        fields_expected_values = {
            'text': self.post.text,
            'group': self.post.group.id,
            'image': self.post.image
        }
        for value, expected in fields_expected_values.items():
            with self.subTest(value=value):
                self.assertEqual(
                    self.author.get(
                        self.POST_EDIT
                    ).context['form'].initial[value], expected)

    def test_create_comment(self):
        """Валидная форма создает запись в Comment."""
        Comment.objects.all().delete()
        form_data = {'text': 'Тестирование формы'}
        response = self.author.post(
            self.COMMENT_CREATE, data=form_data, follow=True
        )
        comment = response.context['post'].comments.all()[0]
        self.assertEqual(
            Comment.objects.get(post=self.post).post, comment.post
        )
        self.assertRedirects(response, self.POST_DETAIL)
        self.assertEqual(Comment.objects.count(), 1)
        self.assertEqual(form_data['text'], comment.text)
        self.assertEqual(self.user, comment.author)
        self.assertEqual(self.post, comment.post)

    def test_create_post_guest(self):
        """Анонимный пользователь не может создать запись в Post."""
        Post.objects.all().delete()
        response = self.guest.post(
            POST_CREATE, data={'text': 'Тестирование формы'}, follow=True
        )
        self.assertRedirects(response, POST_CREATE_TO_LOGIN_REDIRECT)
        self.assertEqual(Post.objects.count(), 0)

    def test_edit_post_guest_and_not_author(self):
        """
        Анонимный пользователь или не автор поста
        не может изменить запись в POST.
        """
        cases = [
            [self.guest, self.POST_EDIT_TO_LOGIN_REDIRECT],
            [self.another, self.POST_DETAIL]
        ]
        form_data = {
            'text': 'Отредактированный пост',
            'group': self.group_2.id,
            'image': SimpleUploadedFile(
                name='edit_post_guest_gif.gif',
                content=SMALL_GIF,
                content_type='image/gif'
            )
        }
        for user, redirect_url in cases:
            with self.subTest(user=user, redirect_url=redirect_url):
                response = user.post(
                    self.POST_EDIT, data=form_data, follow=True
                )
                self.assertRedirects(response, redirect_url)
                self.assertEqual(
                    Post.objects.get(pk=self.post.id).text, self.post.text
                )
                self.assertEqual(
                    Post.objects.get(pk=self.post.id).author, self.post.author
                )
                self.assertEqual(
                    Post.objects.get(pk=self.post.id).group, self.post.group
                )
                self.assertEqual(
                    Post.objects.get(pk=self.post.id).image, self.post.image
                )

    def test_create_comment_guest(self):
        """Анонимный пользователь не может создать запись в Comment."""
        Comment.objects.all().delete()
        response = self.guest.post(
            self.COMMENT_CREATE, data={'text': 'Анонимная запись'}, follow=True
        )
        self.assertRedirects(response, self.COMMENT_CREATE_TO_LOGIN_REDIRECT)
        self.assertEqual(Comment.objects.count(), 0)
