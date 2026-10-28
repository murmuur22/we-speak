from django.contrib.auth import get_user_model
from django.test import TestCase


class AccountTests(TestCase):
    def test_registration_persists_hashed_password_and_session(self):
        response = self.client.post('/join/', {
            'username': 'Fern', 'password1': 'fern-river-clock-784!',
            'password2': 'fern-river-clock-784!',
        })
        self.assertEqual(response.status_code, 302)
        user = get_user_model().objects.get(username='fern')
        self.assertNotEqual(user.password, 'fern-river-clock-784!')
        self.assertTrue(user.check_password('fern-river-clock-784!'))
        self.assertEqual(int(self.client.session['_auth_user_id']), user.pk)

    def test_account_creates_a_persistent_discussion(self):
        user = get_user_model().objects.create_user('fern', password='fern-river-clock-784!')
        self.client.force_login(user)
        response = self.client.post('/new/', {'title': 'A small garden', 'body': 'Hello, network.'})
        self.assertEqual(response.status_code, 302)
        page = self.client.get(response.url)
        self.assertContains(page, 'A small garden')
        self.assertContains(page, 'Hello, network.')
        self.assertContains(page, 'fern')

    def test_guest_can_comment_but_not_start_discussions(self):
        from .models import Post
        user = get_user_model().objects.create_user('host')
        post = Post.objects.create(author=user, title='A shared garden', body='Hello')
        self.assertEqual(self.client.post('/guest/').status_code, 302)
        self.assertEqual(self.client.post('/new/', {'title': 'No', 'body': 'No'}).status_code, 403)
        self.assertEqual(self.client.post(f'/thread/{post.pk}/comment/', {'body': 'Guest reply'}).status_code, 302)
        self.assertContains(self.client.get(f'/thread/{post.pk}/'), 'Guest reply')

    def test_deleting_own_post_erases_content_but_keeps_other_comments(self):
        from .models import Post, Comment
        user = get_user_model().objects.create_user('host')
        other = get_user_model().objects.create_user('visitor')
        post = Post.objects.create(author=user, title='Private title', body='Private body')
        Comment.objects.create(thread=post, author=other, body='My words remain')
        self.client.force_login(user)
        self.assertEqual(self.client.post(f'/post/{post.pk}/delete/').status_code, 302)
        page = self.client.get(f'/thread/{post.pk}/')
        self.assertContains(page, '[deleted]')
        self.assertNotContains(page, 'Private title')
        self.assertNotContains(page, 'Private body')
        self.assertContains(page, 'My words remain')
        post.refresh_from_db()
        self.assertEqual(post.body, '')
        self.assertIsNone(post.author)

    def test_authors_can_edit_their_posts_and_comments_but_not_others(self):
        from .models import Post, Comment
        host = get_user_model().objects.create_user('host')
        other = get_user_model().objects.create_user('visitor')
        post = Post.objects.create(author=host, title='Before', body='Before')
        reply = Comment.objects.create(thread=post, author=other, body='Other words')
        self.client.force_login(host)
        self.assertEqual(self.client.post(f'/post/{post.pk}/edit/', {'title': 'After', 'body': 'New words'}).status_code, 302)
        self.assertEqual(self.client.post(f'/comment/{reply.pk}/edit/', {'body': 'Stolen'}).status_code, 404)
        self.assertContains(self.client.get(f'/thread/{post.pk}/'), 'edited')
        self.client.force_login(other)
        self.assertEqual(self.client.post(f'/comment/{reply.pk}/edit/', {'body': 'My new words'}).status_code, 302)
        self.assertEqual(self.client.post(f'/comment/{reply.pk}/delete/').status_code, 302)
        self.assertNotContains(self.client.get(f'/thread/{post.pk}/'), 'My new words')

    def test_returning_account_can_sign_in_and_see_its_history(self):
        from .models import Post
        user = get_user_model().objects.create_user('fern', password='fern-river-clock-784!')
        Post.objects.create(author=user, title='My discussion', body='My words')
        self.assertEqual(self.client.post('/login/', {'username': 'Fern', 'password': 'fern-river-clock-784!'}).status_code, 302)
        self.assertContains(self.client.get('/history/'), 'My discussion')

    def test_guest_identity_cannot_be_switched_through_login(self):
        get_user_model().objects.create_user('fern', password='fern-river-clock-784!')
        self.client.post('/guest/')
        self.client.post('/login/', {'username': 'fern', 'password': 'fern-river-clock-784!'})
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_guest_can_toggle_each_emoji_without_duplicate_votes(self):
        from .models import Post
        user = get_user_model().objects.create_user('host')
        post = Post.objects.create(author=user, title='Hello', body='World')
        self.client.post('/guest/')
        url = f'/post/{post.pk}/react/'
        self.assertEqual(self.client.post(url, {'emoji': '🌱'}).status_code, 302)
        self.assertContains(self.client.get(f'/thread/{post.pk}/'), '🌱 1')
        self.assertEqual(self.client.post(url, {'emoji': '🌱'}).status_code, 302)
        self.assertNotContains(self.client.get(f'/thread/{post.pk}/'), '🌱 1')
        self.assertEqual(self.client.post(url, {'emoji': '<script>'}).status_code, 400)

    def test_login_attempts_are_rate_limited(self):
        from django.test import override_settings
        with override_settings(WE_SPEAK_AUTH_LIMIT=3):
            for _ in range(3):
                self.assertEqual(self.client.post('/login/', {'username': 'nobody', 'password': 'wrong'}).status_code, 200)
            self.assertEqual(self.client.post('/login/', {'username': 'nobody', 'password': 'wrong'}).status_code, 429)

    def test_image_attachment_is_served_and_removed_with_its_post(self):
        import io
        from PIL import Image
        from django.core.files.uploadedfile import SimpleUploadedFile
        from .models import Post
        user = get_user_model().objects.create_user('host')
        post = Post.objects.create(author=user, title='An image', body='Here')
        self.client.force_login(user)
        image = io.BytesIO()
        Image.new('RGB', (2, 2), 'green').save(image, 'PNG')
        file = SimpleUploadedFile('garden.png', image.getvalue(), content_type='image/png')
        self.assertEqual(self.client.post(f'/post/{post.pk}/attach/', {'file': file}).status_code, 302)
        from .models import Attachment
        attachment = Attachment.objects.get()
        url = f'/attachment/{attachment.pk}/'
        self.assertEqual(self.client.get(url).status_code, 200)
        self.client.post(f'/post/{post.pk}/delete/')
        self.assertEqual(self.client.get(url).status_code, 404)
        self.assertFalse(Attachment.objects.exists())
