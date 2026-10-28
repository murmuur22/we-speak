from django.test import TestCase, override_settings
from django.views.debug import SafeExceptionReporterFilter


class HardeningTests(TestCase):
    @override_settings(DEBUG=False, SECURE_SSL_REDIRECT=False)
    def test_authentication_fields_are_redacted_from_exception_reports(self):
        for path, data in [('/login/', {'username': 'nobody', 'password': 'synthetic-password'}),
                           ('/join/', {'username': '', 'password1': 'synthetic-first', 'password2': 'synthetic-second'})]:
            response = self.client.post(path, data)
            filtered = SafeExceptionReporterFilter().get_post_parameters(response.wsgi_request)
            for name in data:
                if name.startswith('password'):
                    self.assertNotEqual(filtered[name], data[name], f'{path} exposes {name}')

    def test_personalized_pages_are_not_cacheable(self):
        from django.contrib.auth import get_user_model
        for path in ('/login/', '/join/'):
            self.assertIn('no-store', self.client.get(path).get('Cache-Control', ''))
        self.client.force_login(get_user_model().objects.create_user('fern'))
        self.assertIn('no-store', self.client.get('/history/').get('Cache-Control', ''))

    def test_readiness_reports_only_database_connectivity(self):
        response = self.client.get('/healthz/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'status': 'ok'})
