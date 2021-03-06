from http.client import OK, FOUND, NOT_FOUND

from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Group, Post, User

USERNAME = 'Author'
USERNAME_2 = 'Not-Author'
SLUG = 'test-slug'
INDEX = reverse('posts:index')
GROUP_URL = reverse('posts:group_list', args=[SLUG])
PROFILE = reverse('posts:profile', args=[USERNAME])
POST_CREATE = reverse('posts:post_create')
LOGIN = reverse('users:login')
POST_CREATE_TO_LOGIN_REDIRECT = f'{LOGIN}?next={POST_CREATE}'
FOLLOW = reverse('posts:profile_follow', args=[USERNAME])
FOLLOW_TO_LOGIN_REDIRECT = f'{LOGIN}?next={FOLLOW}'
UNFOLLOW = reverse('posts:profile_unfollow', args=[USERNAME])
UNFOLLOW_TO_LOGIN_REDIRECT = f'{LOGIN}?next={UNFOLLOW}'
FOLLOW_INDEX = reverse('posts:follow_index')
FOLLOW_INDEX_TO_LOGIN_REDIRECT = f'{LOGIN}?next={FOLLOW_INDEX}'


class PostsURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username=USERNAME)
        cls.user_2 = User.objects.create_user(username=USERNAME_2)
        cls.group = Group.objects.create(slug=SLUG)
        cls.post = Post.objects.create(author=cls.user, group=cls.group)
        cls.guest = Client()
        cls.author = Client()
        cls.author.force_login(cls.user)
        cls.another = Client()
        cls.another.force_login(cls.user_2)

        cls.POST_EDIT = reverse('posts:post_edit', args=[cls.post.id])
        cls.POST_DETAIL = reverse('posts:post_detail', args=[cls.post.id])
        cls.POST_EDIT_TO_LOGIN_REDIRECT = f'{LOGIN}?next={cls.POST_EDIT}'

    def test_urls_exists_and_have_correct_access_rights(self):
        cases = [
            [INDEX, self.guest, OK],
            [GROUP_URL, self.guest, OK],
            [PROFILE, self.guest, OK],
            [self.POST_DETAIL, self.guest, OK],
            [self.POST_EDIT, self.guest, FOUND],
            [self.POST_EDIT, self.another, FOUND],
            [self.POST_EDIT, self.author, OK],
            [POST_CREATE, self.guest, FOUND],
            [POST_CREATE, self.author, OK],
            [FOLLOW, self.guest, FOUND],
            [FOLLOW, self.author, FOUND],
            [FOLLOW, self.another, FOUND],
            [UNFOLLOW, self.guest, FOUND],
            [UNFOLLOW, self.author, NOT_FOUND],
            [UNFOLLOW, self.another, FOUND],
            [FOLLOW_INDEX, self.guest, FOUND],
            [FOLLOW_INDEX, self.another, OK],
        ]
        for url, client, status in cases:
            with self.subTest(url=url, status=status):
                self.assertEqual(
                    client.get(url).status_code, status
                )

    def test_redirect_to_correct_urls(self):
        urls_to_redirect_urls = [
            [self.POST_EDIT, self.guest,
                self.POST_EDIT_TO_LOGIN_REDIRECT],
            [POST_CREATE, self.guest, POST_CREATE_TO_LOGIN_REDIRECT],
            [self.POST_EDIT, self.another, self.POST_DETAIL],
            [FOLLOW, self.guest, FOLLOW_TO_LOGIN_REDIRECT],
            [FOLLOW, self.author, FOLLOW_INDEX],
            [FOLLOW, self.another, FOLLOW_INDEX],
            [UNFOLLOW, self.guest, UNFOLLOW_TO_LOGIN_REDIRECT],
            [UNFOLLOW, self.another, FOLLOW_INDEX],
            [FOLLOW_INDEX, self.guest, FOLLOW_INDEX_TO_LOGIN_REDIRECT],
        ]
        for url, client, redirect_url in urls_to_redirect_urls:
            with self.subTest(url=url, redirect_url=redirect_url):
                self.assertRedirects(
                    client.get(url, follow=True), redirect_url
                )

    def test_urls_uses_correct_templates(self):
        url_templates_names = {
            INDEX: 'posts/index.html',
            GROUP_URL: 'posts/group_list.html',
            PROFILE: 'posts/profile.html',
            self.POST_DETAIL: 'posts/post_detail.html',
            self.POST_EDIT: 'posts/create_post.html',
            POST_CREATE: 'posts/create_post.html',
            FOLLOW_INDEX: 'posts/follow.html'
        }
        for url, template in url_templates_names.items():
            with self.subTest(url=url):
                self.assertTemplateUsed(
                    self.author.get(url), template
                )
