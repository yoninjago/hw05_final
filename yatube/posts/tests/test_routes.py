from django.test import TestCase
from django.urls import reverse

from posts.urls import app_name

USERNAME = 'test-user'
SLUG = 'test-slug'
POST_ID = 1


class PostsRoutesTests(TestCase):
    def test_url_uses_correct_routes(self):
        """Проверка результата расчета urls"""
        urls_names = [
            ['/', 'index', []],
            [f'/group/{SLUG}/', 'group_list', [SLUG]],
            [f'/profile/{USERNAME}/', 'profile', [USERNAME]],
            [f'/profile/{USERNAME}/follow/', 'profile_follow', [USERNAME]],
            [f'/profile/{USERNAME}/unfollow/', 'profile_unfollow', [USERNAME]],
            [f'/posts/{POST_ID}/', 'post_detail', [POST_ID]],
            [f'/posts/{POST_ID}/edit/', 'post_edit', [POST_ID]],
            [f'/posts/{POST_ID}/comment/', 'add_comment', [POST_ID]],
            ['/create/', 'post_create', []],
            ['/follow/', 'follow_index', []],
        ]
        for url, route, args in urls_names:
            with self.subTest(route=route, url=url):
                self.assertEqual(
                    reverse(f'{app_name}:{route}', args=args), url
                )
