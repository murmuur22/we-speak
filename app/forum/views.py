import secrets

from django import forms
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponseForbidden, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods, require_POST
from django.views.decorators.debug import sensitive_post_parameters

from .forms import JoinForm
from .models import Post, Comment, Reaction, EMOJIS
from django.db import transaction
from django.db.models import Count
from django.http import HttpResponseBadRequest


def actor_key(request):
    if request.user.is_authenticated:
        return f'u:{request.user.pk}'
    if request.session.get('guest_id'):
        return 'g:' + request.session['guest_id']
    return ''


def reaction_rows(request, obj):
    counts = {row['emoji']: row['total'] for row in obj.reactions.values('emoji').annotate(total=Count('pk'))}
    selected = set(obj.reactions.filter(actor=actor_key(request)).values_list('emoji', flat=True))
    return [{'emoji': emoji, 'count': counts.get(emoji, 0), 'selected': emoji in selected} for emoji in EMOJIS]


@require_POST
def react(request, pk, kind='post'):
    if not entered(request):
        return HttpResponseForbidden('Enter a session before reacting.')
    emoji = request.POST.get('emoji', '')
    if emoji not in EMOJIS:
        return HttpResponseBadRequest('Choose an available emoji.')
    model = Comment if kind == 'comment' else Post
    with transaction.atomic():
        obj = get_object_or_404(model.objects.select_for_update(), pk=pk, deleted=False)
        item, created = Reaction.objects.get_or_create(**{kind: obj}, actor=actor_key(request), emoji=emoji)
        if not created:
            item.delete()
    return redirect('thread', pk=obj.thread_id if model is Comment else obj.pk)



class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['body']
        widgets = {'body': forms.Textarea(attrs={'rows': 4})}
        labels = {'body': 'Your reply'}


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['title', 'body']
        widgets = {'body': forms.Textarea(attrs={'rows': 7})}
        labels = {'body': 'Post'}


def entered(request):
    return request.user.is_authenticated or bool(request.session.get('guest_id'))


def owner_filter(request, model):
    if request.user.is_authenticated:
        return {'author_id': request.user.pk}
    if model is Comment and request.session.get('guest_id'):
        return {'author__isnull': True, 'guest_id': request.session['guest_id']}
    raise Http404


def owns(request, obj):
    if obj.deleted:
        return False
    if request.user.is_authenticated:
        return obj.author_id == request.user.pk
    return isinstance(obj, Comment) and bool(request.session.get('guest_id')) and obj.guest_id == request.session['guest_id']


@require_POST
def guest(request):
    if not entered(request):
        request.session.cycle_key()
        request.session['guest_id'] = secrets.token_hex(32)
    return redirect('board')


@require_POST
def leave(request):
    logout(request)
    return redirect('login')


