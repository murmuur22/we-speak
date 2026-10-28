import io
import sqlite3
import tempfile
from pathlib import Path
from django.contrib.auth import get_user_model
from django.core.management import call_command, get_commands
from django.test import TransactionTestCase
from PIL import Image
from .models import Attachment, Post


class BackupTests(TransactionTestCase):
    def test_snapshot_includes_accounts_posts_and_image_bytes_without_overwrite(self):
        self.assertIn('backup', get_commands())
        user = get_user_model().objects.create_user('fern', password='moss-river-garden-496!')
        post = Post.objects.create(author=user, title='Restorable', body='Keep this')
        image = io.BytesIO()
        Image.new('RGB', (2, 2), 'green').save(image, 'PNG')
        data = image.getvalue()
        Attachment.objects.create(post=post, data=data, size=len(data), content_type='image/png')
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'backup.sqlite3'
            call_command('backup', str(path), stdout=io.StringIO())
            with sqlite3.connect(path) as restored:
                self.assertEqual(restored.execute('PRAGMA integrity_check').fetchone()[0], 'ok')
                self.assertEqual(restored.execute('SELECT title FROM forum_post').fetchone()[0], 'Restorable')
                self.assertEqual(bytes(restored.execute('SELECT data FROM forum_attachment').fetchone()[0]), data)
                self.assertTrue(restored.execute('SELECT password FROM auth_user').fetchone()[0].startswith('pbkdf2_'))
            from django.core.management.base import CommandError
            with self.assertRaises(CommandError):
                call_command('backup', str(path), stdout=io.StringIO())
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)
