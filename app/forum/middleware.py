"""Small persistent, fixed-window limits; never trust client proxy headers."""
import time

from django.conf import settings
from django.db import transaction
from django.db.models import F
from django.http import HttpResponse
from django.utils.crypto import salted_hmac

from .models import RateBucket
from django.utils.cache import add_never_cache_headers


class PrivacyHeadersMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        add_never_cache_headers(response)
        response['Referrer-Policy'] = 'same-origin'
        return response


class WriteLimitMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.method == 'POST':
            try:
                if int(request.META.get('CONTENT_LENGTH') or 0) > 6 * 1024 * 1024:
                    return HttpResponse('Request is too large.', status=413)
            except ValueError:
                return HttpResponse('Invalid request size.', status=400)
            path = request.path
            if path in ('/login/', '/admin/login/'):
                scope, seconds, limit = 'login', 60, getattr(settings, 'WE_SPEAK_AUTH_LIMIT', 12)
            elif path == '/join/':
                scope, seconds, limit = 'join', 3600, 5
            else:
                scope, seconds, limit = 'write', 60, 60
            now = int(time.time())
            bucket = now // seconds
            address = request.META.get('REMOTE_ADDR', 'unknown')
            key = salted_hmac('forum-rate', f'{scope}:{address}:{bucket}', algorithm='sha256').hexdigest()
            with transaction.atomic():
                RateBucket.objects.filter(expires__lte=now).delete()
                record, _ = RateBucket.objects.get_or_create(key=key, defaults={'expires': (bucket + 1) * seconds})
                RateBucket.objects.filter(key=key).update(count=F('count') + 1)
                record.refresh_from_db()
            if record.count > limit:
                response = HttpResponse('Please wait before trying again.', status=429)
                response['Retry-After'] = str((bucket + 1) * seconds - now)
                return response
        return self.get_response(request)
