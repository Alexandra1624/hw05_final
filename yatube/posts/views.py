from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404, redirect
from .models import Post, Group, Follow
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from posts.forms import PostForm, CommentForm
from django.views.decorators.cache import cache_page

NUMBER_POSTS = 10
CACHE_SECOND = 20


@cache_page(CACHE_SECOND)
def index(request):
    title = 'Последние обновления на сайте'
    post_list = Post.objects.select_related('group').all()
    paginator = Paginator(post_list, NUMBER_POSTS)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'page_obj': page_obj,
        'title': title,
    }

    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts.all()
    paginator = Paginator(post_list, NUMBER_POSTS)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'group': group,
        'page_obj': page_obj,
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    title = username + ' профайл пользователя'
    author = get_object_or_404(User, username=username)
    posts = author.posts.all()
    paginator = Paginator(posts, NUMBER_POSTS)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    post_number = posts.count()
    following = request.user.is_authenticated and Follow.objects.filter(
        user=request.user, author=author).exists()
    context = {
        'post_number': post_number,
        'page_obj': page_obj,
        'author': author,
        'title': title,
        'following': following,
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    form = CommentForm(request.POST or None)
    post = get_object_or_404(Post, id=post_id)
    get_user_object = User.objects.get(id=post.author_id)
    user = get_user_object.username
    post_list = Post.objects.filter(author=get_user_object)
    posts_count = post_list.count()
    comments = post.comments.all()
    context = {
        'username': user,
        'post': post,
        'posts_count': posts_count,
        'form': form,
        'post_view': True,
        'comment': comments,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    template_name = 'posts/create_post.html'
    form = PostForm(
        request.POST or None,
        files=request.FILES or None
    )
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        username = post.author.username
        return redirect('posts:profile', username)
    return render(request, template_name, {'form': form})


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    if post.author != request.user:
        return redirect('posts:post_detail', post_id=post_id)

    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id=post_id)
    context = {
        'post': post,
        'form': form,
        'is_edit': True,
    }
    return render(request, 'posts/create_post.html', context)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    # информация о текущем пользователе доступна в переменной request.user
    follow_posts = Post.objects.filter(author__following__user=request.user)
    paginator = Paginator(follow_posts, NUMBER_POSTS)
    page_number = request.GET.get('page_obj')
    page_obj = paginator.get_page(page_number)
    context = {
        'paginator': paginator,
        'page_obj': page_obj,
    }
    return render(request, "posts/follow.html", context)


@login_required
def profile_follow(request, username):
    # Подписаться на автора
    author = get_object_or_404(User, username=username)
    user = request.user
    if (
        author != request.user and not
        Follow.objects.filter(author=author, user=user).exists()
    ):
        Follow.objects.create(user=user, author=author)
    return redirect('posts:profile', username)


@login_required
def profile_unfollow(request, username):
    # Дизлайк, отписка
    author = get_object_or_404(User, username=username)
    Follow.objects.filter(user=request.user, author=author).delete()
    return redirect('posts:profile', username=author.username)
