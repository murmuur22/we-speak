from django.contrib.auth import get_user_model
from django.test import TestCase
from .models import Post


class MaintenanceTests(TestCase):
    def test_operator_can_inspect_health_and_disable_identity_without_erasing_words(self):
        user = get_user_model().objects.create_user('member', password='moss-river-network-479!')
        staff = get_user_model().objects.create_user('operator', is_staff=True)
        Post.objects.create(author=user, title='Keep this conversation', body='These words stay.')
        self.assertIn(self.client.get('/maintenance/').status_code, (302, 403))
        self.client.force_login(user)
        self.assertIn(self.client.get('/maintenance/').status_code, (302, 403))
        self.assertIn(self.client.post(f'/maintenance/identity/{user.pk}/').status_code, (302, 403))
        self.client.force_login(staff)
        self.assertContains(self.client.get('/maintenance/'), 'Service health')
        self.assertEqual(self.client.post(f'/maintenance/identity/{user.pk}/', {'action': 'disable'}).status_code, 302)
        user.refresh_from_db()
        self.assertFalse(user.is_active)
        self.assertContains(self.client.get('/'), 'Keep this conversation')
        from .models import OperatorEvent
        self.assertEqual(OperatorEvent.objects.get().action, 'disable')
        self.assertEqual(self.client.post(f'/maintenance/identity/{user.pk}/', {'action': 'restore'}).status_code, 302)
        user.refresh_from_db()
        self.assertTrue(user.is_active)
        self.assertEqual(self.client.post(f'/maintenance/identity/{staff.pk}/', {'action': 'disable'}).status_code, 400)
