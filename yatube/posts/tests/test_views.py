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
        cls.first_user = User.objects.create_user(username='test-username')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.first_user)
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.group_2 = Group.objects.create(
            title='Тестовая группа2',
            slug='test-slug2',
            description='Тестовое описание2',
        )
        cls.group_3 = Group.objects.create(
            title='Тестовая группа3',
            slug='test-slug3',
            description='Тестовое описание3',
        )
        cls.post = Post.objects.create(
            author=cls.first_user,
            group=cls.group,
            text='Тестовый пост'
        )
        cls.comment = Comment.objects.create(
            author=cls.first_user,
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
            'posts:profile', kwargs={'username': cls.first_user.username}
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
        authorized_client = TestsViewsPosts.authorized_client
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
        posts_group = Post.objects.filter(group=TestsViewsPosts.group.id).count()
        posts_group_2 = Post.objects.filter(group=TestsViewsPosts.group_2.id).count()
        posts_group_3 = Post.objects.filter(group=TestsViewsPosts.group_3.id).count()
        self.assertEqual(posts_group, POST_ON_PAGE + 1)
        self.assertEqual(posts_group_2, 0)
        self.assertEqual(posts_group_3, 0)
        response = self.authorized_client.get(self.url_group_list)
        self.assertIn('page_obj', response.context)
        self.assertIn('post', response.context)
        self.assertIn('group', response.context)

    def test_profile_show_correct_context(self):
        """Шаблон profile.html сформирован с правильным контекстом."""
        response = self.authorized_client.get(self.url_profile)
        self.assertIn('author', response.context)
        self.assertIn('following', response.context)
        self.assertIn('page_obj', response.context)

    def test_post_detail_show_correct_context(self):
        """Шаблон post_detail.html сформирован с правильным контекстом."""
        response = self.authorized_client.get(self.url_post_detail)
        self.assertEqual('post', self.post.id)
        self.assertIn('form', response.context)
        self.assertIn('comments', response.context)

    def test_post_create_show_correct_context(self):
        """Шаблон post_create.html сформирован с правильным контекстом."""
        response = self.authorized_client.get(self.url_post_create)
        self.assertIn('form', response.context)

    def test_post_edit_show_correct_context(self):
        """Шаблон post_edit.html сформирован с правильным контекстом."""
        authorized_client = TestsViewsPosts.authorized_client
        response = authorized_client.get(self.url_post_edit)
        self.assertIn('post_id', response.context)
        self.assertIn('form', response.context)
        self.assertIn('is_edit', response.context)

    def test_add_comment_show_correct_context(self):
        response = self.authorized_client.get(self.url_add_comment)
        self.assertIn('post', response.context)
        self.assertIn('comments', response.context)
        self.assertIn('form', response.context)

    def test_created_posts_shows_on_different_pages(self):
        pages = (self.url_index, self.url_group_list, self.url_profile)
        for item in pages:
            with self.subTest(item=item):
                cache.clear()
                response = self.authorized_client.get(item)
                post = response.context['page_obj'][0]
                self.assertEqual(post.text, self.post.text)
                self.assertEqual(post.author.username,
                                 self.first_user.username)
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
        pages = [self.url_index, self.url_group_list, self.url_profile]
        for item in pages:
            with self.subTest(item=item):
                cache.clear()
                response = self.authorized_client.get(item)
                self.assertEqual(len(response.context['page_obj']), 10)

    def test_second_page_contains_ten_records(self):
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
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.follower = User.objects.create_user(username='follower')
        cls.following = User.objects.create_user(username='following')
        cls.test_post = Post.objects.create(
            author=cls.following,
            text='Тестовый текст'
        )

    def setUp(self):
        self.authorized_follower = Client()
        self.authorized_following = Client()
        self.authorized_follower.force_login(self.follower)
        self.authorized_following.force_login(self.following)

    def test_follow(self):
        self.authorized_follower.get(reverse(
            'posts:profile_follow',
            kwargs={'username': self.following.username},
        ))
        self.assertEqual(Follow.objects.all().count(), 1)

    def test_unfollow(self):
        self.authorized_follower.get(reverse(
            'posts:profile_follow',
            kwargs={'username': self.following.username},
        ))
        self.authorized_follower.get(reverse(
            'posts:profile_unfollow',
            kwargs={'username': self.following.username},
        ))
        self.assertEqual(Follow.objects.all().count(), 0)

    def test_subscription_feed(self):
        Follow.objects.create(user=self.follower,
                              author=self.following)
        response = self.authorized_follower.get(reverse(
            'posts:profile_follow',
            kwargs={'username': self.following.username},
        ))
        post_text_0 = response.context["page_obj"][0].text
        self.assertEqual(post_text_0, 'Тестовый текст')
