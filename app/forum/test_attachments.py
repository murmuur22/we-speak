import io
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from PIL import Image
from .models import Attachment, Post


class AttachmentControls(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user('owner')
        self.post = Post.objects.create(author=self.user, title='Pictures', body='Hello')
        self.client.force_login(self.user)
        self.url = f'/post/{self.post.pk}/attach/'

    def image(self, name='../../outside.html', suffix=b''):
        data = io.BytesIO()
        Image.new('RGB', (3, 3), 'green').save(data, 'PNG')
        return SimpleUploadedFile(name, data.getvalue() + suffix, content_type='text/html')

    def test_mislabelled_image_is_normalized_not_served_as_html(self):
        self.assertEqual(self.client.post(self.url, {'file': self.image(suffix=b'<script>bad()</script>')}).status_code, 302)
        item = Attachment.objects.get()
        self.assertNotIn(b'<script>', bytes(item.data))
        response = self.client.get(f'/attachment/{item.pk}/')
        self.assertEqual(response['Content-Type'], 'image/png')
        self.assertEqual(response['X-Content-Type-Options'], 'nosniff')
        self.assertIn('no-store', response['Cache-Control'])

    def test_html_and_svg_are_rejected_even_with_png_name(self):
        for data in (b'<html>bad</html>', b'<svg xmlns="http://www.w3.org/2000/svg"></svg>'):
            response = self.client.post(self.url, {'file': SimpleUploadedFile('image.png', data, content_type='image/png')})
            self.assertEqual(response.status_code, 400)
        self.assertFalse(Attachment.objects.exists())

    def test_upload_is_owner_only(self):
        self.client.logout()
        self.client.post('/guest/')
        self.assertEqual(self.client.post(self.url, {'file': self.image()}).status_code, 404)

    def test_three_image_limit(self):
        for _ in range(3):
            self.assertEqual(self.client.post(self.url, {'file': self.image()}).status_code, 302)
        self.assertEqual(self.client.post(self.url, {'file': self.image()}).status_code, 400)
        self.assertEqual(Attachment.objects.count(), 3)

    @override_settings(WE_SPEAK_ATTACHMENT_QUOTA=1)
    def test_storage_quota_is_enforced(self):
        self.assertEqual(self.client.post(self.url, {'file': self.image()}).status_code, 507)
        self.assertFalse(Attachment.objects.exists())

    def test_original_size_limit(self):
        file = SimpleUploadedFile('too-large.png', b'x' * (5 * 1024 * 1024 + 1))
        self.assertEqual(self.client.post(self.url, {'file': file}).status_code, 400)
        self.assertFalse(Attachment.objects.exists())

    def test_whole_request_limit(self):
        self.assertEqual(self.client.post(self.url, {'file': SimpleUploadedFile('too-large.png', b'x' * (7 * 1024 * 1024))}).status_code, 413)

    def test_repeated_file_fields_are_rejected(self):
        self.assertEqual(self.client.post(self.url, {'file': [self.image(), self.image()]}).status_code, 400)
        self.assertFalse(Attachment.objects.exists())
