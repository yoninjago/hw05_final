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
USERNAME_2 = 'following-user'
SLUG = 'test-slug'
SECOND_SLUG = 'another-slug'
INDEX = reverse('posts:index')
GROUP_URL = reverse('posts:group_list', args=[SLUG])
SECOND_GROUP_URL = reverse('posts:group_list', args=[SECOND_SLUG])
PROFILE = reverse('posts:profile', args=[USERNAME])
POST_CREATE = reverse('posts:post_create')
NUMBER_OF_POSTS = POSTS_PER_PAGE + 3
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

FOLLOW = reverse('posts:profile_follow', args=[USERNAME_2])
UNFOLLOW = reverse('posts:profile_unfollow', args=[USERNAME_2])
FOLLOW_INDEX = reverse('posts:follow_index')


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00'
            b'\x01\x00\x00\x00\x00\x21\xf9\x04'
            b'\x01\x0a\x00\x01\x00\x2c\x00\x00'
            b'\x00\x00\x01\x00\x01\x00\x00\x02'
            b'\x02\x4c\x01\x00\x3b'
        )
        cls.user = User.objects.create_user(username=USERNAME)
        cls.following_user = User.objects.create_user(username=USERNAME_2)
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
                content=small_gif,
                content_type='image/gif'
            )
        )
        cls.comment = Comment.objects.create(
            post=cls.post,
            author=cls.user,
            text='Комментарий'
        )

        cls.POST_EDIT = reverse('posts:post_edit', args=[cls.post.id])
        cls.POST_DETAIL = reverse('posts:post_detail', args=[cls.post.id])

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest = Client()
        self.author = Client()
        self.author.force_login(self.following_user)
        self.another = Client()
        self.another.force_login(self.user)

    def test_index_group_list_profile_pages_show_correct_context(self):
        """Пост корректно передается на страницы."""
        for url in [INDEX, GROUP_URL, PROFILE, self.POST_DETAIL]:
            with self.subTest(url=url):
                response = self.guest.get(url)
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

    def test_post_group_correct(self):
        """Пост не попал в другие группы."""
        self.assertNotIn(
            self.post,
            self.guest.get(SECOND_GROUP_URL).context['page_obj']
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
        comment = response.context['comments'][0]
        self.assertEqual(len(response.context['comments']), 1)
        self.assertEqual(self.comment.text, comment.text)
        self.assertEqual(self.comment.author, comment.author)
        self.assertEqual(self.comment.post, comment.post)
        self.assertEqual(self.comment.id, comment.id)

    def test_index_cache(self):
        """Проверяем работу кеширования списка постов на главной странице"""
        test_post = Post.objects.create(text='deleted', author=self.user)
        response_test_post_exist = self.guest.get(INDEX)
        Post.objects.filter(pk=test_post.pk).delete()
        self.assertEquals(
            response_test_post_exist.content, self.guest.get(INDEX).content
        )
        cache.clear()
        self.assertNotEquals(
            response_test_post_exist.content, self.guest.get(INDEX).content
        )

    def test_follow_and_unfollow(self):
        """
        Авторизованный пользователь может подписываться
        на других пользователей и отписываться от них
        """
        Follow.objects.all().delete()
        self.another.get(FOLLOW)
        self.assertTrue(
            Follow.objects.filter(user=self.user, author=self.following_user)
        )
        self.another.get(UNFOLLOW)
        self.assertFalse(
            Follow.objects.filter(user=self.user, author=self.following_user)
        )

    def test_new_post_in_follow_index(self):
        """
        Новая запись пользователя появляется в ленте тех, кто на него подписан
        и не появляется у пользователей без подписки на автора
        """
        self.another.get(FOLLOW)
        new_post = Post.objects.create(
            text='Новый пост', author=self.following_user, group=self.group
        )
        response = self.another.get(FOLLOW_INDEX)
        self.assertEqual(len(response.context['page_obj']), 1)
        post = response.context['page_obj'][0]
        self.assertEqual(new_post.text, post.text)
        self.assertEqual(new_post.author, post.author)
        self.assertEqual(new_post.group, post.group)
        self.assertEqual(new_post.id, post.id)
        response = self.author.get(FOLLOW_INDEX)
        self.assertEqual(len(response.context['page_obj']), 0)