@sensitive_post_parameters('password1', 'password2')
@require_http_methods(['GET', 'POST'])
def join(request):
    if entered(request):
        return redirect('board')
    form = JoinForm(request.POST if request.method == 'POST' else None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        login(request, user)
        return redirect('board')
    return render(request, 'forum/account.html', {'form': form, 'joining': True})


@sensitive_post_parameters('password')
@require_http_methods(['GET', 'POST'])
def sign_in(request):
    if entered(request):
        return redirect('board')
    data = request.POST.copy() if request.method == 'POST' else None
    if data is not None:
        data['username'] = data.get('username', '').lower()
    form = AuthenticationForm(request, data=data)
    if request.method == 'POST' and form.is_valid():
        login(request, form.get_user())
        return redirect('board')
    return render(request, 'forum/account.html', {'form': form})


@login_required
@require_http_methods(['GET'])
def history(request):
    posts = Post.objects.filter(author=request.user, deleted=False)
    replies = Comment.objects.filter(author=request.user, deleted=False).order_by('-created_at', '-pk')
    return render(request, 'forum/history.html', {
        'posts': Paginator(posts, 30).get_page(request.GET.get('posts')),
        'comments': Paginator(replies, 30).get_page(request.GET.get('comments')),
    })


@require_http_methods(['GET'])
def health(request):
    from django.db import connection
    from django.http import JsonResponse
    with connection.cursor() as cursor:
        cursor.execute('SELECT 1')
        cursor.fetchone()
    return JsonResponse({'status': 'ok'})


@require_http_methods(['GET'])
def board(request):
    posts = Post.objects.select_related('author').filter(deleted=False)
    query = request.GET.get('q', '')[:200]
    if query:
        posts = posts.filter(Q(title__icontains=query) | Q(body__icontains=query))
    return render(request, 'forum/board.html', {'page': Paginator(posts, 30).get_page(request.GET.get('page')), 'query': query})


@require_http_methods(['GET', 'POST'])
def new_post(request):
    if not request.user.is_authenticated:
        return HttpResponseForbidden('Sign in to start a discussion.')
    form = PostForm(request.POST if request.method == 'POST' else None)
    if request.method == 'POST' and form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('thread', pk=post.pk)
    return render(request, 'forum/form.html', {'form': form, 'heading': 'New discussion'})


@require_http_methods(['GET'])
def thread(request, pk):
    post = get_object_or_404(Post.objects.select_related('author'), pk=pk)
    page = Paginator(post.comments.select_related('author'), 30).get_page(request.GET.get('page'))
    for reply in page:
        reply.owned = owns(request, reply)
        reply.reaction_rows = reaction_rows(request, reply)
        reply.image_rows = reply.attachments.defer('data').all()
    post.reaction_rows = reaction_rows(request, post)
    post.image_rows = post.attachments.defer('data').all()
    return render(request, 'forum/thread.html', {'post': post, 'comments': page,
        'reply_form': CommentForm(), 'can_comment': entered(request), 'owned': owns(request, post)})


@require_POST
def comment(request, pk):
    post = get_object_or_404(Post, pk=pk)
    if not entered(request):
        return HttpResponseForbidden('Enter a session before commenting.')
    form = CommentForm(request.POST)
    if form.is_valid():
        reply = form.save(commit=False)
        reply.thread = post
        if request.user.is_authenticated:
            reply.author = request.user
        else:
            reply.guest_id = request.session['guest_id']
        reply.save()
        return redirect('thread', pk=pk)
    return render(request, 'forum/form.html', {'form': form, 'heading': 'Reply', 'submit_label': 'Post reply'}, status=400)


@require_http_methods(['GET', 'POST'])
def edit(request, pk, kind='post'):
    model = Comment if kind == 'comment' else Post
    filters = {'pk': pk, 'deleted': False, **owner_filter(request, model)}
    obj = get_object_or_404(model, **filters)
    form_type = CommentForm if model is Comment else PostForm
    form = form_type(request.POST if request.method == 'POST' else None, instance=obj)
    thread_id = obj.thread_id if model is Comment else obj.pk
    if request.method == 'POST' and form.is_valid():
        model.objects.filter(**filters).update(**form.cleaned_data, edited_at=timezone.now())
        return redirect('thread', pk=thread_id)
    return render(request, 'forum/form.html', {'form': form, 'heading': 'Edit comment' if model is Comment else 'Edit post', 'submit_label': 'Save changes'})


@require_http_methods(['GET', 'POST'])
def delete_post(request, pk, kind='post'):
    model = Comment if kind == 'comment' else Post
    filters = {'pk': pk, 'deleted': False, **owner_filter(request, model)}
    obj = get_object_or_404(model, **filters)
    thread_id = obj.thread_id if model is Comment else obj.pk
    if request.method == 'POST':
        changes = {'body': '', 'author': None, 'deleted': True, 'edited_at': None}
        changes.update({'guest_id': ''} if model is Comment else {'title': ''})
        with transaction.atomic():
            model.objects.filter(**filters).update(**changes)
            obj.attachments.all().delete()
            obj.reactions.all().delete()
        return redirect('thread', pk=thread_id)
    return render(request, 'forum/delete.html', {'post': obj.thread if model is Comment else obj})
