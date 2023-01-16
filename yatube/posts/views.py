from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import cache_page

from .forms import PostForm, CommentForm
from .models import Group, Post, User, Follow

AMOUNT_POST = 10


def page_context(request, posts):
    """Паджинатор."""
    paginator = Paginator(posts, AMOUNT_POST)
    page_number = request.GET.get('page')
    return paginator.get_page(page_number)


@cache_page(20)
def index(request):
    """Функция для отображения главной страницы проекта."""
    template = 'posts/index.html'
    post_list = Post.objects.select_related("group").all()
    page_obj = page_context(request, post_list)
    context = {
        'page_obj': page_obj,
    }
    return render(request, template, context)


def group_posts(request, slug):
    """Функция для отображения страницы сообщества."""
    template = 'posts/group_list.html'
    group = get_object_or_404(Group, slug=slug)
    groups_posts = group.posts.select_related('author')
    page_obj = page_context(request, groups_posts)
    context = {
        'page_obj': page_obj,
        'posts': groups_posts,
        'group': group,
    }
    return render(request, template, context)


def profile(request, username):
    """Функция для отображения профиля пользователя."""
    template = 'posts/profile.html'
    author = get_object_or_404(User, username=username)
    post_list = author.posts.select_related('group')
    page_obj = page_context(request, post_list)
    if request.user.is_authenticated:
        following = Follow.objects.filter(
            user=request.user, author=author
        ).exists()
    else:
        following = False
    context = {
        'author': author,
        'following': following,
        'page_obj': page_obj,
    }
    return render(request, template, context)


def post_detail(request, post_id):
    """Функция для отображения конкретной записи."""
    template = 'posts/post_detail.html'
    post = get_object_or_404(Post.objects.select_related('group'), id=post_id)
    comments = post.comments.select_related('post')
    context = {
        'post': post,
        'form': CommentForm(),
        'comments': comments,
    }
    return render(request, template, context)


@login_required
def post_create(request):
    """Функция для создания записи."""
    template = 'posts/create_post.html'
    post = Post.objects.select_related('author')
    form = PostForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('post:profile', post.author.username)
    context = {
        'post': post,
        'form': form,
    }

    return render(request, template, context)


@login_required
def post_edit(request, post_id):
    """Функция для редактирования записи."""
    template = 'posts/create_post.html'
    edit_post = get_object_or_404(Post, pk=post_id)
    form = PostForm(request.POST or None,
                    files=request.FILES or None, instance=edit_post
                    )

    if edit_post.author != request.user:
        return redirect('posts:post_detail', post_id=post_id)

    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id=post_id)

    context = {
        'post_id': post_id,
        'form': form,
        'is_edit': True
    }
    return render(request, template, context)


@login_required
def add_comment(request, post_id):
    """Функция для добавления комментария."""
    template = 'posts/post_detail.html'
    form = CommentForm(request.POST or None)
    post = get_object_or_404(Post, pk=post_id)
    comments = post.comments.select_related('post')
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
        return redirect('posts:post_detail', post_id=post_id)
    context = {
        'post': post,
        'comments': comments,
        'form': form,
    }
    return render(request, template, context)


@login_required
def follow_index(request):
    """Подписка на пользователя."""
    template = 'posts/follow.html'
    posts = Post.objects.filter(author__following__user=request.user)
    page_obj = page_context(request, posts)
    context = {
        'page_obj': page_obj,
    }
    return render(request, template, context)


@login_required
def profile_follow(request, username):
    """Функция для подписки на автора."""
    author = get_object_or_404(User, username=username)
    user = request.user
    if author != user:
        Follow.objects.get_or_create(user=request.user, author=author)
    return redirect('posts:profile', username)


@login_required
def profile_unfollow(request, username):
    """Функция для отписки от автора."""
    author = get_object_or_404(User, username=username)
    user = request.user
    follower = Follow.objects.filter(user=user, author=author)
    if follower.exists():
        follower.delete()
    return redirect('posts:profile', username=author)
