from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import cache_page

from yatube.settings import CACHE_TIMEOUT

from .forms import CommentForm, PostForm
from .models import Follow, Group, Post, User
from .utils import paginate


@cache_page(CACHE_TIMEOUT, key_prefix='index_page')
def index(request):
    """Главная - со списком всех блогозаписей."""
    posts = Post.objects.select_related('author', 'group').all()
    page_obj = paginate(posts, request)
    return render(request, 'posts/index.html', {
        'page_obj': page_obj, 'index': True})


def group_posts(request, slug):
    """Блогозаписи любого сообщества."""
    selected_group = get_object_or_404(Group, slug=slug)
    post_list = selected_group.posts.select_related('author', 'group').all()
    page_obj = paginate(post_list, request)
    return render(request, 'posts/group_list.html', {
        'group': selected_group, 'page_obj': page_obj})


def profile(request, username):
    """Блогозаписи интернет-мыслителя."""
    author = get_object_or_404(User, username=username)
    post_list = author.posts.select_related('author', 'group').all()
    page_obj = paginate(post_list, request)
    following = False
    if request.user.is_authenticated:
        if Follow.objects.filter(user=request.user, author=author).exists():
            following = True
    return render(request, 'posts/profile.html', {
        'author': author, 'page_obj': page_obj, 'following': following})


def post_detail(request, post_id):
    """Страничка блогозаписи."""
    post = get_object_or_404(Post, pk=post_id)
    comments = post.comments.select_related('author').all()
    form = CommentForm(request.POST or None)
    if not form.is_valid():
        return render(request, 'posts/post_detail.html', {
            'post': post, 'form': form, 'comments': comments})
    new_comment = form.save(commit=False)
    new_comment.author = request.user
    new_comment.save()
    return redirect('posts:post_detail', post_id=post.pk)


@login_required
def post_create(request):
    """Создать блогозапись."""
    form = PostForm(request.POST or None, files=request.FILES or None)
    if not form.is_valid():
        return render(request, 'posts/create_post.html', {'form': form, })
    new_post = form.save(commit=False)
    new_post.author = request.user
    new_post.save()
    return redirect('posts:profile', request.user.username)


@login_required
def post_edit(request, post_id):
    """Исправление блогозаписи."""
    post = get_object_or_404(Post, pk=post_id)
    if request.user != post.author:
        return redirect('posts:post_detail', post_id=post.pk)
    form = PostForm(request.POST or None,
                    files=request.FILES or None,
                    instance=post)
    if not form.is_valid():
        return render(request, 'posts/create_post.html', {
            'form': form, 'is_edit': True, 'post_id': post_id})
    form.save()
    return redirect('posts:post_detail', post_id=post.pk)


@login_required
def add_comment(request, post_id):
    """Добавление замечания."""
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = get_object_or_404(Post, id=post_id)
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)
    # если делать guard lock будет дважды одинаковый return. а так лаконичней


@login_required
def follow_index(request):
    """Блогозаписи из подписок."""
    authors = User.objects.filter(following__user=request.user)
    post_list = Post.objects.filter(author__in=authors)
    page_obj = paginate(post_list, request)
    return render(request, 'posts/index.html', {
        'page_obj': page_obj, 'follow': True})


@login_required
def profile_follow(request, username):
    """Добавить подписку."""
    if request.user == User.objects.get(username=username):
        return redirect('posts:profile', username)
    if not Follow.objects.filter(user=request.user, author=User.objects.get(
            username=username)).exists():
        Follow.objects.create(user=request.user, author=User.objects.get(
            username=username))
    return redirect('posts:profile', username)


@login_required
def profile_unfollow(request, username):
    """Убрать подписку."""
    if Follow.objects.filter(user=request.user, author=User.objects.get(
            username=username)).exists():
        get_object_or_404(Follow, user=request.user,
                          author=User.objects.get(username=username)).delete()
    return redirect('posts:profile', username)
