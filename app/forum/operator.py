"""Keep the operator entry point bound to the forum's current identity."""
from django.contrib import admin
from django.shortcuts import redirect
from django.views.decorators.cache import never_cache
from django.views.decorators.debug import sensitive_post_parameters
from django.views.decorators.http import require_http_methods


@never_cache
@sensitive_post_parameters('password')
@require_http_methods(['GET', 'POST'])
def operator_login(request):
    # A valid second password must not silently replace an existing identity.
    # Operators can leave first, then use Django's regular protected login.
    if request.user.is_authenticated or request.session.get('guest_id'):
        return redirect('admin:index' if admin.site.has_permission(request) else 'board')
    return admin.site.login(request)


@require_http_methods(['GET'])
def dashboard(request):
    from pathlib import Path
    from django.conf import settings
    from django.contrib.auth import get_user_model
    from django.core.paginator import Paginator
    from django.db import connection
    from django.db.models import Sum
    from django.http import HttpResponseForbidden
    from django.shortcuts import render
    from .models import Attachment, OperatorEvent, Post, Comment
    if not request.user.is_active or not request.user.is_staff:
        return HttpResponseForbidden('Operator access required.')
    with connection.cursor() as cursor:
        cursor.execute('SELECT 1')
        healthy = cursor.fetchone()[0] == 1
    database = Path(settings.DATABASES['default']['NAME'])
    return render(request, 'forum/maintenance.html', {
        'healthy': healthy,
        'database_bytes': database.stat().st_size if database.is_file() else None,
        'image_bytes': Attachment.objects.aggregate(total=Sum('size'))['total'] or 0,
        'post_count': Post.objects.filter(deleted=False).count(),
        'comment_count': Comment.objects.filter(deleted=False).count(),
        'identities': Paginator(get_user_model().objects.order_by('username'), 30).get_page(request.GET.get('page')),
        'events': OperatorEvent.objects.select_related('actor')[:20],
    })


@require_http_methods(['POST'])
def identity_action(request, pk):
    from django.contrib.auth import get_user_model
    from django.db import transaction
    from django.http import HttpResponseForbidden, HttpResponseBadRequest
    from django.shortcuts import get_object_or_404
    from .models import OperatorEvent
    if not request.user.is_active or not request.user.is_staff:
        return HttpResponseForbidden('Operator access required.')
    action = request.POST.get('action')
    if action not in ('disable', 'restore'):
        return HttpResponseBadRequest('Choose disable or restore.')
    with transaction.atomic():
        target = get_object_or_404(get_user_model().objects.select_for_update(), pk=pk)
        if target.is_staff or target.is_superuser:
            return HttpResponseBadRequest('Manage operator accounts through the local administration tools.')
        desired = action == 'restore'
        if target.is_active != desired:
            target.is_active = desired
            target.save(update_fields=['is_active'])
            OperatorEvent.objects.create(actor=request.user, target_id=target.pk, action=action)
    return redirect('maintenance')
