from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.core.cache import cache
from django.urls import reverse

from ..models import Group, Post

User = get_user_model()


class PostURLTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='HasNoName')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            description='Тестовое описание',
            slug='test-slug'
        )

        cls.post = Post.objects.create(
            author=cls.user,
            group=cls.group,
            text='Тестовый пост'
        )

        cls.url_index = '/'
        cls.url_group_list = f'/group/{cls.group.slug}/'
        cls.url_post_detail = f'/posts/{cls.post.pk}/'
        cls.url_profile = f'/profile/{cls.user.username}/'
        cls.url_post_create = '/create/'
        cls.url_post_edit = f'/posts/{cls.post.pk}/edit/'
        cls.url_redirect_to_login = '/auth/login/?next=/create/'
        cls.url_unexisting_page = '/unexisting_page/'

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.another_user = User.objects.create_user(username='TestUser')
        self.another_user_client = Client()
        self.another_user_client.force_login(self.another_user)

    def test_urls_uses_correct_template(self):
        """Проверяем запрашиваемые шаблоны страниц через имена."""
        cache.clear()
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse(
                'posts:group_list',
                kwargs={'slug': self.group.slug}
            ): 'posts/group_list.html',
            reverse(
                'posts:profile',
                kwargs={'username': self.user.username}
            ): 'posts/profile.html',
            reverse(
                'posts:post_detail',
                kwargs={'post_id': self.post.id}
            ): 'posts/post_detail.html',
            reverse(
                'posts:post_edit',
                kwargs={'post_id': self.post.id}
            ): 'posts/create_post.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse('posts:follow_index'): 'posts/follow.html'
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_urls_uses_correct_unexisting_page(self):
        response = self.guest_client.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_create_url_redirect_anonymous_on_admin_login(self):
        response = self.guest_client.get(self.url_post_create, follow=True)
        self.assertRedirects(
            response, self.url_redirect_to_login
        )

    def test_post_edit_url_redirect_not_author_on_post_detail(self):
        response = self.another_user_client.get(
            self.url_post_edit, follow=True)
        self.assertRedirects(
            response, self.url_post_detail
        )

    def test_home_url_exists_at_desired_location(self):
        response = self.guest_client.get(self.url_index)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_group_list_exists_at_desired_location(self):
        response = self.guest_client.get(self.url_group_list)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_profile_exists_at_desired_location(self):
        response = self.guest_client.get(self.url_profile)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_detail_exists_at_desired_location(self):
        response = self.guest_client.get(self.url_post_detail)
        self.assertEqual(response.status_code, HTTPStatus.OK)
