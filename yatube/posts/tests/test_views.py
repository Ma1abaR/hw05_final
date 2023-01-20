from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django.core.cache import cache

from ..models import Post, Group, Follow, Comment

POST_ON_PAGE = 0
AMOUNT_POST = 13
User = get_user_model()


class TestsViewsPosts(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='test-username')
        cls.author_authorized = Client()
        cls.author_authorized.force_login(cls.author)
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.author,
            group=cls.group,
            text='Тестовый пост'
        )
        cls.comment = Comment.objects.create(
            author=cls.author,
            text='Тестовый комментарий',
            post=cls.post
        )
        cls.url_index = reverse('posts:index')
        cls.url_group_list = reverse(
            'posts:group_list',
            kwargs={'slug': 'test-slug'}
        )
        cls.url_post_detail = reverse(
            'posts:post_detail',
            kwargs={'post_id': cls.post.id}
        )
        cls.url_profile = reverse(
            'posts:profile', kwargs={'username': cls.author.username}
        )
        cls.url_post_create = reverse('posts:post_create')
        cls.url_post_edit = reverse(
            'posts:post_edit', kwargs={'post_id': cls.post.pk}
        )
        cls.url_add_comment = reverse(
            'posts:add_comment',
            kwargs={'post_id': cls.post.id}
        )

    def setUp(self):
        self.guest_client = Client()

        self.user = User.objects.create_user(username='test-user')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_pages_use_correct_templates(self):
        """URL-адрес использует соответствующий шаблон."""
        authorized_client = TestsViewsPosts.author_authorized
        templates_pages_names = {
            self.url_index: 'posts/index.html',
            self.url_group_list: 'posts/group_list.html',
            self.url_profile: 'posts/profile.html',
            self.url_post_detail: 'posts/post_detail.html',
            self.url_post_create: 'posts/create_post.html',
            self.url_post_edit: 'posts/create_post.html',
            self.url_add_comment: 'posts/post_detail.html',
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                cache.clear()
                response = authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_show_correct_context(self):
        """Шаблон index.html сформирован с правильным контекстом."""
        cache.clear()
        response = self.authorized_client.get(self.url_index)
        self.assertIn('page_obj', response.context)

    def test_group_posts_show_correct_context(self):
        """Шаблон group_list.html сформирован с правильным контекстом и пост в нужной группе"""
        group1 = Group.objects.create(title='group1', slug='slug1')
        group2 = Group.objects.create(title='group2', slug='slug2')

        post1 = Post.objects.create(group=group1, text='test-text', author=self.user)
        Post.objects.create(group=group2, text='test-text', author=self.user)
        Post.objects.create(text='test-text', author=self.user)

        url = reverse('posts:group_list', kwargs={'slug': group1.slug})
        response = self.authorized_client.get(url)

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(response.context['group'], group1)
        self.assertEqual(len(response.context['page_obj']), 1)
        self.assertEqual(response.context['page_obj'][0], post1)

    def test_profile_show_correct_context(self):
        """Шаблон profile.html сформирован с правильным контекстом."""

        profile1 = User.objects.create_user(username='user1')
        profile2 = User.objects.create_user(username='user2')

        post1 = Post.objects.create(text='test-text', author=profile1)
        Post.objects.create(text='test-text', author=profile2)

        url = reverse('posts:profile', kwargs={'username': profile1.username})

        response = self.authorized_client.get(url)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(response.context['author'], profile1)
        self.assertEqual(len(response.context['page_obj']), 1)
        self.assertEqual(response.context['page_obj'][0], post1)

    def test_post_detail_show_correct_context(self):
        """Шаблон post_detail.html сформирован с правильным контекстом."""
        response = self.authorized_client.get(self.url_post_detail)
        self.assertIn('form', response.context)
        self.assertIn('comments', response.context)

    def test_post_create_show_correct_context(self):
        """Шаблон post_create.html сформирован с правильным контекстом."""
        response = self.authorized_client.get(self.url_post_create)
        self.assertIn('form', response.context)

    def test_post_edit_show_correct_context(self):
        """Шаблон post_edit.html сформирован с правильным контекстом."""
        authorized_client = TestsViewsPosts.author_authorized
        response = authorized_client.get(self.url_post_edit)
        self.assertIn('post_id', response.context)
        self.assertIn('form', response.context)
        self.assertIn('is_edit', response.context)

    def test_add_comment_show_correct_context(self):
        response = self.author_authorized.get(self.url_add_comment)
        self.assertIn('post', response.context)
        self.assertIn('comments', response.context)
        self.assertIn('form', response.context)

    def test_created_posts_shows_on_different_pages(self):
        """Проверяем, что новый пост на нужной странице"""
        pages = (self.url_index, self.url_group_list, self.url_profile)
        for item in pages:
            with self.subTest(item=item):
                cache.clear()
                response = self.author_authorized.get(item)
                post = response.context['page_obj'][0]
                self.assertEqual(post.text, self.post.text)
                self.assertEqual(post.author.username,
                                 self.author.username)
                self.assertEqual(post.pub_date, self.post.pub_date)
                self.assertEqual(post.author, self.post.author)
                self.assertEqual(post.group, self.post.group)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test-username')
        cls.group = Group.objects.create(
            title='test-group2',
            slug='test-slug2',
            description='Тестовое описание',
        )
        cls.url_index = reverse('posts:index')
        cls.url_group_list = reverse(
            'posts:group_list',
            kwargs={'slug': cls.group.slug}
        )
        cls.url_profile = reverse(
            'posts:profile', kwargs={'username': cls.user.username}
        )
        fixtures = [Post(
            text=f'Тестовый текст {i}',
            author=cls.user,
            group=cls.group)
            for i in range(13)]
        Post.objects.bulk_create(fixtures)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_firsts_page_contains_ten_records(self):
        """Первая страница содержит 10 постов"""
        pages = [self.url_index, self.url_group_list, self.url_profile]
        for item in pages:
            with self.subTest(item=item):
                cache.clear()
                response = self.authorized_client.get(item)
                self.assertEqual(len(response.context['page_obj']), 10)

    def test_second_page_contains_ten_records(self):
        """Вторая страница содержит 10 постов"""
        pages = [self.url_index, self.url_group_list, self.url_profile]
        for item in pages:
            with self.subTest(item=item):
                cache.clear()
                response = self.authorized_client.get(item + '?page=2')
                self.assertEqual(len(response.context['page_obj']), 3)


class IndexCacheTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.test_user = User.objects.create_user(username='test-user')
        cls.test_post = Post.objects.create(
            author=cls.test_user,
            text='Какой-то текст поста')
        cls.url_index = reverse('posts:index')

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='test-user-auth')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_cache_index_page(self):
        """Проверяем кеш главной страницы"""
        first_step = self.authorized_client.get(self.url_index)
        post = Post.objects.get(id=self.test_post.id)
        post.text = 'Изменённый текст поста'
        post.save()
        second_step = self.authorized_client.get(self.url_index)
        self.assertEqual(first_step.content, second_step.content)
        cache.clear()
        third_step = self.authorized_client.get(self.url_index)
        self.assertNotEqual(first_step.content, third_step.content)


