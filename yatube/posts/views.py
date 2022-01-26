from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http.response import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from .forms import CommentForm, PostForm
from .models import Follow, Group, Post, User
from .settings import POSTS_PER_PAGE


def paginator_page(request, post_list) -> object:
    return Paginator(
        post_list, POSTS_PER_PAGE).get_page(request.GET.get('page'))


def index(request) -> HttpResponse:
    return render(request, 'posts/index.html', {
        'page_obj': paginator_page(request, Post.objects.all())
    })


def group_posts(request, slug) -> HttpResponse:
    group = get_object_or_404(Group, slug=slug)
    return render(request, 'posts/group_list.html', {
        'group': group,
        'page_obj': paginator_page(request, group.posts.all())
    })


def profile(request, username) -> HttpResponse:
    author = get_object_or_404(User, username=username)
    following = request.user.is_authenticated and request.user != author and (
        Follow.objects.filter(user=request.user, author=author))
    return render(request, 'posts/profile.html', {
        'author': author,
        'following': following,
        'page_obj': paginator_page(request, author.posts.all())
    })


def post_detail(request, post_id) -> HttpResponse:
    return render(request, 'posts/post_detail.html', {
        'post': get_object_or_404(Post, pk=post_id),
        'form': CommentForm(),
    })


@login_required
def post_create(request) -> HttpResponse:
    form = PostForm(request.POST or None, request.FILES or None)
    if not form.is_valid():
        return render(request, 'posts/create_post.html', {'form': form})
    new_post = form.save(commit=False)
    new_post.author = request.user
    new_post.save()
    return redirect('posts:profile', username=new_post.author.username)


@login_required
def post_edit(request, post_id) -> HttpResponse:
    post = get_object_or_404(Post, pk=post_id)
    if request.user != post.author:
        return redirect('posts:post_detail', post_id=post_id)
    form = PostForm(
        request.POST or None, request.FILES or None, instance=post
    )
    if not form.is_valid():
        return render(request, 'posts/create_post.html', {
            'form': form, 'is_edit': True
        })
    form.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def add_comment(request, post_id) -> HttpResponse:
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request) -> HttpResponse:
    return render(request, 'posts/follow.html', {'page_obj': paginator_page(
        request, Post.objects.filter(author__following__user=request.user)
    )})


@login_required
def profile_follow(request, username) -> HttpResponse:
    author = get_object_or_404(User, username=username)
    if author != request.user:
        Follow.objects.get_or_create(user=request.user, author=author)
    return redirect('posts:follow_index')


@login_required
def profile_unfollow(request, username) -> HttpResponse:
    get_object_or_404(
        Follow, user=request.user, author__username=username
    ).delete()
    return redirect('posts:follow_index')
