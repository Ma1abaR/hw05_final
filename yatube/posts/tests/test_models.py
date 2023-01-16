from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Group, Post

User = get_user_model()

LENGTH_TEXT = 15


class PostModelTest(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )

        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост 1',
        )

    def test_post_model_have_correct_object_names(self):
        post = PostModelTest.post
        expected_name = post.text[:LENGTH_TEXT]
        self.assertEqual(expected_name, str(post))

    def test_group_model_have_correct_object_names(self):
        group = self.group
        expected_name = group.title
        self.assertEqual(expected_name, str(group))
