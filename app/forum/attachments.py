"""Raster-only uploads, decoded and re-encoded; no user-provided file paths."""
import io
import warnings

from django.conf import settings
from django.db import transaction
from django.db.models import Sum
from django.http import Http404, HttpResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_GET, require_POST
from PIL import Image, ImageOps, UnidentifiedImageError

from .models import Attachment, Comment, Post

MAX_FILE = 5 * 1024 * 1024
MAX_PIXELS = 16_000_000
MAX_ATTACHMENTS = 3


def normalize_image(upload):
    if upload.size > MAX_FILE:
        raise ValueError('Images must be 5 MiB or smaller.')
    raw = upload.read(MAX_FILE + 1)
    if len(raw) > MAX_FILE:
        raise ValueError('Images must be 5 MiB or smaller.')
    with warnings.catch_warnings():
        warnings.simplefilter('error', Image.DecompressionBombWarning)
        with Image.open(io.BytesIO(raw)) as image:
            if image.format not in ('JPEG', 'PNG', 'WEBP'):
                raise ValueError('Use a PNG, JPEG or WebP image.')
            if image.width * image.height > MAX_PIXELS or getattr(image, 'n_frames', 1) != 1:
                raise ValueError('Use a still image with at most 16 million pixels.')
            image.load()
            output = io.BytesIO()
            normalized = ImageOps.exif_transpose(image).convert('RGBA' if 'A' in image.getbands() else 'RGB')
            # Construct fresh pixels so source metadata and trailing bytes cannot survive.
            clean = Image.new(normalized.mode, normalized.size)
            clean.paste(normalized)
            clean.save(output, format='PNG')
    data = output.getvalue()
    if len(data) > MAX_FILE:
        raise ValueError('The decoded image is too large. Try a smaller image.')
    return data


@require_POST
def attach(request, pk, kind='post'):
    from .views import owner_filter
    model = Comment if kind == 'comment' else Post
    filters = {'pk': pk, 'deleted': False, **owner_filter(request, model)}
    get_object_or_404(model, **filters)
    upload = request.FILES.get('file')
    if upload is None or len(request.FILES) != 1 or len(request.FILES.getlist('file')) != 1:
        return HttpResponseBadRequest('Choose one image at a time.')
    try:
        data = normalize_image(upload)
    except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError, Image.DecompressionBombWarning):
        return HttpResponseBadRequest('Use a still PNG, JPEG or WebP image up to 5 MiB and 16 million pixels.')
    with transaction.atomic():
        obj = get_object_or_404(model.objects.select_for_update(), **filters)
        if obj.attachments.count() >= MAX_ATTACHMENTS:
            return HttpResponseBadRequest('At most three images per post or comment.')
        used = Attachment.objects.aggregate(total=Sum('size'))['total'] or 0
        if used + len(data) > getattr(settings, 'WE_SPEAK_ATTACHMENT_QUOTA', 512 * 1024 * 1024):
            return HttpResponse('Attachment storage is full.', status=507)
        Attachment.objects.create(**{kind: obj}, data=data, size=len(data), content_type='image/png')
    return redirect('thread', pk=obj.thread_id if model is Comment else obj.pk)


@require_GET
def download(request, pk):
    item = get_object_or_404(Attachment.objects.select_related('post', 'comment'), pk=pk)
    target = item.post if item.post_id else item.comment
    if target.deleted:
        raise Http404
    response = HttpResponse(bytes(item.data), content_type='image/png')
    response['X-Content-Type-Options'] = 'nosniff'
    response['Content-Disposition'] = 'inline; filename="image.png"'
    response['Cache-Control'] = 'no-store'
    response['Content-Security-Policy'] = "default-src 'none'; sandbox"
    return response