class FollowTests(TestCase):

    def setUp(self) -> None:

        self.authorized_client = Client()
        self.user = User.objects.create_user(username='art1')
        self.authorized_client.force_login(self.user)

        self.author_client = Client()
        self.author_user = User.objects.create_user(username='art2')
        self.author_client.force_login(self.author_user)

        self.guest_client = Client()
        self.guest_user = User.objects.create_user(username='art3')
        self.guest_client.force_login(self.guest_user)

        self.group = Group.objects.create(
            title='Заголовок',
            slug='slug',
        )

        self.post = Post.objects.create(
            text='Текст',
            author=self.author_user,
            group=self.group
        )

    def test_follow_unfollow(self):
        """Тестирование подписки и отписки."""
        count = Follow.objects.filter(author=self.author_user,
                                      user=self.user).count()
        self.assertEqual(count, 0)
        self.authorized_client.get(reverse('posts:profile_follow', kwargs={
            'username': self.author_user.username}))
        count = Follow.objects.filter(author=self.author_user,
                                      user=self.user).count()
        self.assertEqual(count, 1)
        self.authorized_client.get(reverse('posts:profile_unfollow', kwargs={
            'username': self.author_user.username}))
        count = Follow.objects.filter(author=self.author_user,
                                      user=self.user).count()
        self.assertEqual(count, 0)

    """Новая запись пользователя появляется в ленте тех, кто на него подписан
    и не появляется в ленте тех, кто не подписан на него"""
    def test_view_new_follow_post(self):
        self.authorized_client.get(reverse('posts:profile_follow', kwargs={
            'username': self.author_user.username}))
        response = self.authorized_client.get(reverse('posts:follow_index'))
        # Решил попробовать NotContains
        self.assertContains(response, self.post.text, status_code=200)
        response = self.guest_client.get(reverse('posts:follow_index'))
        self.assertNotContains(response, self.post.text, status_code=200)

