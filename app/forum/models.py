import uuid
from django.conf import settings
from django.db import models


class Post(models.Model):
    author = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    title = models.CharField(max_length=140)
    body = models.TextField(max_length=6000)
    deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    edited_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at', '-pk']


class Comment(models.Model):
    thread = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    guest_id = models.CharField(max_length=64, blank=True)
    body = models.TextField(max_length=4000)
    deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    edited_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['created_at', 'pk']


EMOJIS = ('👍', '❤️', '😂', '🎉', '👀', '🌱', '🤔', '🙇')


class OperatorEvent(models.Model):
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    target_id = models.PositiveBigIntegerField()
    action = models.CharField(max_length=16, choices=[('disable', 'Disable'), ('restore', 'Restore')])
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at', '-pk']


class RateBucket(models.Model):
    key = models.CharField(max_length=64, primary_key=True)
    count = models.PositiveIntegerField(default=0)
    expires = models.PositiveBigIntegerField(db_index=True)


class Attachment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    post = models.ForeignKey(Post, null=True, blank=True, on_delete=models.CASCADE, related_name='attachments')
    comment = models.ForeignKey(Comment, null=True, blank=True, on_delete=models.CASCADE, related_name='attachments')
    data = models.BinaryField()
    size = models.PositiveIntegerField()
    content_type = models.CharField(max_length=32)

    class Meta:
        constraints = [models.CheckConstraint(
            condition=(models.Q(post__isnull=False, comment__isnull=True) | models.Q(post__isnull=True, comment__isnull=False)),
            name='attachment_one_target',
        )]


class Reaction(models.Model):
    post = models.ForeignKey(Post, null=True, blank=True, on_delete=models.CASCADE, related_name='reactions')
    comment = models.ForeignKey(Comment, null=True, blank=True, on_delete=models.CASCADE, related_name='reactions')
    actor = models.CharField(max_length=80)
    emoji = models.CharField(max_length=16)

    class Meta:
        constraints = [
            models.CheckConstraint(condition=(models.Q(post__isnull=False, comment__isnull=True) | models.Q(post__isnull=True, comment__isnull=False)), name='reaction_one_target'),
            models.CheckConstraint(condition=models.Q(emoji__in=EMOJIS), name='reaction_allowed_emoji'),
            models.UniqueConstraint(fields=['post', 'actor', 'emoji'], name='unique_post_reaction'),
            models.UniqueConstraint(fields=['comment', 'actor', 'emoji'], name='unique_comment_reaction'),
        ]
