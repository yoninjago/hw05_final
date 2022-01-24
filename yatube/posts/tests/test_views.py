import shutil
import tempfile

from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings, Client, TestCase
from django.urls import reverse

from posts.models import Comment, Follow, Group, Post, User
from posts.settings import POSTS_PER_PAGE

USERNAME = 'test-user'
USERNAME_2 = 'follower'
SLUG = 'test-slug'
SECOND_SLUG = 'another-slug'
INDEX = reverse('posts:index')
GROUP_URL = reverse('posts:group_list', args=[SLUG])
SECOND_GROUP_URL = reverse('posts:group_list', args=[SECOND_SLUG])
PROFILE = reverse('posts:profile', args=[USERNAME])
POST_CREATE = reverse('posts:post_create')
NUMBER_OF_POSTS = POSTS_PER_PAGE + 3
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
FOLLOW = reverse('posts:profile_follow', args=[USERNAME])
UNFOLLOW = reverse('posts:profile_unfollow', args=[USERNAME])
FOLLOW_INDEX = reverse('posts:follow_index')
SMALL_GIF = (
    b'\x47\x49\x46\x38\x39\x61\x01\x00'
    b'\x01\x00\x00\x00\x00\x21\xf9\x04'
    b'\x01\x0a\x00\x01\x00\x2c\x00\x00'
    b'\x00\x00\x01\x00\x01\x00\x00\x02'
    b'\x02\x4c\x01\x00\x3b'
)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username=USERNAME)
        cls.follower = User.objects.create_user(username=USERNAME_2)
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug=SLUG,
            description='Тестовое описание',
        )
        cls.group_2 = Group.objects.create(
            title="Другая группа",
            slug=SECOND_SLUG,
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
        cls.comment = Comment.objects.create(
            post=cls.post,
            author=cls.user,
            text='Комментарий'
        )
        cls.guest = Client()
        cls.author = Client()
        cls.author.force_login(cls.user)
        cls.another = Client()
        cls.another.force_login(cls.follower)

        cls.POST_EDIT = reverse('posts:post_edit', args=[cls.post.id])
        cls.POST_DETAIL = reverse('posts:post_detail', args=[cls.post.id])

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_index_group_list_profile_pages_show_correct_context(self):
        """Пост корректно передается на страницы."""
        Follow.objects.create(user=self.follower, author=self.user)
        for url in [INDEX, GROUP_URL, PROFILE, self.POST_DETAIL, FOLLOW_INDEX]:
            with self.subTest(url=url):
                response = self.another.get(url)
                if 'page_obj' in response.context:
                    self.assertEqual(
                        len(response.context['page_obj']), 1
                    )
                    post = response.context['page_obj'][0]
                else:
                    post = response.context['post']
                self.assertEqual(self.post.text, post.text)
                self.assertEqual(self.post.author, post.author)
                self.assertEqual(self.post.group, post.group)
                self.assertEqual(self.post.id, post.id)
                self.assertEqual(self.post.image, post.image)

    def test_group_list_page_show_correct_context(self):
        """Контекст страницы group_list содержит правильную группу"""
        group = self.guest.get(
            GROUP_URL).context.get('group')
        self.assertEqual(self.group.title, group.title)
        self.assertEqual(self.group.slug, group.slug)
        self.assertEqual(self.group.description, group.description)
        self.assertEqual(self.group.id, group.id)

    def test_profile_page_show_correct_context(self):
        """Контекст страницы профиля пользователя
        содержит правильного пользователя"""
        self.assertEqual(
            self.user,
            self.guest.get(PROFILE).context.get('author')
        )

    def test_post_group_and_post_feed_correct(self):
        """Пост не попал в другие группы или ленты постов."""
        Follow.objects.create(user=self.follower, author=self.user)
        urls = [SECOND_GROUP_URL, FOLLOW_INDEX]
        for url in urls:
            with self.subTest(url=url):
                self.assertNotIn(
                    self.post,
                    self.author.get(url).context['page_obj']
                )

    def test_paginator(self):
        Post.objects.all().delete()
        Post.objects.bulk_create((Post(
            text=f'Тест_{post_id}',
            author=self.user,
            group=self.group
        ) for post_id in range(NUMBER_OF_POSTS)))
        cases = {
            INDEX: POSTS_PER_PAGE,
            GROUP_URL: POSTS_PER_PAGE,
            PROFILE: POSTS_PER_PAGE,
            INDEX + '?page=2': NUMBER_OF_POSTS - POSTS_PER_PAGE,
            GROUP_URL + '?page=2': NUMBER_OF_POSTS - POSTS_PER_PAGE,
            PROFILE + '?page=2': NUMBER_OF_POSTS - POSTS_PER_PAGE
        }
        for url, posts_per_page in cases.items():
            with self.subTest(url=url, posts_per_page=posts_per_page):
                self.assertEqual(
                    len(self.guest.get(url).context['page_obj']),
                    posts_per_page
                )

    def test_post_detail_page_show_correct_context(self):
        """Комментарий корректно передается на страницу."""
        response = self.guest.get(self.POST_DETAIL)
        comment = response.context['post'].comments.all()[0]
        self.assertEqual(len(response.context['post'].comments.all()), 1)
        self.assertEqual(self.comment.text, comment.text)
        self.assertEqual(self.comment.author, comment.author)
        self.assertEqual(self.comment.post, comment.post)
        self.assertEqual(self.comment.id, comment.id)

    def test_index_cache(self):
        """Проверяем работу кеширования списка постов на главной странице"""
        response_posts_exist = self.guest.get(INDEX)
        Post.objects.all().delete()
        self.assertEquals(
            response_posts_exist.content, self.guest.get(INDEX).content
        )
        cache.clear()
        self.assertNotEquals(
            response_posts_exist.content, self.guest.get(INDEX).content
        )

    def test_follow(self):
        """Авторизованный пользователь может подписываться на авторов"""
        Follow.objects.all().delete()
        self.another.get(FOLLOW)
        self.assertTrue(
            Follow.objects.filter(user=self.follower, author=self.user)
        )

    def test_unfollow(self):
        """Авторизованный пользователь может отписываться от авторов"""
        self.another.get(FOLLOW)
        self.another.get(UNFOLLOW)
        self.assertFalse(
            Follow.objects.filter(user=self.follower, author=self.user)
        )
