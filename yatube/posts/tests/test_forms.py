import shutil
import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model
from http import HTTPStatus

from ..models import Post, Group

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

User = get_user_model()


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='NoName')
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)
        cls.group = Group.objects.create(
            title='Тестовая группа',
            description='Тестовое описание',
            slug='test-slug'
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.author)
        self.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        self.uploaded_image = SimpleUploadedFile(
            name='small.gif',
            content=self.small_gif,
            content_type='image/gif',
        )

    def test_post_create(self):
        form_data = {
            'text': 'Текст из формы.',
            'group': self.group.id,
            'image': self.uploaded_image
        }

        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )

        self.assertRedirects(response,
                             reverse('posts:profile',
                                     kwargs={'username': self.author.username})
                             )

        post = Post.objects.first()
        self.assertEqual(Post.objects.count(), 1)
        self.assertEqual(post.text, form_data['text'])
        self.assertEqual(post.author, self.author)
        self.assertEqual(post.group.id, form_data['group'])
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_edit(self):
        post = Post.objects.create(
            author=self.author,
            group=self.group,
            text='Тестовый пост'
        )

        group_2 = Group.objects.create(
            title='Тестовая группа2',
            description='Тестовое описание2',
            slug='test-slug2'
        )
        form_data = {
            'text': 'Текст из формы2',
            'group': group_2.id,
            'image': self.uploaded_image,
        }

        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': post.id}),
            data=form_data,
            follow=True
        )

        post = Post.objects.last()
        self.assertEqual(post.author, self.author)
        self.assertEqual(post.text, form_data['text'])
        self.assertEqual(post.group.id, form_data['group'])
        self.assertEqual(Post.objects.count(), 1)
        self.assertEqual(len(Post.objects.filter(group=self.group)), 0)
        self.assertTrue(post.image)
        self.assertEqual(response.status_code, HTTPStatus.OK)


class CommentFormTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.test_author = User.objects.create_user(
            username='test-author',
        )
        cls.test_post = Post.objects.create(
            text='Тестовый текст комментируемого поста',
            author=cls.test_author
        )
        cls.url_add_comment = reverse(
            'posts:add_comment',
            kwargs={'post_id': cls.test_post.id}
        )

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='test-user')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_add_comment(self):
        form_data = {
            'text': 'Это тестовый комментарий'
        }
        response = self.authorized_client.post(
            self.url_add_comment,
            data=form_data,
            follow=True,
        )
        comment = self.test_post.comments.last()
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(comment.text, 'Это тестовый комментарий')
