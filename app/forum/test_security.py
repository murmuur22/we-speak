from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import TestCase, Client

from .models import Post, Comment, Reaction


class SecurityControls(TestCase):
    def setUp(self):
        self.owner = get_user_model().objects.create_user('owner', password='correct-horse-river-456!')
        self.other = get_user_model().objects.create_user('other')
        self.post = Post.objects.create(author=self.owner, title='Original title', body='Original body')

    def test_wrong_password_does_not_sign_in(self):
        self.client.post('/login/', {'username': 'owner', 'password': 'not-the-password'})
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_username_duplicate_ignores_case(self):
        response = self.client.post('/join/', {'username': 'OWNER', 'password1': 'cool-moss-river-890!', 'password2': 'cool-moss-river-890!'})
        self.assertContains(response, 'already taken')
        self.assertEqual(get_user_model().objects.count(), 2)

    def test_csrf_rejects_registration_without_token(self):
        client = Client(enforce_csrf_checks=True)
        self.assertEqual(client.post('/join/', {'username': 'intruder'}).status_code, 403)

    def test_guest_thread_creation_is_rejected_server_side(self):
        self.client.post('/guest/')
        self.assertEqual(self.client.post('/new/', {'title': 'Bad', 'body': 'Bad'}).status_code, 403)
        self.assertEqual(Post.objects.count(), 1)

    def test_another_account_cannot_delete_post(self):
        self.client.force_login(self.other)
        self.assertEqual(self.client.post(f'/post/{self.post.pk}/delete/').status_code, 404)
        self.post.refresh_from_db()
        self.assertFalse(self.post.deleted)

    def test_get_delete_only_shows_confirmation(self):
        self.client.force_login(self.owner)
        self.assertContains(self.client.get(f'/post/{self.post.pk}/delete/'), 'Delete permanently')
        self.post.refresh_from_db()
        self.assertFalse(self.post.deleted)

    def test_own_guest_cookie_can_edit_and_delete_its_comment(self):
        self.client.post('/guest/')
        self.client.post(f'/thread/{self.post.pk}/comment/', {'body': 'My guest words'})
        reply = Comment.objects.get()
        other_guest = Client()
        other_guest.post('/guest/')
        self.assertEqual(other_guest.post(f'/comment/{reply.pk}/edit/', {'body': 'Stolen'}).status_code, 404)
        self.assertEqual(self.client.post(f'/comment/{reply.pk}/edit/', {'body': 'New guest words'}).status_code, 302)
        self.assertEqual(self.client.post(f'/comment/{reply.pk}/delete/').status_code, 302)
        reply.refresh_from_db()
        self.assertEqual(reply.body, '')
        self.assertEqual(reply.guest_id, '')

    def test_html_is_escaped_in_thread_and_comment(self):
        self.post.body = '<script>alert(1)</script>'
        self.post.save()
        Comment.objects.create(thread=self.post, author=self.other, body='<img src=x onerror=alert(1)>')
        page = self.client.get(f'/thread/{self.post.pk}/')
        self.assertContains(page, '&lt;script&gt;')
        self.assertNotContains(page, '<script>')
        self.assertNotContains(page, '<img src=x')

    def test_comment_requires_entry_session(self):
        self.assertEqual(self.client.post(f'/thread/{self.post.pk}/comment/', {'body': 'No session'}).status_code, 403)

    def test_deleted_post_cannot_be_edited_or_reacted_to(self):
        self.client.force_login(self.owner)
        self.client.post(f'/post/{self.post.pk}/delete/')
        self.assertEqual(self.client.post(f'/post/{self.post.pk}/edit/', {'title': 'Revived', 'body': 'Revived'}).status_code, 404)
        self.assertEqual(self.client.post(f'/post/{self.post.pk}/react/', {'emoji': '🌱'}).status_code, 404)
        self.assertNotContains(self.client.get('/?q=Original'), 'Original title')

    def test_history_is_private_to_signed_in_account(self):
        self.assertEqual(self.client.get('/history/').status_code, 302)
        self.client.force_login(self.other)
        self.assertNotContains(self.client.get('/history/'), 'Original title')

    def test_logout_requires_post_and_invalidates_session(self):
        self.client.force_login(self.owner)
        self.assertEqual(self.client.get('/logout/').status_code, 405)
        self.client.post('/logout/')
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_database_enforces_reaction_uniqueness(self):
        Reaction.objects.create(post=self.post, actor='u:1', emoji='🌱')
        with self.assertRaises(IntegrityError), transaction.atomic():
            Reaction.objects.create(post=self.post, actor='u:1', emoji='🌱')

    def test_board_paginates(self):
        Post.objects.bulk_create([Post(author=self.owner, title=f'Topic {i}', body='Body') for i in range(35)])
        page = self.client.get('/')
        self.assertEqual(len(page.context['page']), 30)
        self.assertTrue(page.context['page'].has_next())

    def test_comments_keep_working_when_parent_is_deleted(self):
        self.client.force_login(self.owner)
        self.client.post(f'/post/{self.post.pk}/delete/')
        self.client.force_login(self.other)
        self.assertEqual(self.client.post(f'/thread/{self.post.pk}/comment/', {'body': 'Discussion continues'}).status_code, 302)
        self.assertContains(self.client.get(f'/thread/{self.post.pk}/'), 'Discussion continues')
